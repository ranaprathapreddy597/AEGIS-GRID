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


Phase 4 adds PyMongo 4.19.0 (Apache-2.0), redis-py 8.1.0 (MIT), and AJV 8.20.0
(MIT) for actual storage and generated JSON Schema/Node contract verification.
Exact package hashes are in the Python and pnpm lockfiles.

Phase 5: pypdf 6.20.1 (BSD-3-Clause), jsonschema 4.26.0 (MIT), reportlab 5.0.1
(BSD, development PDF generator), Pillow 12.3.0 (HPND, locked generator dependency).
Manual PDFs are project-authored CC0-1.0 synthetic fixtures. Evolus schema subset
is derived from the user-supplied specification; it is not a provider recording.
