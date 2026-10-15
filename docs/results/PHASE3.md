# Phase 3 execution report — 2026-10-15, Asia/Calcutta

Status: **PASS**. Baseline Phase 2: `57010e1`.

## Implementation

- `services/edge/aegis_edge/sentinel.py`: sensor-only thermal observer, bounded
  FAISS engineering-feature memory and independent exact emergency allowlist.
- `runner.py`, `twin.py`, `app.py`: isolated CPU C ABI supervisor, native version
  recheck, actual emergency controls, authenticated status and bounded incidents.
- `cloud.py`: separate authenticated HTTPS AEGIS event client, idempotent batch
  digest, bounded outbox/history, complete typed acknowledgements and backoff.
- Native model v3: observed flow/pressure channels, snapshot revision and zero-load
  priority over injected demand bursts. A real rollout test found the missing
  priority rule; the fixed rule is covered by C++ and Python regressions.
- Pydantic/OpenAPI-generated contracts, locked FAISS/NumPy, compiler cache
  separation, CPU thread limits, explicit optional cloud egress, real React
  detector/policy/memory/cloud views and browser coverage.

`SensorFrame` excludes truth, labels and scenario identity. FAISS similarity is
based on 18 standardized engineering features; it is not a semantic text model,
diagnosis or probability. Limits are synthetic and documented in ADR 0006.

## Executed evidence

Commands: `.venv/Scripts/python tools/dev.py start`,
`.venv/Scripts/python tools/dev.py check`, and the QA container's
`python tools/profile_sentinel.py` with `--network none --memory 512m --cpus 2`.
The profile mounted only the results/tools directories. Complete gate output is
`phase3-checks.txt`; measured profile is `phase3-sentinel-profile.json`.

Final gate passed: **149 Python tests / 3 CTest checks / 5 real Chromium tests**,
including actual HTTPS loopback refusal while the live child still detects and
stops the C++ plant. Ruff, ESLint, strict Python/TypeScript typing, generated
contract/fixture drift checks, builds, secret scan, pip-audit, pnpm audit and
real authenticated HTTP/SSE smoke all passed. Browser axe reported zero violations;
desktop/mobile, observe-only overheat and actual local-stop captures were inspected.
The upstream TestClient deprecation warning remains nonblocking. No hosted CI run
is claimed.

The measured profile executed 18,000 actual supervised steps over five healthy
and ten deceptive development fixtures, 1,200 simulated seconds each. All five
healthy trials stayed unlatched; all ten deceptive trials detected and stopped
loads while the local HTTPS receiver was unreachable. In scenario-090:

| Metric | Actual value |
|---|---|
| First detection | 110 simulated seconds |
| Maximum physical temperature with safety | 41.104 °C |
| Final maximum machine load fraction | 0 |
| Cloud state / retained incident | offline / 1 |
| Largest physical temperature over ten deceptive fixtures | 41.361 °C |
| Full supervised step median / p95 | 0.475 / 0.971 ms |
| Profile wall duration | 11.490 s |
| Peak process RSS | 101.87 MiB |

Timing includes native step/serialization, sensor projection, observer/FAISS,
independent shield and control application. RSS is process-only, excluding
Docker/WSL and other services. This single CPU run is not a hard real-time claim,
held-out accuracy evaluation, or production safety certification. Phase 2's
unmitigated v2 scenario reached 80 °C near 488 simulated seconds; the current
explicit observe-only comparison independently retains the hidden-overheat case.

## Hardware/provider and security boundary

Actual Windows enumeration found an NPU Compute Accelerator Device with OK status
and an `amd-smi` command on PATH (`phase3-npu-probe.json`). No accelerated workload
or compatible runtime is verified; CPU fallback is the tested execution path.
The host remains the inspected Ryzen AI 7 350 / 31.29 GiB laptop.

The emergency policy is automatic only inside the isolated simulator, always
rechecked against native state version. It can only stop loads and maximize
cooling; it cannot restart machinery or approve a recovery proposal. Public
operational writes remain unavailable. Local observe-only mode is explicitly
labeled and cannot be selected by a public API or cloud response. Cloud delivery
does not pass commands into the supervisor. Queues are bounded and volatile;
Phase 4 adds durable storage. Overflow counts are exposed. Stale/invalid child
streams remove readiness; this does not claim physical equipment protection.

Actual connection refusal is tested. Successful cloud acknowledgements are
explicit HTTP test doubles; no remote TLS/MI300X/provider success is claimed.
Default Compose has no edge internet egress. An operator must opt in and provide
an application-owned HTTPS receiver and separate credential for live delivery.

The user supplied `api-1.json`, an Evolus Integration API OpenAPI 3.0.4 document
(v1, 179 paths, server api.evolus.ai), for Phase 5 inspection. Its SHA-256 is
`0af55c67c60d07dc35f37b70553f1a2a6b1cce76a3311d014c6be1473fadd4f8`.
The original file is not included in this phase's commit. No provider credential
was printed, committed or used by this phase. MI300X access is pending the user.

Next gate: Phase 4 event-sourced backend with least-privilege Mongo/Redis,
reliable persistence/replay across restarts, versioning, idempotency and typed
read boundaries. No Phase 4 implementation is claimed in this report.
