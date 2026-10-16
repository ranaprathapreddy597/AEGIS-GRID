# ADR 0007: Canonical append-only monitoring journal and at-least-once fanout

Phase 4, 2026-10-15. MongoDB stores immutable canonical monitoring events. Each
record includes tenant, event/run/state IDs, schema revision, exact canonical
payload JSON and SHA-256, ingest time and server-selected expiry. The embedded
detection snapshot makes the canonical event a single atomic document. Incident
and snapshot collections are recoverable immutable views; unique indexes make
duplicate projection insertion harmless. An ID with a changed payload conflicts.
Native snapshots are captured in the supervisor before local emergency targets
are applied; the API never automatically restores or executes them.

Redis Streams provide bounded fanout, not the durable source of truth. After
Mongo append, publishing records a separate Mongo receipt. A crash between XADD
and the receipt can duplicate a delivery; consumers must deduplicate by event ID.
Unpublished events are discovered by a fixed lookup against receipts after a
restart. Projection repair precedes publishing. Redis failure retains the Mongo
record. This does not claim cross-system exactly-once transactions.

All monitoring records expire after 30 days through server TTL indexes; Redis
retains at most 10,000 stream entries with an exact MAXLEN. TTL removal is
asynchronous. Payloads contain synthetic plant state and evidence, not tokens,
provider documents, free-form prompts or credentials. API lists are bounded to
50 incidents and replay to 100 events. Only the `local` tenant is supported;
shared local tokens are not production multi-tenant identity. A replay fingerprint
covers canonical event hashes and remains stable across process restarts.

Migration creates events, incidents, snapshots, fanout_receipts, plans, actions,
audit and migration collections, validators and indexes. A disposable bootstrap
container alone receives local admin credentials. API has separate Mongo writer
(find/insert monitoring collections only), Mongo reader (find only) and Redis
ingestor (one stream; PING/XADD/XRANGE/XREAD/XLEN). Runtime identities cannot
update/delete documents, administer servers or insert plans/actions/audit records.
Redis ACLs are saved in its local persistent volume and survive Redis restart.
Existing volumes are preserved. Re-running startup reapplies the migration and
scoped credentials without dropping collections.

The authenticated AEGIS receiver accepts only typed append-only EdgeBatch events,
under an independent ingest token and canonical batch digest. It does not accept
commands, operational documents or arbitrary database filters. Read/replay uses
the separate viewer boundary. Local golden-path collection polls the trusted
edge event history independently of browser reads and remote cloud availability.
No successful fake in-memory persistence is provided when storage is unavailable.

Local Mongo/Redis traffic stays on the isolated Docker storage network; local
HTTP/shared tokens are development boundaries. High availability, encrypted
remote storage and production tenant policies are not claimed. Hashes detect
corruption, not a stolen credential capable of recomputing them. Monitoring
append permission is distinct from Phase 9 approval-gated operational writes.
The API process has both scoped monitoring clients but no admin/operational
credential. Explicit contract-test records carry `storage_contract_fixture`
origin and are excluded from the ordinary incident listing.

Primary references inspected: [PyMongo async CRUD](https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/),
[async API migration semantics](https://www.mongodb.com/docs/languages/python/pymongo-driver/current/reference/migration/),
[Redis async lifecycle](https://redis.io/docs/latest/develop/clients/redis-py/async/),
and [XADD](https://redis.io/docs/latest/commands/xadd/).
Actual ACL, idempotency, load and restart evidence belongs in the Phase 4 report.
