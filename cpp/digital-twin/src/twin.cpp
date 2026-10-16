#include "twin.hpp"
#include <algorithm>
#include <cmath>
#include <stdexcept>
namespace aegis {
namespace {
void require(bool v, const char *message) {
  if (!v)
    throw std::invalid_argument(message);
}
double number(const Json &j, double lo, double hi) {
  require(j.is_number(), "expected number");
  const double v = j.get<double>();
  require(std::isfinite(v) && v >= lo && v <= hi, "number outside bounds");
  return v;
}
std::uint64_t integer(const Json &j, std::uint64_t hi) {
  require(j.is_number_unsigned() ||
              (j.is_number_integer() && j.get<std::int64_t>() >= 0),
          "expected unsigned integer");
  const auto v = j.get<std::uint64_t>();
  require(v <= hi, "integer outside bounds");
  return v;
}
void size(const Json &j, std::size_t n) {
  require(j.size() == n, "incorrect field count");
}
double ramp(double c, double t, double rate, double dt) {
  return c + std::clamp(t - c, -rate * dt, rate * dt);
}
std::string id(unsigned i) { return "CELL-0" + std::to_string(i + 1); }
Json observation_json(const Observation &o) {
  return {{"temperatures", o.temperatures},
          {"version", o.version},
          {"time_s", o.time_s}};
}
Observation observation_from(const Json &j, std::uint64_t version,
                             double time) {
  size(j, 3);
  size(j.at("temperatures"), 6);
  Observation o;
  for (unsigned i = 0; i < 6; ++i)
    o.temperatures[i] = number(j.at("temperatures").at(i), -100, 1000);
  o.version = integer(j.at("version"), version);
  o.time_s = number(j.at("time_s"), 0, time);
  return o;
}
} // namespace
void to_json(Json &j, const Scenario &s) {
  j = {{"scenario_id", s.scenario_id}, {"seed", s.seed},
       {"fault_mask", s.fault_mask},   {"severity", s.severity},
       {"start_s", s.start_s},         {"noise_c", s.noise_c},
       {"target", s.target},           {"delay_steps", s.delay_steps},
       {"drop_every", s.drop_every}};
}
void from_json(const Json &j, Scenario &s) {
  size(j, 9);
  s.scenario_id = j.at("scenario_id").get<std::string>();
  require(s.scenario_id.size() == 12 &&
              s.scenario_id.substr(0, 9) == "scenario-" &&
              s.scenario_id.substr(9).find_first_not_of("0123456789") ==
                  std::string::npos,
          "invalid scenario id");
  s.seed = static_cast<std::uint32_t>(integer(j.at("seed"), UINT32_MAX));
  s.fault_mask = static_cast<unsigned>(integer(j.at("fault_mask"), 255));
  s.severity = number(j.at("severity"), 0, 1);
  s.start_s = number(j.at("start_s"), 0, 3600);
  s.noise_c = number(j.at("noise_c"), 0, 1);
  s.target = static_cast<unsigned>(integer(j.at("target"), 5));
  s.delay_steps = static_cast<unsigned>(integer(j.at("delay_steps"), 20));
  s.drop_every = static_cast<unsigned>(integer(j.at("drop_every"), 100));
  require(s.drop_every >= 2, "drop_every must be at least two");
}
Twin::Twin(std::uint32_t seed) : Twin(Scenario{"scenario-000", seed}) {}
Twin::Twin(const Scenario &s) : scenario_(Json(s).get<Scenario>()) {
  rng_ = static_cast<std::uint64_t>(s.seed) + 1;
  for (unsigned i = 0; i < 6; ++i) {
    cells_[i].temperature_c = 25 + random_unit();
    cells_[i].load_fraction = load_targets_[i] = 0.65 + 0.04 * i;
    valve_targets_[i] = 1;
    observed_.temperatures[i] = cells_[i].temperature_c;
  }
}
void Twin::reset() { *this = Twin(scenario_); }
double Twin::random_unit() {
  rng_ ^= rng_ << 13;
  rng_ ^= rng_ >> 7;
  rng_ ^= rng_ << 17;
  return static_cast<double>(rng_ >> 11) * 0x1.0p-53;
}
double Twin::energy() const {
  double e = coolant_capacity * coolant_;
  for (const auto &c : cells_)
    e += cell_capacity * c.temperature_c;
  return e;
}
void Twin::controls(std::uint64_t v, const Json &j) {
  require(v == version_, "stale state version");
  size(j, 3);
  size(j.at("loads"), 6);
  size(j.at("valves"), 6);
  const double pump = number(j.at("pump"), 0, 1);
  std::array<double, 6> loads{}, valves{};
  for (unsigned i = 0; i < 6; ++i) {
    loads[i] = number(j.at("loads").at(i), 0, 1);
    valves[i] = number(j.at("valves").at(i), 0, 1);
  }
  pump_target_ = pump;
  load_targets_ = loads;
  valve_targets_ = valves;
}
void Twin::substep(double dt) {
  // Synthetic coefficients and units are specified in docs/PHYSICS.md.
  // Compute all heat fluxes from the same old thermal state before updating it.
  const unsigned mask = time_ >= scenario_.start_s ? scenario_.fault_mask : 0;
  const double severity = scenario_.severity,
               efficiency = (mask & 8) ? 1 - 0.55 * severity : 1;
  const bool burst =
      (mask & 16) && std::fmod(time_ - scenario_.start_s, 60) < 30;
  const bool spike =
      (mask & 128) && std::fmod(time_ - scenario_.start_s, 30) < 10;
  pump_ = ramp(pump_, pump_target_, 0.12, dt);
  std::array<double, 6> conductance{}, requested{}, heat{}, transfer{};
  double sum = 0;
  for (unsigned i = 0; i < 6; ++i) {
    auto &c = cells_[i];
    c.load_fraction =
        ramp(c.load_fraction,
             std::min(1.0, load_targets_[i] + (burst && load_targets_[i] > 0 ? 0.25 * severity : 0)),
             0.1, dt);
    c.valve = ramp(c.valve, valve_targets_[i], 0.2, dt);
    const double block =
        (mask & 4) && i == scenario_.target ? 0.98 * severity : 0;
    conductance[i] = c.valve * (1 - block) / std::sqrt(800.0);
    sum += conductance[i];
  }
  const double target_pressure =
      180 * std::pow(pump_ * efficiency, 2) / (1 + 12 * sum * sum);
  pressure_ = ramp(pressure_, target_pressure, 20, dt);
  const double pump_power = 350 * std::pow(pump_, 3) / efficiency;
  double demand = 0;
  for (unsigned i = 0; i < 6; ++i) {
    requested[i] = (200 + 2000 * cells_[i].load_fraction) *
                   (spike ? 1 + 0.65 * severity : 1);
    demand += requested[i];
  }
  const double served = std::min(1.0, (14500 - pump_power) / demand);
  feeder_ = demand * served + pump_power;
  double coolant_heat = pump_power - 700 * (coolant_ - 22),
         external_heat = coolant_heat;
  for (unsigned i = 0; i < 6; ++i) {
    auto &c = cells_[i];
    c.flow_kg_s = conductance[i] * std::sqrt(pressure_);
    c.heat_input_w = 0.85 * requested[i] * served;
    const double capacity_flow = c.flow_kg_s * 4180,
                 ua = 120 * std::pow(c.flow_kg_s / 0.3, 0.8);
    const double h = capacity_flow > 0
                         ? capacity_flow * (-std::expm1(-ua / capacity_flow))
                         : 0;
    transfer[i] = h * (c.temperature_c - coolant_);
    const double ambient_loss = 6 * (c.temperature_c - 22);
    const double coupling =
        8 * (cells_[(i + 5) % 6].temperature_c +
             cells_[(i + 1) % 6].temperature_c - 2 * c.temperature_c);
    heat[i] = c.heat_input_w - transfer[i] - ambient_loss + coupling;
    coolant_heat += transfer[i];
    external_heat += c.heat_input_w - ambient_loss;
    production_ += dt * c.load_fraction * served / 60;
  }
  const double before = energy();
  // Internal ring and coolant exchange cancel in the total-energy balance.
  for (unsigned i = 0; i < 6; ++i)
    cells_[i].temperature_c += dt * heat[i] / cell_capacity;
  coolant_ += dt * coolant_heat / coolant_capacity;
  energy_residual_ += energy() - before - dt * external_heat;
  energy_j_ += dt * feeder_;
  time_ += dt;
}
void Twin::observe() {
  // Sensor corruption never modifies physical state. RNG advances even on drops.
  const unsigned mask = time_ >= scenario_.start_s ? scenario_.fault_mask : 0;
  Observation sample;
  sample.version = version_;
  sample.time_s = time_;
  for (unsigned i = 0; i < 6; ++i) {
    double value = cells_[i].temperature_c;
    if (i == scenario_.target) {
      if (mask & 1)
        value = std::min(value, 38.0);
      if (mask & 2) {
        if (!frozen_set_) {
          frozen_ = value;
          frozen_set_ = true;
        }
        value = frozen_;
      }
    }
    sample.temperatures[i] =
        value + scenario_.noise_c * (2 * random_unit() - 1);
  }
  history_.push_back(sample);
  if (history_.size() > 21)
    history_.pop_front();
  const auto delay = (mask & 32) ? std::min<std::size_t>(scenario_.delay_steps,
                                                         history_.size() - 1)
                                 : 0;
  observed_ = history_[history_.size() - 1 - delay];
  packet_available_ = !(mask & 64) || version_ % scenario_.drop_every != 0;
  if (!packet_available_)
    ++dropped_;
}
void Twin::step(double dt) {
  require(std::isfinite(dt) && dt > 0 && dt <= 1,
          "dt must be in (0,1] seconds");
  require(version_ < 1000000000 && time_ + dt <= 1000000,
          "simulation horizon exceeded");
  const unsigned n = static_cast<unsigned>(std::ceil(dt / 0.05));
  for (unsigned i = 0; i < n; ++i)
    substep(dt / n);
  ++version_;
  observe();
}
std::string Twin::json() const {
  Json observed = Json::array(), truth = Json::array();
  double flow = 0;
  for (unsigned i = 0; i < 6; ++i) {
    const auto &c = cells_[i];
    flow += c.flow_kg_s;
    observed.push_back({{"cell_id", id(i)},
                        {"temperature_c", observed_.temperatures[i]},
                        {"noise_bound_c", scenario_.noise_c},
                        {"flow_kg_s", c.flow_kg_s},
                        {"load_fraction", c.load_fraction},
                        {"heat_input_w", c.heat_input_w}});
    truth.push_back({{"cell_id", id(i)},
                     {"temperature_c", c.temperature_c},
                     {"flow_kg_s", c.flow_kg_s},
                     {"valve_fraction", c.valve}});
  }
  return Json({{"schema_version", "3.0.0"},
               {"model_version", "coupled-factory-v3"},
               {"scenario_id", scenario_.scenario_id},
               {"seed", scenario_.seed},
               {"state_version", version_},
               {"simulation_time_s", time_},
               {"coolant_temperature_c", coolant_},
               {"loop_pressure_kpa", pressure_},
               {"cells", observed},
               {"ground_truth",
                {{"cells", truth},
                 {"pressure_kpa", pressure_},
                 {"total_flow_kg_s", flow},
                 {"pump_fraction", pump_},
                 {"feeder_power_w", feeder_},
                 {"energy_j", energy_j_},
                 {"production_units", production_},
                 {"energy_residual_j", energy_residual_}}},
               {"measurement",
                {{"sampled_version", observed_.version},
                 {"sampled_time_s", observed_.time_s},
                 {"age_s", time_ - observed_.time_s},
                 {"packet_available", packet_available_},
                 {"dropped_packets", dropped_}}},
               {"injected_fault_mask",
                time_ >= scenario_.start_s ? scenario_.fault_mask : 0}})
      .dump();
}
std::string Twin::snapshot() const {
  Json cells = Json::array(), history = Json::array();
  for (const auto &c : cells_)
    cells.push_back({c.temperature_c, c.load_fraction, c.valve, c.flow_kg_s,
                     c.heat_input_w});
  for (const auto &o : history_)
    history.push_back(observation_json(o));
  return Json({{"format", "aegis-snapshot-v3"},
               {"scenario", scenario_},
               {"version", version_},
               {"rng", rng_},
               {"dropped", dropped_},
               {"time", time_},
               {"coolant", coolant_},
               {"pump", pump_},
               {"pump_target", pump_target_},
               {"pressure", pressure_},
               {"feeder", feeder_},
               {"energy", energy_j_},
               {"production", production_},
               {"residual", energy_residual_},
               {"frozen", frozen_},
               {"frozen_set", frozen_set_},
               {"packet_available", packet_available_},
               {"cells", cells},
               {"load_targets", load_targets_},
               {"valve_targets", valve_targets_},
               {"history", history},
               {"observed", observation_json(observed_)}})
      .dump();
}
std::string Twin::rollout(const Json &request) const {
  size(request, 3);
  const auto steps = integer(request.at("steps"), 1200);
  const auto every = integer(request.at("sample_every"), 1200);
  require(steps >= 1 && (every == 0 || (every >= 10 && steps / every <= 120)),
          "invalid rollout bound");
  Twin t = *this;
  if (!request.at("controls").is_null())
    t.controls(t.version_, request.at("controls"));
  double max_temp = 0, max_pressure = t.pressure_, max_power = t.feeder_,
         min_flow = 1, downtime = 0, wear = 0, ramp_excess = 0;
  unsigned violations = 0;
  Json samples = Json::array();
  auto sample = [&]() {
    double peak = 0;
    for (const auto &c : t.cells_)
      peak = std::max(peak, c.temperature_c);
    samples.push_back({{"elapsed_s", t.time_ - time_},
                       {"maximum_temperature_c", peak},
                       {"production_units", t.production_ - production_},
                       {"energy_kwh", (t.energy_j_ - energy_j_) / 3600000}});
  };
  // The initial state participates in all safety metrics, including a hot start.
  auto check = [&](bool flow_required) {
    max_pressure = std::max(max_pressure, t.pressure_);
    max_power = std::max(max_power, t.feeder_);
    for (const auto &c : t.cells_) {
      max_temp = std::max(max_temp, c.temperature_c);
      min_flow = std::min(min_flow, c.flow_kg_s);
      if (c.temperature_c >= 70) violations |= 1;
      if (flow_required && c.load_fraction > 0.01 && c.flow_kg_s < 0.02)
        violations |= 2;
    }
    if (t.pressure_ > 180.000001) violations |= 4;
    if (t.feeder_ > 14500.000001) violations |= 8;
  };
  check(false);
  if (every) sample();
  for (std::uint64_t k = 1; k <= steps; ++k) {
    const auto before = t.cells_;
    const double before_pump = t.pump_;
    require(t.version_ < 1000000000 && t.time_ + 1 <= 1000000,
            "simulation horizon exceeded");
    for (unsigned sub = 0; sub < 20; ++sub) {
      t.substep(0.05);
      check(t.time_ - time_ >= 10.0 - 1e-8);
    }
    ++t.version_;
    t.observe();
    // A ten-second ramp-down grace applies only to branch flow. Thermal,
    // pressure, feeder and ramp constraints apply from the initial state.
    double load_sum = 0;
    ramp_excess = std::max(ramp_excess, std::abs(t.pump_ - before_pump) - 0.12);
    wear += std::abs(t.pump_ - before_pump);
    for (unsigned i = 0; i < 6; ++i) {
      const auto &c = t.cells_[i];
      ramp_excess = std::max(ramp_excess, std::abs(c.load_fraction - before[i].load_fraction) - 0.10);
      ramp_excess = std::max(ramp_excess, std::abs(c.valve - before[i].valve) - 0.20);
      wear += std::abs(c.load_fraction - before[i].load_fraction) + std::abs(c.valve - before[i].valve);
      load_sum += c.load_fraction;
    }
    if (load_sum < 0.06) downtime += 1;
    if (every && (k % every == 0 || k == steps)) sample();
  }
  if (ramp_excess > 1e-9) violations |= 16;
  return Json({{"horizon_s", steps}, {"steps", steps},
               {"maximum_temperature_c", max_temp},
               {"maximum_pressure_kpa", max_pressure},
               {"maximum_feeder_power_w", max_power},
               {"minimum_flow_kg_s", min_flow},
               {"energy_kwh", (t.energy_j_ - energy_j_) / 3600000},
               {"production_units", t.production_ - production_},
               {"downtime_s", downtime}, {"actuator_travel", wear},
               {"maximum_ramp_excess", ramp_excess},
               {"violation_mask", violations}, {"samples", samples}}).dump();
}
void Twin::restore(const std::string &snapshot) {
  require(snapshot.size() <= 32768, "snapshot too large");
  const auto j = Json::parse(snapshot);
  size(j, 22);
  require(j.at("format") == "aegis-snapshot-v3", "unsupported snapshot");
  Twin t(j.at("scenario").get<Scenario>());
  t.version_ = integer(j.at("version"), 1000000000);
  t.rng_ = integer(j.at("rng"), UINT64_MAX);
  require(t.rng_ != 0, "invalid rng");
  t.dropped_ = integer(j.at("dropped"), t.version_);
  t.time_ = number(j.at("time"), 0, 1000000);
  t.coolant_ = number(j.at("coolant"), 0, 1000);
  t.pump_ = number(j.at("pump"), 0, 1);
  t.pump_target_ = number(j.at("pump_target"), 0, 1);
  t.pressure_ = number(j.at("pressure"), 0, 180);
  t.feeder_ = number(j.at("feeder"), 0, 14500.000001);
  t.energy_j_ = number(j.at("energy"), 0, 14500000000.0);
  t.production_ = number(j.at("production"), 0, 100001);
  t.energy_residual_ = number(j.at("residual"), -1, 1);
  t.frozen_ = number(j.at("frozen"), 0, 1000);
  t.frozen_set_ = j.at("frozen_set").get<bool>();
  t.packet_available_ = j.at("packet_available").get<bool>();
  size(j.at("cells"), 6);
  size(j.at("load_targets"), 6);
  size(j.at("valve_targets"), 6);
  for (unsigned i = 0; i < 6; ++i) {
    const auto &c = j.at("cells").at(i);
    size(c, 5);
    t.cells_[i] = {number(c.at(0), 0, 1000), number(c.at(1), 0, 1),
                   number(c.at(2), 0, 1), number(c.at(3), 0, 0.5),
                   number(c.at(4), 0, 5000)};
    t.load_targets_[i] = number(j.at("load_targets").at(i), 0, 1);
    t.valve_targets_[i] = number(j.at("valve_targets").at(i), 0, 1);
  }
  require(j.at("history").is_array() &&
              j.at("history").size() == std::min<std::uint64_t>(21, t.version_),
          "invalid history size");
  std::uint64_t previous = t.version_ - j.at("history").size();
  double previous_time = -1;
  for (const auto &item : j.at("history")) {
    const auto o = observation_from(item, t.version_, t.time_);
    require(o.version == ++previous && o.time_s > previous_time,
            "invalid history order");
    previous_time = o.time_s;
    t.history_.push_back(o);
  }
  if (t.version_ > 0)
    require(t.history_.back().time_s == t.time_, "history/state mismatch");
  t.observed_ = observation_from(j.at("observed"), t.version_, t.time_);
  if (t.version_ > 0) {
    const auto match =
        std::find_if(t.history_.begin(), t.history_.end(), [&t](const auto &o) {
          return observation_json(o) == observation_json(t.observed_);
        });
    require(match != t.history_.end(), "observed/history mismatch");
  }
  // Commit only a fully validated replacement; malformed restore is atomic.
  *this = std::move(t);
}
} // namespace aegis
