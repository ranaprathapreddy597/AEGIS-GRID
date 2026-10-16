# AEGIS//GRID 2.0

An industrial incident-response system, built in the twelve phases supplied in
[`AEGIS_GRID_BUILD_PHASES.md`](AEGIS_GRID_BUILD_PHASES.md).
**Current scope: Phase 10 — guarded local Mongo maintenance and reviewed repair; local gate passed.**

C++20 C ABI + independent CPU sentinel → Python edge → authenticated FastAPI SSE → React.
Six cells share a finite coolant loop, bounded pump/valves and an electrical feeder.
They are not a validated industrial plant. No physical I/O exists.
Live cloud inference and provider access remain **BLOCKED**. Numerical forensic
reasoners and C++ forecasts work locally; the offline model template abstains.
Passkey approval covers a separate stationary simulator test resource and an
atomic maintenance record in local Mongo. The reviewed repair diff is downloadable;
Evolus invocation and GitHub publication remain closed. Phases 11–12 are next.
The incident's contradictory evidence and protected external writes remain closed.

## Start locally

Prerequisites: Python 3.11–3.13, Docker Engine with Compose (or Docker Desktop
running Linux containers), a free loopback port, and internet access
for the first image build. Git is needed for development checks. On Windows,
Docker Desktop uses WSL2; no native C++ toolchain is required.

```powershell
python tools/dev.py start
```

Open the URL printed by startup (8080 preferred; falls back to 8180, 8787 or
18080 when occupied, persisted as `AEGIS_WEB_PORT` in `.env`). In your own terminal, run the following and paste
the displayed token into the local access form:

```powershell
python tools/dev.py token
```

Startup generates random local credentials in ignored `.env`, builds the C++
binary and web app, and waits for six healthy containers. Secrets never enter
the web bundle. The browser keeps its read-only token in memory until reload or
disconnect. `python tools/dev.py stop` stops the stack and preserves DB volumes.
`python tools/dev.py status` shows service health. Do not share `.env` or token output.

## Development and checks

Use Node 24, pnpm 11.25.0, Python 3.12, and uv 0.13.1. The `uv.lock` and
`pnpm-lock.yaml` files pin dependency resolution. Container images are pinned by
digest; C++ compiler/CMake/Make versions are pinned directly in the Dockerfile.

```powershell
python -m pip install uv==0.13.1
uv sync --locked
npm install --global pnpm@11.25.0
pnpm install --frozen-lockfile
pnpm exec playwright install chromium
python tools/dev.py start
uv run --locked python tools/dev.py check
```

Linux uses the same commands (`python3` where `python` is unavailable). CI also
installs Chromium system dependencies with `playwright install --with-deps chromium`.
The check command requires the local stack to be running; the C++ integration
tests run in the QA image and **fail**, rather than skip, if the real binary is absent.

Regenerate contracts after changing Pydantic models or routes:

```powershell
uv run --locked python tools/export_contracts.py
pnpm contracts
```

For host-side UI editing, `pnpm --filter @aegis/web dev` runs Vite. Its `/api`
proxy expects a native API at 127.0.0.1:8000; the default supported full-stack
workflow is Docker. See the [runbook](docs/DEMO_RUNBOOK.md) for debugging/reset.

## What is real, simulated, or unavailable

| Component | Scope |
|---|---|
| C++ thermal kernel | Real compiled C++20 code; synthetic coupled physics; 100 seeded fault fixtures; C ABI snapshots; independent local emergency policy |
| Edge, API, React | Real processes, authenticated requests, live SSE, no fixture readings |
| Node executor | Independent Ed25519/schema/scope/stop verifier; fixed private gateway, no external tool scope |
| Redis / Mongo | Append-only monitoring journal, immutable snapshots/incidents and bounded fanout; scoped credentials, operational collections closed |
| MI300X / ROCm / vLLM | No provisioned cloud endpoint; no performance claims |
| Evolus / Pinecone / GitHub | No live connector implemented or called |
| Edge sentinel / FAISS / local emergency shield | Real sensor-only CPU observer and bounded feature memory; synthetic limits, isolated simulator only |
| LangGraph | Real bounded cycles, Mongo checkpoints, observed-only inputs, C++ forecasts and durable no-action interrupt |
| Passkeys / authorization | Actual WebAuthn UV, owner session, immutable digest and durable approval; isolated test sandbox only |

See [architecture](docs/ARCHITECTURE.md), [progress](docs/PROGRESS.md),
[integration evidence](docs/INTEGRATION_EVIDENCE.md),
[open issues](docs/OPEN_ISSUES.md), and [security baseline](docs/security/THREAT_MODEL.md).

The full master prompt is not finished. Phases 10–12 and the external live gates remain.

See [physics equations and fault semantics](docs/PHYSICS.md) and the
[phase reports](docs/results/PHASE3.md). Toggle **Simulation ground truth**
to inspect hidden temperatures and flow alongside the observed sensor traces.


The default edge automatically latches a conservative local stop after a physics
residual/data-quality/thermal alarm. Its trusted policy has no cloud dependency.
The dashboard shows detector state, policy, FAISS count and cloud queue status.
`AEGIS_SAFETY_MODE=observe_only` is an explicit local comparison mode; it is shown
in telemetry and cannot be enabled by an API or model response. See the runbook
for controlled versus unmitigated demonstrations and the [design ADR](docs/ADR/0006-independent-edge-sentinel.md).


Phase 4 startup provisions scoped local Mongo/Redis identities through a disposable
migration container. API never receives the bootstrap administrator passwords.
The command center reads the persistent incident journal, replays immutable events
and downloads the captured native snapshot/evidence. Monitoring append permission
uses a separate ingest token; it cannot write operational plans/actions/audit data.
See [storage design](docs/ADR/0007-event-journal-and-scoped-storage.md).

Phase 5 adds authenticated manual evidence retrieval and original source download
to the local UI. The corpus is 999 project-authored synthetic reference pages plus
a contradictory bulletin; it is not an OEM manual. The bulletin blocks action.
The actual Evolus read adapter follows the supplied OpenAPI; live extraction and
Pinecone remain blocked. See `docs/results/PHASE5.md` and ADR 0008.

Phase 6 selects an upstream revision with native 262,144 context and adds an
authenticated serving client, labeled offline abstention, projected memory
calculator, render-tested cloud recipe and actual-result collection tools. The
local UI compares 80/192 GiB projections. No MI300X load, cloud deployment, GPU
benchmark or 200K success is claimed. See `docs/results/PHASE6.md` and
`infra/cloud/README.md` for the remaining live gates. No live GPU success is claimed.

Phase 7 provides a real cyclic LangGraph investigation with Mongo checkpoints,
sensor-only heuristic diagnosis, real C++ forecasts and a durable no-action
interrupt. The offline model backend is an abstention template, not a generative
LLM. Run the investigator from the local UI after a simulator incident. See
`docs/results/PHASE7.md`; incident execution remains closed by manual evidence.

The Phase 8 analysis endpoint runs eleven controls across 37 native uncertainty
cases, with a content-hashed artifact and actual baseline/intervention timelines.
It cannot execute a proposal. Severe uncertain blockage may require losing
production to preserve hard constraints. See docs/ADR/0011-finite-robust-recovery-search.md.

For Phase 9 open **http://localhost:PORT** (the port printed by startup), connect
with the viewer token, then use the separate owner token from your own terminal:
`python tools/dev.py owner-token`. Enroll a passkey, prepare the stationary sandbox
stop, inspect its exact diff/digest, approve with user verification and execute.
The receipt proves one atomic local Mongo/native-snapshot change. Never share
either token. Physical passkey acceptance is unverified; automated Chromium uses
a labeled virtual authenticator with real server cryptographic verification.
See ADR 0012 and the runbook for the limited scope and production gaps.
