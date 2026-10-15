# Phase 1 acceptance report

Work performed 2026-10-14–2026-10-15, Asia/Calcutta. Scope is the exact supplied
Phase 1 prompt; Phase 2 has not started.

## Executable result

Six-cell C++20 thermal sample → owned Python edge process → authenticated FastAPI
SSE → React. Local Node executor denies every write. Mongo/Redis are healthy
isolated infrastructure with no application persistence claim. The supported
startup is `python tools/dev.py start` on Windows with Docker Linux containers,
or Linux with Docker/Compose. The tested workspace selected port **8180**.

## Commands and actual results

The aggregate command was `.venv/Scripts/python.exe tools/dev.py check` (portable
equivalent: `uv run --locked python tools/dev.py check`). Exact output is retained
in [phase1-checks.txt](phase1-checks.txt).

| Executed checks | Actual result |
|---|---|
| `ruff check .`; `ruff format --check .` | Pass |
| `mypy` | No issues in 9 source files |
| `tools/export_contracts.py --check`; `tools/check_ts_contracts.py` | Pydantic/OpenAPI/TypeScript contracts match |
| `pnpm lint`; `pnpm typecheck`; `pnpm build` | Pass; React production build and executor compiled |
| `pnpm test` | 2/2 Node tests pass, including authenticated mutation denial |
| Docker QA build; `ctest --test-dir /build --output-on-failure` | 3/3 checks pass; actual compiled C++ |
| `docker run --rm --network none aegis-grid-qa:phase1` | 24/24 Python tests pass, including actual C++/edge process tests |
| `tools/secret_scan.py` | No generated local tokens/private-key headers found in repository files |
| `pip_audit --skip-editable`; `pnpm audit --audit-level high` | No known vulnerabilities returned; local editable app excluded from advisory lookup |
| `tools/smoke.py` | Three increasing SSE frames, changing temperature, anonymous read denied, mutation routes absent |
| `pnpm exec playwright test` | 3/3 pass; actual value rendering/export, wrong-token denial, real edge outage/reconnection |
| Browser axe WCAG 2 A/AA and 2.1 AA scan | Zero reported violations on the live desktop view |
| Mobile viewport | 390 px layout checked for horizontal overflow and captured |
| Clean staged-source export startup | Pass: no host .env/venv/node_modules; separate Compose project with fresh volumes; six healthy containers and authenticated changing SSE |

Python tests report one Starlette TestClient/httpx deprecation warning. Node's
terminal color warning is environmental. Neither represents a failing assertion.
Hosted GitHub Actions has **not** run; the workflow executes the same local gate.

## Changed files

- Root: preserved both supplied prompts; added AGENTS.md, README, locked Python/Node
  workspaces, configuration examples, ignores and CI workflow.
- `cpp/digital-twin/`: C++20 kernel, NDJSON CLI, CMake/CTest and analytic/invariant checks.
- `packages/contracts/`: strict Pydantic/config schemas, generated JSON/OpenAPI/TS,
  shared authentication and typed error boundary.
- `services/edge/`, `services/api/`: live process ownership, validation/freshness,
  authenticated reads, SSE and bounded local rate/stream limits.
- `services/executor/`: typed Node health service and fail-closed mutation denials.
- `apps/web/`: actual live React dashboard, login, traces, log/export, stale/reconnect
  behavior and responsive accessible layout.
- `infra/local/`: digest-pinned multi-stage builds, six-service Compose and nginx.
- `tools/`, `tests/`: startup/configuration, doctor, contracts, secret baseline,
  live smoke, Python/C++ integration and browser checks.
- `docs/`: architecture, four ADRs, security baseline, evidence, issues, runbook,
  scope markers for future components and real screenshots.

## Hardware/provider evidence and limits

See [integration evidence](../INTEGRATION_EVIDENCE.md) and
[environment.json](environment.json). The laptop's CPU/RAM class is verified;
the thermal plant is synthetic. Native Windows C++ and NPU acceleration are not
verified. MI300X, ROCm/vLLM, Evolus and Pinecone are not connected. No GPU/model
measurement, enterprise mutation, physical actuation or remote GitHub write occurred.

The phase uses independent thermal cells and fixed coolant. Shared hydraulics,
faults, deterministic safety, incident persistence, graph/planner, approval and
recovery are later-phase work. Local read tokens and HTTP are not production
identity/TLS. OS transitive package pinning and full security/licensing review
remain release-hardening tasks. API polling is bounded but not a scalable fanout bus.

## Gate and next step

**Phase 1 gate: PASS.** The aggregate local automated gate and clean-source
bootstrap both passed. [clean-bootstrap.json](clean-bootstrap.json) records the
staged tree and exact bootstrap assertions. The clean copy was exported using
`git archive`, started with `python tools/dev.py start` under a separate Compose
project on port 18080, and verified with a Python standard-library HTTP/SSE client.
It reused Docker image/layer caches; no fresh-machine/cold-download timing is claimed.
Only completion documentation/evidence changed after that runtime source snapshot.
The temporary stack was removed; the main demo uses its preserved local credentials
and data. See `git log -1` for the local Phase 1 commit. There is no Git remote/push.

Initial failures repaired during development: npm release-age policy selected
older compatible package patches, TypeScript peer mismatch resolved with 5.9.3,
Make added to the CMake build image, loopback port conflict handled without stopping
an unrelated listener, and nginx gained a dedicated ingress bridge while backend
and storage isolation was retained. The final gate output contains the passing run.

The next work order is Phase 2: deterministic shared coolant/feeder physics,
seeded faults, snapshots and 100 scenario fixtures. It must be explicitly started.
