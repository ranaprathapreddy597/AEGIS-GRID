#include "twin.hpp"
#include <cmath>
#include <iomanip>
#include <locale>
#include <sstream>
#include <stdexcept>

namespace aegis {
Twin::Twin(std::uint32_t seed) : seed_(seed) {
  for (std::size_t i = 0; i < cells_.size(); ++i) {
    const auto offset = static_cast<double>((seed % 100U + i * 17U) % 100U) / 100.0;
    cells_[i] = {25.0 + offset, 0.50 + static_cast<double>(i) * 0.06};
  }
}
void Twin::step(double dt_s) {
  if (!std::isfinite(dt_s) || dt_s <= 0.0 || dt_s > 1.0) {
    throw std::invalid_argument("dt_s must be finite and in (0, 1]");
  }
  // Exact solution of C*dT/dt=P-h*(T-Tc) over a constant-load interval.
  // Synthetic independent cells; shared coolant and fault dynamics arrive in Phase 2.
  for (auto& cell : cells_) {
    const double power_w = 1200.0 * cell.load_fraction;
    const double equilibrium_c = coolant_c + power_w / conductance_w_per_k;
    cell.temperature_c = equilibrium_c + (cell.temperature_c - equilibrium_c)
      * std::exp(-conductance_w_per_k * dt_s / capacity_j_per_k);
  }
  time_s_ += dt_s;
  ++version_;
}
std::string Twin::json() const {
  std::ostringstream out;
  out.imbue(std::locale::classic());
  out << std::setprecision(12) << "{\"schema_version\":\"1.0.0\","
      << "\"model_version\":\"thermal-bootstrap-v1\",\"seed\":" << seed_
      << ",\"state_version\":" << version_ << ",\"simulation_time_s\":" << time_s_
      << ",\"coolant_temperature_c\":" << coolant_c << ",\"cells\":[";
  for (std::size_t i = 0; i < cells_.size(); ++i) {
    if (i != 0) out << ',';
    out << "{\"cell_id\":\"CELL-0" << i + 1 << "\",\"temperature_c\":"
        << cells_[i].temperature_c << ",\"load_fraction\":" << cells_[i].load_fraction
        << ",\"heat_input_w\":" << 1200.0 * cells_[i].load_fraction << '}';
  }
  return out.str() + "]}";
}
}
