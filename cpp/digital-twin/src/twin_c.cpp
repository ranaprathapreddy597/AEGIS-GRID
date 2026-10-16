#include "twin_c.h"
#include "twin.hpp"
#include <stdexcept>
namespace {
struct Handle {
  aegis::Twin twin;
  std::string buffer;
  const char *error = "";
};
std::string bounded(const char *s) {
  if (!s)
    throw std::invalid_argument("null input");
  std::size_t n = 0;
  while (n <= 32768 && s[n] != '\0')
    ++n;
  if (n > 32768)
    throw std::invalid_argument("input too large");
  return {s, n};
}
template <class F> int guard(void *p, F f) noexcept {
  if (!p)
    return -1;
  auto &h = *static_cast<Handle *>(p);
  try {
    f(h);
    h.error = "";
    return 0;
  } catch (...) {
    h.error = "Simulator operation rejected: invalid input or state";
    return -1;
  }
}
} // namespace
extern "C" {
unsigned aegis_abi_version() { return 2; }
void *aegis_create(const char *config) {
  try {
    return new Handle{
        aegis::Twin(aegis::Json::parse(bounded(config)).get<aegis::Scenario>()),
        {},
        ""};
  } catch (...) {
    return nullptr;
  }
}
void aegis_destroy(void *p) { delete static_cast<Handle *>(p); }
int aegis_step(void *p, double dt) {
  return guard(p, [dt](auto &h) { h.twin.step(dt); });
}
int aegis_reset(void *p) {
  return guard(p, [](auto &h) { h.twin.reset(); });
}
int aegis_controls(void *p, uint64_t v, const char *c) {
  return guard(p, [v, c](auto &h) {
    h.twin.controls(v, aegis::Json::parse(bounded(c)));
  });
}
int aegis_restore(void *p, const char *s) {
  return guard(p, [s](auto &h) { h.twin.restore(bounded(s)); });
}
const char *aegis_json(void *p) {
  return guard(p, [](auto &h) { h.buffer = h.twin.json(); }) == 0
             ? static_cast<Handle *>(p)->buffer.c_str()
             : nullptr;
}
const char *aegis_snapshot(void *p) {
  return guard(p, [](auto &h) { h.buffer = h.twin.snapshot(); }) == 0
             ? static_cast<Handle *>(p)->buffer.c_str()
             : nullptr;
}
const char *aegis_error(void *p) {
  return p ? static_cast<Handle *>(p)->error : "null handle";
}
const char *aegis_rollout(void *p, const char *request) {
  return guard(p, [request](auto &h) {
           h.buffer = h.twin.rollout(aegis::Json::parse(bounded(request)));
         }) == 0 ? static_cast<Handle *>(p)->buffer.c_str() : nullptr;
}
}
