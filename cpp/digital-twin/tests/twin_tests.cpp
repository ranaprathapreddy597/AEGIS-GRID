#include "twin.hpp"
#include <cmath>
#include <iostream>
#include <limits>
#include <stdexcept>

void require(bool condition, const char* message) {
  if (!condition) throw std::runtime_error(message);
}
int main() {
  try {
    aegis::Twin a(42), b(42), other(43);
    require(a.cells()[0].temperature_c != other.cells()[0].temperature_c,
            "seed must affect physical initial temperature");
    for (int i = 0; i < 100; ++i) {
      a.step(0.5); b.step(0.5);
      require(a.json() == b.json(), "same seed differs");
    }
    other.step(0.5);
    require(other.json() != a.json(), "different seed must differ");
    aegis::Twin full(42), halves(42);
    full.step(1.0); halves.step(0.5); halves.step(0.5);
    require(std::abs(full.cells()[0].temperature_c - halves.cells()[0].temperature_c) < 1e-12,
            "exact integration inconsistent");
    // Integral of heat loss over the step: h * [(Teq-Tc)*dt + (T0-Teq)*(1-exp(-k*dt))/k].
    aegis::Twin conservation(42);
    const double t0 = conservation.cells()[0].temperature_c;
    const double p = 1200.0 * conservation.cells()[0].load_fraction;
    const double eq = aegis::Twin::coolant_c + p / aegis::Twin::conductance_w_per_k;
    const double k = aegis::Twin::conductance_w_per_k / aegis::Twin::capacity_j_per_k;
    conservation.step(1.0);
    const double heat_loss = aegis::Twin::conductance_w_per_k *
      ((eq - aegis::Twin::coolant_c) + (t0-eq) * (-std::expm1(-k)) / k);
    const double stored = aegis::Twin::capacity_j_per_k *
      (conservation.cells()[0].temperature_c-t0);
    require(std::abs(stored - (p-heat_loss)) < 1e-8, "thermal energy balance");
    for (int i = 0; i < 10000; ++i) full.step(1.0);
    for (const auto& cell : full.cells()) {
      const double equilibrium = 22.0 + 1200.0 * cell.load_fraction / 80.0;
      require(std::abs(cell.temperature_c-equilibrium) < 1e-9, "equilibrium bound");
    }
    for (const double dt : {0.0, -0.1, 1.1, std::numeric_limits<double>::infinity(),
                            std::numeric_limits<double>::quiet_NaN()}) {
      const auto before = a.json();
      bool rejected = false;
      try { a.step(dt); } catch (const std::invalid_argument&) { rejected = true; }
      require(rejected && a.json() == before, "invalid dt changed state");
    }
    std::cout << "PASS deterministic trace, analytic integration, conservation, equilibrium, invalid dt\n";
  } catch (const std::exception& e) { std::cerr << e.what() << '\n'; return 1; }
}
