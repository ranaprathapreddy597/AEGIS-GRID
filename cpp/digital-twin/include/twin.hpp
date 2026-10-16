#pragma once
#include <array>
#include <cstdint>
#include <deque>
#include <nlohmann/json.hpp>
#include <string>
namespace aegis {
using Json = nlohmann::json;
struct Scenario {
  std::string scenario_id = "scenario-000";
  std::uint32_t seed = 42;
  unsigned fault_mask = 0;
  double severity = 1, start_s = 30, noise_c = 0.1;
  unsigned target = 0, delay_steps = 4, drop_every = 3;
};
void to_json(Json &, const Scenario &);
void from_json(const Json &, Scenario &);
struct Cell {
  double temperature_c = 25, load_fraction = 0.65, valve = 1;
  double flow_kg_s = 0, heat_input_w = 0;
};
struct Observation {
  std::array<double, 6> temperatures{};
  std::uint64_t version = 0;
  double time_s = 0;
};
class Twin {
public:
  explicit Twin(std::uint32_t seed = 42);
  explicit Twin(const Scenario &);
  void step(double dt);
  void reset();
  void controls(std::uint64_t expected_version, const Json &);
  std::string json() const;
  std::string snapshot() const;
  void restore(const std::string &);
  std::string rollout(const Json &request) const;
  const std::array<Cell, 6> &cells() const { return cells_; }
  std::uint64_t version() const { return version_; }
  bool packet_available() const { return packet_available_; }
  static constexpr double cell_capacity = 10000, coolant_capacity = 83600;

private:
  void substep(double dt);
  void observe();
  double random_unit();
  double energy() const;
  Scenario scenario_;
  std::uint64_t version_ = 0, rng_ = 1, dropped_ = 0;
  double time_ = 0, coolant_ = 25, pump_ = 0.85, pump_target_ = 0.85;
  double pressure_ = 0, feeder_ = 0, energy_j_ = 0, production_ = 0;
  double energy_residual_ = 0, frozen_ = 25;
  bool frozen_set_ = false, packet_available_ = true;
  std::array<Cell, 6> cells_{};
  std::array<double, 6> load_targets_{}, valve_targets_{};
  std::deque<Observation> history_;
  Observation observed_;
};
} // namespace aegis
