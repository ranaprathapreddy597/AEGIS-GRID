#include "twin.hpp"
#include <cmath>
#include <iostream>
#include <limits>
#include <stdexcept>
using aegis::Json;
using aegis::Twin;
void require(bool v, const char *m) {
  if (!v)
    throw std::runtime_error(m);
}
template <class F> void rejects(F f) {
  bool threw = false;
  try {
    f();
  } catch (const std::exception &) {
    threw = true;
  }
  require(threw, "expected rejection");
}
int main() {
  try {
    for (unsigned seed = 0; seed < 100; ++seed) {
      aegis::Scenario s;
      s.seed = seed;
      s.fault_mask = (seed * 37) % 256;
      s.start_s = 2;
      Twin a(s), b(s);
      for (int k = 0; k < 400; ++k) {
        a.step(0.5);
        b.step(0.5);
        require(a.json() == b.json(), "seed replay mismatch");
        const auto j = Json::parse(a.json());
        const auto &g = j.at("ground_truth");
        require(std::abs(g.at("energy_residual_j").get<double>()) < 1e-5,
                "energy conservation");
        require(g.at("total_flow_kg_s").get<double>() <= 3, "flow capacity");
        require(g.at("feeder_power_w").get<double>() <= 14500.000001,
                "feeder capacity");
        for (const auto &c : a.cells())
          require(c.temperature_c >= 22 && c.temperature_c < 300 &&
                      c.load_fraction <= 1 && c.valve <= 1,
                  "physical envelope");
        if (k == 100) {
          const auto snap = a.snapshot();
          b.step(1);
          b.restore(snap);
          require(a.snapshot() == b.snapshot(), "snapshot restoration");
        }
      }
      a.reset();
      b.reset();
      require(a.snapshot() == b.snapshot(), "reset mismatch");
    }
    Twin a(42);
    const auto before = a.snapshot();
    for (double dt :
         {0.0, -1.0, 1.01, std::numeric_limits<double>::quiet_NaN()})
      rejects([&] { a.step(dt); });
    require(a.snapshot() == before, "bad step mutated state");
    Json control = {{"pump", 0.0},
                    {"loads", {0, 0, 0, 0, 0, 0}},
                    {"valves", {0, 0, 0, 0, 0, 0}}};
    rejects([&] { a.controls(1, control); });
    auto bad = control;
    bad["loads"][5] = 1.1;
    rejects([&] { a.controls(0, bad); });
    require(a.snapshot() == before, "bad control mutated state");
    a.controls(0, control);
    a.step(0.5);
    const auto g = Json::parse(a.json()).at("ground_truth");
    require(std::abs(g.at("pump_fraction").get<double>() - 0.79) < 1e-12,
            "pump ramp");
    require(std::abs(a.cells()[0].valve - 0.9) < 1e-12, "valve ramp");
    require(std::abs(a.cells()[0].load_fraction - 0.6) < 1e-12, "load ramp");
    const auto stable = a.snapshot();
    auto corrupt = Json::parse(stable);
    corrupt["pressure"] = -1;
    rejects([&] { a.restore(corrupt.dump()); });
    rejects([&] { a.restore("{}"); });
    require(a.snapshot() == stable, "bad restore mutated state");
    Twin coarse(42), fine(42);
    for (int k = 0; k < 200; ++k) {
      coarse.step(0.5);
      for (int n = 0; n < 20; ++n)
        fine.step(0.025);
    }
    for (unsigned i = 0; i < 6; ++i)
      require(std::abs(coarse.cells()[i].temperature_c -
                       fine.cells()[i].temperature_c) < 0.01,
              "step refinement");
    aegis::Scenario s;
    s.fault_mask = 1 | 4 | 8 | 16 | 128;
    s.start_s = 30;
    Twin fault(s), healthy(42);
    bool deceived = false;
    for (int k = 0; k < 2400; ++k) {
      fault.step(0.5);
      healthy.step(0.5);
      const auto j = Json::parse(fault.json());
      bool observed_hot = false;
      for (const auto &c : j.at("cells"))
        observed_hot |= c.at("temperature_c").get<double>() > 80;
      if (fault.cells()[0].temperature_c > 80 && !observed_hot)
        deceived = true;
    }
    require(deceived, "fault must deceive naive 80 C monitor");
    require(fault.cells()[1].temperature_c >
                healthy.cells()[1].temperature_c + 5,
            "shared resource cascade");
    // A demand fault represents an external workload request, not an interlock bypass.
    fault.controls(fault.version(), control);
    for (int k = 0; k < 180; ++k)
      fault.step(0.5);
    for (const auto &cell : fault.cells())
      require(cell.load_fraction < 1e-12, "burst reenergized a stopped machine");
    std::cout
        << "100 seeded invariant/replay trials; conservation, ramps, atomic "
           "rejection, refinement, hidden overheat and cascade passed\n";
  } catch (const std::exception &e) {
    std::cerr << e.what() << '\n';
    return 1;
  }
}
