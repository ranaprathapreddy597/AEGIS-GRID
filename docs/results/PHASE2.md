# Phase 2 execution report — 2026-10-15, Asia/Calcutta

Status: **PASS**. Phase 1 baseline is commit `f024ab5`. The Phase 2 commit
containing this report is identifiable with `git log -1` after phase completion.
The full master prompt remains unfinished; Phases 3–12 are not implemented.

## Delivered source

| Area | Changes |
|---|---|
| `cpp/digital-twin` | Six coupled cells, finite coolant reservoir/radiator, ring heat exchange, pressure/flow/pump model, feeder budget, actuator ramps, C ABI v2, seeded faults, snapshots/reset and CLI time scaling |
| `services/edge/aegis_edge` | ctypes rollout wrapper, strict scenario loading/fingerprints, live packet-loss accounting and subprocess configuration |
| `packages/contracts` | Pydantic physics, measurement quality, scenario and offline control contracts; regenerated OpenAPI/JSON Schema/TypeScript |
| `data/scenarios` | 100 generated, preregistered fixtures across 10 injected-cause families |
| `apps/web` | Live shared-resource metrics, working observed/truth toggle, hidden temperatures/flow, dynamic observed/truth chart and scenario provenance |
| `tests`, `tools` | Physics/replay/property/ABI/transport/browser checks; deterministic fixture generator and measured CPU rollout profiler |
| `infra`, CI, docs | Pinned JSON dependency, shared-library runtime packaging, local scenario/time-scale configuration, current gate, equations, limits and runbook |

The supplied master prompt and phase guide are preserved unchanged. Phase 1
screenshots, report and check log are retained as historical evidence.

## Executed commands and evidence

The final command is `.venv/Scripts/python tools/dev.py check` on Windows,
equivalent to `uv run --locked python tools/dev.py check` after dependency setup.
Its complete actual output is `phase2-checks.txt` beside this report.
An initial PyPI vulnerability-service read timeout (15 s) is preserved in
`phase2-network-retry.txt`. Retrying with a 60 s timeout succeeded without
suppressing any vulnerability; the gate now uses that timeout.

| Check | Result |
|---|---|
| Ruff lint/format, strict mypy, generated-schema drift, 100-fixture drift | Passed |
| ESLint, TypeScript, production web/executor build | Passed |
| CMake Release / CTest | 3/3 passed, including 100 seeded property/replay trials, conservation, ramps, atomic rejection, step refinement, hidden overheat and neighbor heating |
| Actual C++ CLI / ctypes / edge / API / boundary Python tests | 129/129 passed in 8.82 seconds; one upstream TestClient deprecation warning |
| Real Chromium / axe / mobile / outage / injected overheat | 4/4 passed in 46.7 seconds; zero axe violations; desktop/mobile and hidden-overheat captures inspected |
| ASan + UBSan Debug C++ / CTest | 3/3 passed in 273.15 seconds; `phase2-sanitizers.txt`; no sanitizer finding reported |
| CPU profile, 100 scenarios × 1,200 seconds × 2 passes | All 100 complete trajectories replay identically; final measured report is `phase2-profile.json` |
| Secret scan / pip-audit / pnpm audit | Passed; no local tokens/private keys found; no known dependency vulnerabilities reported |
| Actual authenticated HTTP/SSE smoke | Passed; three increasing frames with changing temperatures, anonymous reads denied, mutation routes unavailable |

The sanitizer command used a disposable local compiler image:

```sh
cmake -S /source -B /san -DCMAKE_BUILD_TYPE=Debug \
  -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer"
cmake --build /san --parallel 2
ctest --test-dir /san --output-on-failure
```

The source was mounted read-only into `aegis-grid-build:phase2`. The sanitizer
run exercises the C++ kernel/CLI tests, not the Python FFI under ASan.

The profile command and recreation instructions are in `../DEMO_RUNBOOK.md`.
`phase2-trajectories.ndjson.gz` contains observed and truth frames every tenth
simulated second for all 100 cases; whole-trajectory hashes cover every step.
The report includes initial snapshots, effective-scenario hashes and library hash.
The measured 120,000 first-pass steps took a median 0.133 ms
and p95 0.359 ms with serialization/validation included.
Both passes plus hashing/output completed in 47.14 s;
process peak RSS was 43.38 MiB. Maximum absolute
energy-balance residual across the 100 runs was
7.44e-08 J. The sampled
trajectory archive hash matched the earlier independent execution exactly.
Timing and memory are a single local run with the scope recorded in the JSON;
no isolated-host or hard-real-time guarantee is claimed.

## Demonstrated deception

For fixture `scenario-090` (seed 42, mask 157), at approximately 488 simulated
seconds the hottest physical cell reached **80.08 °C**, while the highest observed
temperature across all six sensors was **56.66 °C**. Its target sensor is clamped
near 38 °C. This defeats the explicitly defined naive rule “alarm if any observed
temperature exceeds 80 °C.” The 80 °C value is an experimental threshold, not an
OEM operating limit. The React browser test separately runs the actual live
scenario and asserts hidden truth above 80 °C with every reading below 80 °C.

All ten combined deceptive-cascade fixtures demonstrate such a miss. There are
15/100 cases with at least one threshold miss overall: the ten combined faults
plus five blockage cases with ordinary instrument noise just below the boundary
at the first temperature crossing. Only the combined cases establish a large
hidden-temperature gap. This is a model demonstration, not detector precision,
recall, diagnosis accuracy or a held-out evaluation. Phase 3 detection and safety
control are absent.

## Hardware, security and remaining gates

Executed on the previously inspected Ryzen AI 7 350 / 31.29 GiB Windows laptop
using Docker Desktop Linux/WSL2, GCC 12.2 and Python 3.12.15. Profile command limits
the container to 2 CPUs / 512 MiB. GPU/NPU acceleration and MI300X inference were
not used or measured. Process RSS excludes Docker/WSL and the rest of the stack;
it is not a whole-host peak-memory claim.

All execution remains in isolated local simulator processes. HTTP operational
mutations are unavailable; Node still denies mutation requests. Offline C ABI
controls operate on caller-owned synthetic instances and enforce ranges, ramps
and expected versions; they are not the later independent safety/approval system.
Snapshot SHA-256 detects accidental corruption and provides no authentication.
Ground truth/fault labels are explicitly for simulator inspection and must be
excluded from future detector inputs. Local shared tokens/loopback HTTP remain
development boundaries. Physics parameters lack OEM/plant calibration; see
`../PHYSICS.md` for approximations and uncertainty limitations.

No external provider writes, deployments or credentials were added. Evolus,
Pinecone, GitHub execution and MI300X remain unavailable/unimplemented as recorded
in `../OPEN_ISSUES.md`. Hosted CI was not run. The next gate is Phase 3: edge
physics anomaly detection, local FAISS memory, deterministic safety and verified
cloud-outage survival within the host memory budget.
