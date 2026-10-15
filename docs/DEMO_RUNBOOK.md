# Phase 2 golden-path runbook

This is the Phase 2 telemetry demonstration, **not** the final three-minute
incident/recovery demo. All values come from the local synthetic C++ model.

1. Start Docker Desktop with Linux containers, or a Linux Docker Engine/Compose.
2. From the repository run `python tools/dev.py start`.
3. Open the URL printed by startup and enter the viewer token shown by
   `python tools/dev.py token` in your own terminal. Do not share/capture the token.
4. Observe increasing frame/time values, six temperatures, and traces. Verify the
   local simulation and unavailable-integration labels.
5. Open Signal log, then export a frame. Inspect its run ID, seed, source, model
   revision and simulator binary SHA-256. These are actual runtime fields.
6. Disconnect; the browser clears its token and readings.

## Reset and outages

Reset uses an explicit local operator CLI, not an unapproved API write:

```powershell
docker compose --env-file .env -f infra/local/compose.yaml restart edge
```

The seed stays fixed, the simulation restarts at version 1, and a new run UUID
causes React to clear the previous graph. This is normally a few seconds; actual
timing must be measured, not promised. Change `AEGIS_SEED` in `.env` and recreate
the edge service to select another initial state.

To demonstrate a lost edge link, stop `edge` through Compose. The view becomes
stale/degraded and keeps clearly labeled last-received readings. Start `edge`
again; the fetch/SSE consumer resumes with the new run. This proves transport
behavior only; the independent safety controller is Phase 3.

## Health and diagnostics

`python tools/dev.py status` lists the six services. Public web liveness is
`GET /healthz`. API health internally depends on fresh authenticated edge data;
edge health depends on a live child and a recent valid frame. Node health explicitly
reports that mutations are disabled. Never dump `docker compose config` or full
container inspection into chat because resolved configuration contains secrets.

Safe diagnostics:

```powershell
docker compose --env-file .env -f infra/local/compose.yaml logs --tail 40 edge api web executor
uv run --locked python tools/smoke.py
```

No credentials are required from AMD/Evolus/GitHub. Startup selects a free default
loopback port on first use and persists it as `AEGIS_WEB_PORT` in `.env`. If that
port later becomes occupied, choose another port in `.env`; smoke/browser tests
read the same setting. Do not stop unrelated listeners to make room.
Do not remove database volumes to repair an application build. Keep `.env` with
existing volumes; changing database passwords without a migration can invalidate
health checks. `python tools/dev.py stop` preserves volumes.

## Test / acceptance

Follow README development setup, then `uv run --locked python tools/dev.py check`.
Tests include real C++ subprocess execution and browser reads from the running
Docker stack. The API outage/malformed-data unit tests use explicitly named local
test doubles. No mocked hardware/passkey/provider success is reported.

## Select a deterministic fault scenario

Set the following nonsecret settings in `.env` (retain all existing credentials):

```
AEGIS_SCENARIO=scenario-090
AEGIS_SEED=42
AEGIS_TIME_SCALE=20
```

Recreate only the edge after a configuration change:

```powershell
docker compose --env-file .env -f infra/local/compose.yaml up -d --force-recreate edge
```

Toggle **Simulation ground truth**. Observe cell 01 heating while its sensor
clamps near 38 °C; dashed curves show truth, solid curves show observed readings.
The clock is simulated seconds. Fault onset is 30 simulated seconds. This is
an unmitigated synthetic scenario: there is no safety detector/recovery yet.
Return to `scenario-000` and `AEGIS_TIME_SCALE=1`, then recreate edge for the
normal automated browser gate. `scenario-070` demonstrates actual packet loss;
`scenario-060` demonstrates temperature measurement delay.

Offline profile (Docker Linux, no credentials or network required):

```powershell
docker build -f infra/local/python.Dockerfile --target qa -t aegis-grid-qa:phase2 .
docker run --rm --network none --memory 512m --cpus 2 --mount "type=bind,source=$((Get-Location).Path)/docs/results,target=/app/docs/results" aegis-grid-qa:phase2 python tools/profile_twin.py
```

Linux: replace the mount source with `$(pwd)/docs/results`. Profile artifacts
include initial snapshots, complete-trajectory hashes, sampled observed/truth
trajectories and measured CPU timing/RSS. They are not inference benchmarks.
