# Phase 4 execution report — 2026-10-16, Asia/Calcutta

Status: **PASS**, completed 2026-10-16.
Baseline Phase 3: `b9985f6`. Final gate passed **155 Python / 3 CTest / 6 Chromium** checks, including snapshot
version-mismatch refusal and actual process restart. Linters, types, contract drift,
builds, two Node tests, secret scan, dependency audits, HTTP/SSE smoke and
cross-language corruption refusals passed. Browser axe reported zero violations.

## Delivered implementation

| Source | Actual behavior |
|---|---|
| `services/api/aegis_api/storage.py` | Canonical append-only Mongo events, immutable incident/snapshot views, unique-ID conflict checks, exact payload hashes, journal-acknowledged writer, bounded Redis fanout and durable receipts |
| `storage_checks.py` | Real Mongo/Redis permission, idempotency, delivery and 128-event load checks with app credentials |
| `services/edge/aegis_edge/runner.py` | Native C++ snapshot captured before emergency control; strict frame/event/snapshot version agreement |
| `services/api/aegis_api/app.py` | Independent monitoring collector, separate-token ingest, authenticated incident/read/replay/status APIs and typed errors |
| Pydantic / generated contracts | Incident/snapshot/replay/storage schemas and generated TypeScript; explicit truncated replay flag |
| Node / cross-language tool | Real HTTP telemetry validated by generated JSON Schema/AJV and semantic checks; four corrupted frames rejected |
| React / Playwright | Persistent incident list, actual replay/download, restart and snapshot fingerprint verification |
| Local infra / tools | Idempotent migrations, scoped identities, persistent Redis ACLs, preserved volumes, dependency cache layers and current gate |

Plans/actions/audit collections exist as reserved operational resources. Runtime
monitoring identities cannot insert into them. No approval-gated operational
write path or application persistence test fake is exposed.

## Commands and actual evidence

Executed using the project virtualenv on the documented Windows laptop:

```powershell
.venv/Scripts/python tools/dev.py start
.venv/Scripts/python tools/dev.py check
docker compose --env-file .env -f infra/local/compose.yaml exec -T api python -m aegis_api.storage_checks
docker compose --env-file .env -f infra/local/compose.yaml restart redis
docker compose --env-file .env -f infra/local/compose.yaml up --detach --wait --no-recreate redis
```

The complete gate output is `phase4-checks.txt`. Separate actual storage runs
are `phase4-storage-checks.json` and `phase4-redis-restart-checks.json`; these
earlier measurements precede the explicit journal-acknowledgement setting.
The final gate verifies `{"j":true,"w":1}` on the real writer and reports updated
latency in its storage-check output: median 24.112 ms, p95 93.970 ms,
0.9034 s wall time for 128 appends at concurrency eight. No administrator credential is used by
the runtime checks. Migrations alone use a disposable bootstrap container.

Six forbidden operations are checked against real services: Mongo monitoring
update/delete, reader insert, operational-plan insert, and Redis SET/XADD on an
unallowlisted key. Only labeled contract-test monitoring records are used; no
destructive Redis flush is executed. Identical append retries return the same
record; changing a payload under an existing ID conflicts. Actual stream data
and the Mongo delivery receipt are read back and compared.

The load test appends 128 labeled records with concurrency eight. It is a single
local storage measurement, not a production throughput/latency guarantee. Test
records are excluded from the ordinary incident listing and retained for 30 days.

The real Chromium restart test:

1. Reads a C++-generated incident and its before-policy native snapshot.
2. Confirms the run has anomaly/local-stop event evidence.
3. Restarts the actual API container while retaining Mongo/Redis volumes.
4. Reads the same events, snapshot hash and reproducibility fingerprint.
5. Opens the incident through React and downloads the replay JSON.

The native Python/C ABI test separately restores the snapshot into the actual
C++ model and verifies two identical 50-step traces. Evidence replay does not
mutate the live plant. The screenshot capture was also repeated after scrolling
to the top for a readable full-page capture (`phase4-replay-capture.txt`).

## Boundaries and remaining gates

All services remain local on the previously inspected Ryzen AI 7 350 / 31.29 GiB
host. Mongo/Redis have no published host ports; only the API joins storage with
scoped credentials. Bootstrap administrator passwords do not enter API, edge or
executor environments. Monitoring append auth differs from viewer/service auth.
No external provider, GitHub, enterprise mutation or deployment was used.

Mongo is authoritative, with single-document canonical events and embedded
snapshots. Cross-collection views are repairable. Redis delivery is at least once:
a crash after XADD but before receipt can duplicate an item; consumers deduplicate
by event ID. This is not an exactly-once cross-system transaction. Default storage
is a single local Mongo instance, not replicated high availability or a whole-host
power-failure certification. Hashes detect corruption, not compromised credentials.

One `local` tenant is supported under shared development tokens. Monitoring TTL
is 30 days, asynchronously enforced by Mongo; Redis stream retention is capped
at 10,000 entries. Lists return 50 incidents and replay returns at most 100 events,
with `truncated` marking larger pages. Snapshot/model revision is recorded, but
later rollout certification must additionally bind the executing native build.
Successful cloud TLS/provider calls, production identity/TLS and hosted CI remain
unverified. Remaining external gates are tracked in `../OPEN_ISSUES.md`.

Next: Phase 5 provider-schema inspection and Evolus document adapter/corpus,
with exact citations, contradiction refusal and honest live-versus-test evidence.
The supplied `api-1.json` remains unchanged and untracked for that phase; no
provided API key is printed or committed. MI300X access remains pending Phase 6.
