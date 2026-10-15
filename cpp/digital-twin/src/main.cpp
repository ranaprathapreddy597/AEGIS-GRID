#include "twin.hpp"
#include <chrono>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>
#include <thread>

int main(int argc, char** argv) {
  try {
    std::uint32_t seed = 42;
    std::uint64_t steps = 0;
    double dt = 0.5;
    bool realtime = false;
    for (int i = 1; i < argc; ++i) {
      const std::string arg = argv[i];
      if (arg == "--realtime") { realtime = true; continue; }
      if (++i >= argc) throw std::invalid_argument("missing option value");
      const std::string value = argv[i];
      std::size_t used = 0;
      if (arg == "--seed" || arg == "--steps") {
        if (value.empty() || value.find_first_not_of("0123456789") != std::string::npos)
          throw std::invalid_argument("expected unsigned integer");
        const auto n = std::stoull(value, &used);
        if (used != value.size()) throw std::invalid_argument("invalid integer");
        if (arg == "--seed") {
          if (n > UINT32_MAX) throw std::invalid_argument("seed out of range");
          seed = static_cast<std::uint32_t>(n);
        } else { steps = n; }
      } else if (arg == "--dt") {
        dt = std::stod(value, &used);
        if (used != value.size()) throw std::invalid_argument("invalid dt");
      } else { throw std::invalid_argument("unknown option"); }
    }
    aegis::Twin twin(seed);
    for (std::uint64_t i = 0; steps == 0 || i < steps; ++i) {
      twin.step(dt);
      std::cout << twin.json() << std::endl;
      if (realtime) std::this_thread::sleep_for(std::chrono::duration<double>(dt));
    }
  } catch (const std::exception& error) {
    std::cerr << "twin: " << error.what() << '\n';
    return 2;
  }
}
