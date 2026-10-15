#pragma once
#include <stdint.h>
#ifdef _WIN32
#define AEGIS_API __declspec(dllexport)
#else
#define AEGIS_API __attribute__((visibility("default")))
#endif
#ifdef __cplusplus
extern "C" {
#endif
/* Single-threaded opaque handle; strings owned by handle until next call.
   Null/-1 means failure. This API has no physical I/O or network operations. */
AEGIS_API unsigned aegis_abi_version(void);
AEGIS_API void *aegis_create(const char *scenario_json);
AEGIS_API void aegis_destroy(void *handle);
AEGIS_API int aegis_step(void *handle, double dt);
AEGIS_API int aegis_reset(void *handle);
AEGIS_API int aegis_controls(void *handle, uint64_t version,
                             const char *controls_json);
AEGIS_API int aegis_restore(void *handle, const char *snapshot);
AEGIS_API const char *aegis_json(void *handle);
AEGIS_API const char *aegis_snapshot(void *handle);
AEGIS_API const char *aegis_error(void *handle);
#ifdef __cplusplus
}
#endif
