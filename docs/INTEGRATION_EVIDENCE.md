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
