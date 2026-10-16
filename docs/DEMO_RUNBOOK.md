# Phase 3 edge-sentinel runbook

This is the Phase 3 edge-sentinel demonstration, **not** the final three-minute
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
behavior. The separate Phase 3 cloud-refusal test keeps the actual supervisor
running while the HTTPS receiver is unreachable.

## Health and diagnostics

`python tools/dev.py status` lists the six services. Public web liveness is
`GET /healthz`. API health internally depends on fresh authenticated edge data;
edge health depends on a live child and a recent valid frame. Node health reports
the restricted authorization-sandbox scope. Never dump `docker compose config` or full
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

## Phase 9 local Ask First proof

Open the command center at **http://localhost:PORT**, using the actual printed
port. The approval RP is localhost; 127.0.0.1 remains usable for read-only views.
Connect with the viewer token. In your own terminal run
`python tools/dev.py owner-token`, then enter that separate secret into the owner
form. Never share/capture either token. Enroll a passkey with user verification,
prepare a sandbox stop, inspect the exact diff/digest, approve that action with the
passkey, then execute. The Node verifier and native gateway recheck everything.
The receipt reports the actual atomic sandbox snapshot/database change.

This explicitly changes only `authorization-sandbox-01`, created once by admin
startup. It does not resolve the incident's contradictory bulletin or change the
running edge. There is no public reset for it. Its 256-receipt quota is deliberate;
an administrator must review further testing when exhausted. Do not delete volumes
to work around state, evidence or approval failures.

`pnpm exec playwright test tests/e2e/approval.spec.ts` uses a clearly labeled
Chromium virtual authenticator and the actual server verification, Node gateway,
Mongo CAS and C++ kernel. Its ignored `.run/webauthn-ci.json` is sensitive generated
CI test material; do not print, commit or distribute it. It is not evidence of
Windows Hello/physical-key acceptance. The exact same browser flow is available
to the user with their own real authenticator, but that hardware gate is unverified.

## Select a deterministic fault scenario

Set the following nonsecret settings in `.env` (retain all existing credentials):

```
AEGIS_SCENARIO=scenario-090
AEGIS_SEED=42
AEGIS_TIME_SCALE=20
AEGIS_SAFETY_MODE=observe_only
```

Recreate only the edge after a configuration change:

```powershell
docker compose --env-file .env -f infra/local/compose.yaml up -d --force-recreate edge
```

Toggle **Simulation ground truth**. Observe cell 01 heating while its sensor
clamps near 38 °C; dashed curves show truth, solid curves show observed readings.
The clock is simulated seconds. Fault onset is 30 simulated seconds. This is
an unmitigated synthetic scenario: there is no safety detector/recovery yet.
Return to `scenario-000`, `AEGIS_TIME_SCALE=1`, `AEGIS_SAFETY_MODE=enforce`, then recreate edge for the
normal automated browser gate. `scenario-070` demonstrates actual packet loss;
`scenario-060` demonstrates temperature measurement delay.

Offline profile (Docker Linux, no credentials or network required):

```powershell
docker build -f infra/local/python.Dockerfile --target qa -t aegis-grid-qa:phase3 .
docker run --rm --network none --memory 512m --cpus 2 --mount "type=bind,source=$((Get-Location).Path)/docs/results,target=/app/docs/results" aegis-grid-qa:phase3 python tools/profile_twin.py
```

Linux: replace the mount source with `$(pwd)/docs/results`. Profile artifacts
include initial snapshots, complete-trajectory hashes, sampled observed/truth
trajectories and measured CPU timing/RSS. They are not inference benchmarks.


## Controlled scenario and real cloud refusal

For the same scenario-090, set `AEGIS_SAFETY_MODE=enforce` and recreate edge.
The sensor-only detector latches, local load targets go to zero under native
ramp constraints, and the event outbox remains available without a cloud link.
The state remains latched; this phase has no automatic restart command.

The Phase 3 CPU profile uses `python tools/profile_sentinel.py` inside the QA
container with `--network none --memory 512m --cpus 2` and the same results mount.
It exercises an actual refused HTTPS loopback port, with no external provider.
`phase3-sentinel-profile.json` reports measured latency, RSS, detections, maximum
truth temperature and zero final load. This is development evidence, not a
held-out detection benchmark. NPU enumeration is in `phase3-npu-probe.json`;
no NPU inference is claimed.

Live cloud delivery is unconfigured by default. Only after provisioning an AEGIS
receiver with a separate token should an operator configure AEGIS_CLOUD_EVENTS_URL
and AEGIS_CLOUD_EVENTS_TOKEN and opt into `infra/local/cloud-egress.yaml`.
The route is this application's protocol, not an assumed Evolus/MI300X route.
Never put tokens in URLs, CLI arguments, screenshots or Git.


## Phase 4 persistent journal and restart replay

Startup now builds images, starts storage, applies an idempotent local migration,
and starts the app. Existing Mongo/Redis volumes are preserved. It creates
separate Mongo append/read identities, a one-stream Redis identity and a dedicated
monitoring ingest token. Keep the generated `.env` with its existing volumes.
Administrator credentials never enter API/edge/executor environments.

Run the enforced fault scenario above. After detection, the persistent journal
shows the actual incident. Choose **Replay incident**, then **Download replay**.
The artifact contains immutable event evidence and a native snapshot captured
before emergency targets were applied. Replaying evidence never mutates the live
plant. A process restart preserves the journal and replay fingerprint.

```powershell
docker compose --env-file .env -f infra/local/compose.yaml exec -T api python -m aegis_api.storage_checks
```

This explicit local verification uses application credentials, inserts clearly
labeled contract-test monitoring records, checks idempotency/conflict rejection,
verifies Redis delivery, tests six harmless scoped permission refusals and measures
128 appends at concurrency eight. Fixture records do not appear in the ordinary
incident list. They expire under the same 30-day monitoring retention policy.
No destructive Redis flush command is executed by this test.

Monitoring data uses one local tenant; this is not production tenancy. Mongo TTL
expiration is asynchronous, Redis retains at most 10,000 stream entries, and API
list/replay responses are bounded. A crash between Redis delivery and receipt can
duplicate a stream item; use event ID for deduplication. See ADR 0007 for limits.

## Phase 5 manual evidence

After connecting with the local viewer token, use **Retrieve citations** in the
Manual evidence room. It queries the real bounded FAISS corpus and displays both
conflicting revisions. **Download cited source** downloads the authenticated
original PDF. No action is executable. This is synthetic evidence, not a provider
recording or OEM authority. `python tools/probe_evolus.py` checks only documented
provider reads when a rotated key/application scope are configured in ignored .env.
Do not place credentials in documents, screenshots, terminal logs or commits.
