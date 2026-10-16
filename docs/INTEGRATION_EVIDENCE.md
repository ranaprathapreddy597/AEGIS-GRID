# Capability evidence — 2026-10-14, Asia/Calcutta

## Verified host discovery

PowerShell CIM and executable probes observed:

| Item | Actual observation |
|---|---|
| Computer | LENOVO model 83HY |
| CPU | AMD Ryzen AI 7 350 w/ Radeon 860M; 16 logical processors |
| OS | Windows 11 Home Single Language, 64-bit, 10.0.26300 |
| Visible RAM | 31.29 GiB (consistent with requested 32 GB class) |
| Video controller | AMD Radeon 860M; driver 32.0.31041.1004 |
| GPU memory probe | WMI AdapterRAM reported 536870912; not a reliable unified-memory/usable-VRAM measurement |
| Python host | 3.12.7 |
| Node / npm | v24.19.0 / 11.17.0 |
| pnpm / installed local uv | 11.25.0 / 0.13.1 |
| Git | 2.55.0.windows.3; repository initialized locally |
| Docker | 29.8.1, Linux engine; Compose v5.5.1 |
| WSL | Version 2; only docker-desktop distro listed |
| Native C++ | CMake, CTest, ninja, clang++, g++, cl not on PATH; no VS compiler installation found by the performed probes |

Docker was initially stopped; `docker desktop start --detach` started it, and
`docker info` confirmed Linux server version 29.8.1. No OS/driver/compiler install
or WSL distro change was made. `.venv` is project-local.

## External capability boundaries

Presence-only checks found the following variables unset: EVOLUS_API_KEY,
EVOLUS_BASE_URL, EVOLUS_MCP_URL, PINECONE_API_KEY, GITHUB_TOKEN, GH_TOKEN,
MI300X_HOST, INFERENCE_BASE_URL, INFERENCE_API_KEY, MONGODB_URI, REDIS_URL.
This says nothing about credentials held elsewhere; no credential files/accounts
were searched. Secret values were not printed.

| Capability | Classification | Evidence |
|---|---|---|
| CPU execution | Verified local | Runtime builds/tests recorded in phase report |
| Industrial plant | Locally simulated | C++ synthetic thermal kernel; no physical connector |
| NPU | Unverified | No compatible workload, driver/API or model probe performed |
| MI300X / ROCm / vLLM | Blocked | No provisioned instance; no device/benchmark logs |
| Evolus | Blocked | No verified provider SDK/tool schema supplied; no adapter claims |
| Pinecone / external GitHub | Not integrated | No external request or mutation performed |
| Mongo / Redis | Verified local infrastructure only | Authenticated Compose health checks passed; application persistence not implemented |

AMD's advertised MI300X memory is **192 GB HBM3**, a vendor specification, not a
measurement on this machine ([official data sheet](https://www.amd.com/content/dam/amd/en/documents/instinct-tech-docs/data-sheets/amd-instinct-mi300x-data-sheet.pdf)).
No model has been selected and no 200K-context performance claim exists.

## Implementation references inspected

- [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Pydantic strict mode](https://github.com/pydantic/pydantic/blob/main/docs/concepts/strict_mode.md)
- [uv locking/sync](https://docs.astral.sh/uv/concepts/projects/sync/)
- [OpenAPI TypeScript CLI](https://openapi-ts.dev/cli)
- [Docker Compose health ordering](https://docs.docker.com/compose/how-tos/startup-order/)
- [CMake testing](https://cmake.org/cmake/help/latest/guide/tutorial/Testing%20and%20CTest.html)
- [Vite requirements](https://vite.dev/guide/)

Package versions were inspected from PyPI/npm registry metadata. React 19.3.0 and
Playwright 1.64.0 were selected to satisfy the repository's 24-hour release-age
guard. TypeScript 5.9.3 satisfies the OpenAPI generator's peer requirement; 7.x
was rejected after a real compatibility failure. No failing version is retained.

## Runtime evidence

The complete Phase 1 check command passed on 2026-10-14; completion documentation
continues on 2026-10-15. See `results/phase1-checks.txt` for executed output.
All six containers were healthy on the inspected laptop. Port 8080 was occupied;
startup saved the available loopback port 8180 without terminating that listener.
Docker 29 required a web-only ingress bridge for host publication; backend/storage
networks remain internal.

Actual container versions: Python 3.12.15, Node v24.21.0, GCC 12.2.0
(`12.2.0-14+deb12u1`), CMake 3.25.1, Redis 8.10.2, MongoDB 8.3.13.
These differ from host Python/Node as expected for pinned image digests.

A single `docker stats --no-stream` snapshot observed approximately 340.7 MiB
across the six application containers (web 2.793, API 44.47, edge 42.66, executor
19.89, Redis 4.605, Mongo 226.3 MiB). This excludes Docker/WSL overhead and builds,
and is not a peak-memory, load, inference, or latency benchmark.

`results/phase1-dashboard.png` and `results/phase1-mobile.png` were captured by
Playwright from actual streamed C++ values, not generated mockups. The browser
suite also stopped/restarted the actual edge container and verified stale status
followed by resumed live readings. No physical-safety result is implied.

On 2026-10-15, the clean-source export bootstrapped a separate six-service stack
with fresh credentials and volumes, without a host virtualenv/node_modules. A
standard-library HTTP client verified its UI, unauthenticated denial, and three
changing SSE frames. See `results/clean-bootstrap.json`. Docker caches were reused.

## Phase 2 execution — 2026-10-15

The same laptop executed the coupled C++ factory, Python ctypes offline rollouts
and the live edge/API/React path. The kernel now includes finite shared coolant,
pressure/flow, ring heat exchange, electrical feeder and actuator ramps. It is
still synthetic, without plant calibration or physical I/O. Equations, units,
approximations and fault/uncertainty semantics are recorded in `PHYSICS.md`.

The 100 registered fixtures were each stepped for 1,200 simulated seconds and
replayed from reset. All 100 complete observed/ground-truth trajectory hashes
matched. The sampled trajectory archive also matched across two executions.
`results/phase2-profile.json` contains initial state, scenario/library hashes,
per-case maxima and measured timing/memory. The final CPU profile used a Docker
container limited to 2 CPUs / 512 MiB: median step 0.133 ms, p95 0.359 ms, peak
process RSS 43.38 MiB, 47.14 s for the full two-pass profile and artifact work.
This excludes Docker/WSL and other services, and includes serialization and
Pydantic validation in each measured first-pass step. No GPU/NPU was used.

For scenario-090, actual model truth first crossed the experimental 80 °C
threshold at about 488 simulated seconds while all temperature observations were
at most 56.66 °C. The live browser test independently exercises this fault through
the actual process and SSE path. These are synthetic threshold-deception tests;
an anomaly detector, independent safety shield and recovery system are Phase 3+.

Release CTest, 129 Python tests and browser/axe checks cover actual binaries and
transport; see `results/PHASE2.md` and `results/phase2-checks.txt` for final gate
results. A separate ASan/UBSan Debug build passed all three CTest checks in
273.15 s with no reported finding (`results/phase2-sanitizers.txt`). Ground truth
and injected labels are exposed only for local simulator inspection and must be
excluded from later detector evidence. C ABI controls are local offline simulator
operations; no HTTP operational mutation endpoint was added.

Evolus, MI300X, Pinecone and external GitHub integration status is unchanged.
No provider credential or external write was used, and hosted CI remains unrun.


## Phase 3 execution — 2026-10-15

Actual C++/ctypes supervisor, sensor-only observer, bounded FAISS and independent
local shield pass the full gate (149 Python / 3 CTest / 5 Chromium checks).
`results/PHASE3.md` records source, commands, actual outputs and limitations.
The network-none CPU profile exercised a real refused HTTPS loopback receiver:
all ten deceptive development fixtures stopped, five healthy cases stayed
unlatched, and scenario-090 detection occurred at 110 simulated seconds with
maximum truth 41.104 °C. Measured p95 whole supervised step 0.971 ms and peak
process RSS 101.87 MiB on the documented laptop, with a 512 MiB / 2 CPU container.
NPU enumeration found an OK device and amd-smi is on PATH, but no accelerated
workload is verified. CPU fallback is the functional measured backend.
Successful remote cloud TLS and MI300X remain unverified. Reconnect ack tests
use explicit local HTTP doubles; unreachability uses actual connection refusal.
Queues are bounded and volatile; durable persistence is Phase 4. The user supplied
an Evolus OpenAPI file for Phase 5; no provider call or credential use occurred.

## Phase 4 execution — 2026-10-16

Actual local Mongo and Redis now store monitoring events with separate scoped
identities. The full gate passed 155 Python / 3 CTest / 6 Chromium checks, both
dependency audits, secret scan and live cross-language/HTTP checks. Six actual
forbidden Mongo/Redis operations were refused. Mongo writer acknowledgement is
verified as journaled w=1. The 128-event concurrency-eight check measured median
24.112 ms and p95 93.970 ms, 0.9034 s wall. This is one local sample, not an SLA.
A Chromium test restarted the actual API and verified unchanged native incident
snapshot, events and replay digest. Separate Redis restart verified persistent
ACL authentication and subsequent delivery. See results/PHASE4.md and raw logs.
No external provider call, hardware inference or operational enterprise write
was performed. Raw Evolus specification was supplied; application scope and live
extraction verification remain pending. MI300X provisioning will follow later.

## Phase 5 local execution — 2026-10-16

Supplied Evolus OpenAPI was inspected and a read-only adapter implemented against
actual routes, headers and schemas. Contract doubles are explicitly labeled; no
live provider success is claimed. User supplied application scope; rotated key is
not configured at the recorded probe. MI300X remains unprovisioned.
The local corpus has 999 synthetic reference sheets plus one contradictory
bulletin. Pinned pypdf, exact source/page hashes, typed evidence and bounded FAISS
are exercised by actual tests. Full gate passed 179 Python / 3 CTest / 7 Chromium
checks, audits, contract drift, live storage and HTTP/SSE. Actual network-none CPU
retrieval profile: 96.70 MiB peak RSS, 0.536 ms p95, 20/24 exact-term top-1 relevant
queries. Misses are recorded. These are development lexical tests, not semantic
OEM validation. Contradiction refusal checks the complete corpus. See PHASE5.md.

## Phase 6 source/registry discovery — 2026-10-16

Actual upstream metadata/config and a real Docker registry inspection verified
Qwen3-Coder-30B-A3B-Instruct revision b2cff646eb4bb1d68355c01b18ae02e7cf42d120
and the pinned ROCm 7.0/vLLM 0.11.2 image digest. These are source/registry checks,
not GPU observations. Model metadata reports 30,532,122,624 BF16 parameters;
config reports 48 layers, four KV heads, head dimension 128 and native 262,144
context. No model weights or GPU image were downloaded to the laptop.
Projected BF16 weights 56.8705 GiB + 24 GiB KV per full-context sequence; the
two-sequence case totals 132.8705 GiB with explicit assumed reserves. No real
OOM, throughput, engine prefill/decode, peak HBM or 200K success is claimed.
The user will provide MI300X access later. Probe/benchmark outputs are blocked
and contain no fabricated measurement rows. See results/PHASE6.md and ADR 0009.

Phase 6 final local gate passed 203 Python / 3 CTest / 8 Chromium checks plus
all existing audits/contracts, actual local storage and HTTP/SSE checks. The first
QA-image missing-file failure was repaired and preserved in raw evidence. Manifest
rendering proves configuration only; device/runtime execution remains blocked.

## Phase 7 local execution — 2026-10-16

Pinned LangGraph executes real cyclic numerical reasoning, C++ counterfactuals,
Mongo checkpoints and durable interrupt. The observed-input boundary includes
only actual delivered sensor windows, never undelivered snapshot history.
208 Python / 3 CTest / 9 Chromium / 2 Node tests passed, including real API
restart/read/idempotent retry and three actual Mongo denials for graph credentials.
Offline inference is an abstention template, not an actual generative LLM. No
model tokens/cost or GPU metrics are invented. MI300X/Evolus/Pinecone live gates
remain BLOCKED; user explicitly authorized continued local Phases 8–12.

## Phase 8 CPU evidence — 2026-10-16

Actual native private-copy minimax runs eleven controls across 37 seeded full-state
priors; 409 rollouts including paired timelines, 4,908,000 physics substeps.
A network-none 2-CPU/512-MiB container measured 1.4994 s and 86.05 MiB process RSS
for one development incident. Baseline peak 92.8155 versus checked stop 41.1321
Celsius, at the explicit cost of 591 s downtime and nearly all production. These
are synthetic model outcomes, not real economics or GPU/plant measurements.
212 Python / 3 CTest / 10 browser / 2 Node tests and actual restart replay pass.
MI300X, Evolus and Pinecone live acceptance remain BLOCKED. Phase 9 is next.

## Phase 9 actual local authorization — 2026-10-16

244 Python / 3 CTest / 15 Node / 11 Chromium checks passed. Maintained WebAuthn
verification checks real ES256 browser assertions; fixed Ed25519 capabilities pass
an independent Node verifier and the private native gateway. The actual Mongo
sandbox CAS atomically changes version/snapshot/nonce/hash-chained receipt. The
browser proves durable approval across API restart, tamper/replay/stale refusal
and one-effect retry. Fourteen additional actual role escalations were denied.
This uses a labeled Chromium virtual authenticator, not a physical security key or
hardware attestation. The initial transport failures and final passing full output
are preserved; no timeout/security rule was relaxed. MI300X/Evolus/Pinecone live
gates remain BLOCKED. No incident, external enterprise or physical I/O was enabled.

## Phase 10 actual local enterprise sandbox — 2026-10-16

248 Python / 3 CTest / 16 Node / 13 Chromium checks passed. Both real ES256
virtual-authenticator flows (native stop and local Mongo maintenance + stop)
survive browser/API restart and reject replay/tamper/stale state. V2 receipts
bind the maintenance record; actual V1 records remain verifiable. The original
reload bug and independently applied repair have actual before/after browser
proof. No hosted CI/PR or Evolus invocation is claimed. Presence-only probe
confirms required external credentials/endpoints absent; live gates BLOCKED.
Public GitHub version metadata was read to verify header compatibility only.
See PHASE10.md, ADR 0013 and the raw full gate.

## Phase 11 actual CPU/UI — 2026-10-16

10,000 real CPU C++ futures / 120 million substeps: 40.1391 s, 89.09 MiB
process RSS, bounded network-none 2-CPU/512-MiB container. All 5,000 paired rows
are fingerprinted; a stored prior re-executes exactly. Private analysis replay
detects scenario-090 seed42 at 109 s (dt .5), 87.20 versus 40.95 C peak over
600 s. This is synthetic CPU analysis, not cloud inference or operational control.
252 Python / 3 CTest / 16 Node / 14 browser checks pass, including real selected
analysis LangGraph and tournament. Live external gates remain BLOCKED.

## Phase 12 final actual local evidence — 2026-10-16

Main and separately installed clean-source gates each passed 268 Python / 3 CTest
/ 16 Node / 14 browser tests and all existing audit/contract/transport/storage
checks. Actual fresh-source export tree 64d4da5ded1a00b056e137af853e95e908a3e0b7
started a unique project with new credentials/volumes; its 180.0156-second demo
produced real LangGraph/rollout/manual/WebAuthn/Node/Mongo evidence. Video,
analysis export and receipt proof retained. A later separate source venv and
node_modules install passed the complete gate against that isolated database.
Only completion docs/evidence and its validation helper changed after the export;
runtime source/contracts match. Main stack and all volumes were preserved.

The original 100-case benchmark is not hidden: Sentinel 46/90 fault detections,
31/90 numerical diagnoses and five late thermal trips. A 65 C operating guard
with unchanged 70 C hard limit fixes all five native regressions; the separate
post-fix 100-case run has zero thermal violations and diagnosis 34/90. These are
post-evaluation synthetic regressions, not held-out industrial results. Learned
CPU baseline 62/90; all misses/intervals and model parameters are published.

Actual package inventory/Node lock matching and pip/pnpm/secret scans do not imply
OS CVE scanning, signed provenance or independent assessment. No GPU/NPU/provider
performance or external mutation is invented. MI300X/Evolus/Pinecone/GitHub live
gates and production security/physical-key acceptance remain BLOCKED/unverified.
No release tag. See PHASE12.md, FINAL_AUDIT.md and RELEASE_CHECKLIST.md.

## Pinecone provisioned index: live metadata verified

User supplied the index host; it is saved only in ignored local .env. An actual
authenticated GET /indexes/aegis-grid-memory with API version 2025-10 returned
HTTP 200: Ready, dense, 256 dimensions, cosine, host matching supplied endpoint.
Only metadata was read; credentials were not printed or committed. No external
write, document upload or retrieval comparison was performed. Full Pinecone live
indexing/retrieval acceptance remains BLOCKED, separately from verified metadata.
See results/pinecone-live-metadata.json. Earlier absence records are historical.

## AMD Token Factory — catalog verified, opinion acceptance partial

Authenticated catalog and tiny identity calls succeeded for the three requested
models. Only two of six structured-opinion cases validated; validation failures,
a timeout and shared quota refusal are retained. Standalone bounded routing and
probes are implemented; hosted LangGraph reasoning is not enabled. Full hosted
acceptance and MI300X hardware acceptance remain BLOCKED. See
results/AMD_TOKEN_FACTORY.md for scope, actual evidence and local checks.
