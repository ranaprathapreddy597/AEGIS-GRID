#pragma once
#include <array>
#include <cstdint>
#include <string>

namespace aegis {
struct Cell {
  double temperature_c;
  double load_fraction;
};
class Twin {
 public:
  explicit Twin(std::uint32_t seed);
  void step(double dt_s);
  [[nodiscard]] std::string json() const;
  [[nodiscard]] const std::array<Cell, 6>& cells() const { return cells_; }
  [[nodiscard]] std::uint64_t version() const { return version_; }
  static constexpr double coolant_c = 22.0;
  static constexpr double capacity_j_per_k = 8000.0;
  static constexpr double conductance_w_per_k = 80.0;
 private:
  std::uint32_t seed_;
  std::uint64_t version_ = 0;
  double time_s_ = 0.0;
  std::array<Cell, 6> cells_{};
};
}
