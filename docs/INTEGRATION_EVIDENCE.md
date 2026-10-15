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
