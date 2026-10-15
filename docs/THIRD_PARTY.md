# Third-party dependencies and assets

No downloaded fonts, photographs, generated images, paid assets or copied UI
templates are used. The interface uses system fonts, CSS and SVG primitives.
Screenshots are captures of the running application.

Application source has no license assigned yet; the repository owner must choose
one before public redistribution. Do not infer relicensing of the supplied prompts.

Dependency versions and integrity hashes are recorded in uv.lock/pnpm-lock.yaml.
Redis/Mongo container images are official vendor distributions; their licenses and
redistribution/hosting requirements must be reviewed before a public release.
Local use here does not claim a production licensing review. GNU runtime linking
uses its upstream runtime exception; OS packages retain their own licenses.

Dependency vulnerability scans are a point-in-time check, separate from license
compliance. Full SBOM/license automation is part of release hardening.

The C++ build uses Debian `nlohmann-json3-dev=3.11.2-2` (upstream
nlohmann/json 3.11.2, MIT), included as header-only serialization code.
[Upstream license](https://github.com/nlohmann/json/blob/v3.11.2/LICENSE.MIT)
and Debian copyright notices remain applicable.


Phase 3 adds faiss-cpu 1.15.1 (FAISS, MIT) and NumPy 2.4.6 (BSD-3-Clause,
with bundled-library notices). Exact wheel hashes are in uv.lock. The runtime
installs pinned Debian libgomp1 for CPU OpenMP; no GPU/NPU SDK is used.
