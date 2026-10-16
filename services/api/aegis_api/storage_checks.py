"""Actual local DB/ACL/idempotency/load verification using application credentials."""

import asyncio
import hashlib
import json
import statistics
import time
import uuid

from aegis_contracts.config import Settings
from aegis_contracts.models import EdgeIncident
from pymongo.errors import OperationFailure
from redis.exceptions import NoPermissionError

from aegis_api.storage import DB_NAME, STREAM, EventConflict, TelemetryStore


async def main() -> None:
    store = TelemetryStore(Settings.from_env())
    try:
        status = await store.probe()
        if status.mongo != "ready" or status.redis != "ready":
            raise RuntimeError("Real local storage is mandatory for this check")
        if store.writer is None or store.reader is None or store.redis is None:
            raise RuntimeError("Storage identities missing")
        if store.writer.write_concern.document != {"j": True, "w": 1}:
            raise RuntimeError("Monitoring acknowledgements must wait for Mongo journaling")
        run_id = str(uuid.uuid4())
        first = EdgeIncident(
            event_id=hashlib.sha256(run_id.encode()).hexdigest(),
            run_id=run_id,
            state_version=1,
            simulation_time_s=0.5,
            kind="anomaly",
            evidence=[],
            origin="storage_contract_fixture",
        )
        record = await store.append(first)
        if record != await store.append(first):
            raise RuntimeError("Idempotent append changed the record")
        try:
            await store.append(first.model_copy(update={"simulation_time_s": 99.0}))
        except EventConflict:
            pass
        else:
            raise RuntimeError("Changed payload accepted under an existing ID")
        denied = 0
        operations = [
            store.writer[DB_NAME].events.update_one(
                {"event_id": first.event_id}, {"$set": {"schema_version": 99}}
            ),
            store.writer[DB_NAME].events.delete_one({"event_id": first.event_id}),
            store.reader[DB_NAME].events.insert_one({"event_id": "read-identity-cannot-write"}),
            store.writer[DB_NAME].plans.insert_one({"event_id": "monitoring-cannot-write-plans"}),
        ]
        for operation in operations:
            try:
                await operation
            except OperationFailure as exc:
                if exc.code != 13:
                    raise RuntimeError("Unexpected Mongo refusal category") from None
                denied += 1
            else:
                raise RuntimeError("Restricted identity allowed a forbidden write")
        for redis_operation in [
            store.redis.set("unallowlisted-key", "storage-contract-fixture"),
            store.redis.xadd("unallowlisted-key", {"x": "1"}),
        ]:
            try:
                await redis_operation
            except NoPermissionError:
                denied += 1
            else:
                raise RuntimeError("Redis ACL allowed a forbidden operation")
        timings = []

        async def append(index: int) -> None:
            event = EdgeIncident(
                event_id=hashlib.sha256(f"{run_id}:{index}".encode()).hexdigest(),
                run_id=run_id,
                state_version=index + 2,
                simulation_time_s=float(index + 1),
                kind="anomaly",
                evidence=[],
                origin="storage_contract_fixture",
            )
            start = time.perf_counter_ns()
            await store.append(event)
            timings.append((time.perf_counter_ns() - start) / 1e6)

        begin = time.perf_counter()
        for offset in range(0, 128, 8):
            await asyncio.gather(*(append(index) for index in range(offset, offset + 8)))
        duration = time.perf_counter() - begin
        for _ in range(5):
            await store.publish_pending()
        replay = await store.replay(first.event_id)
        if replay is None or replay.incident.payload_sha256 != record.payload_sha256:
            raise RuntimeError("Actual journal replay mismatch")
        receipt = await store.reader[DB_NAME].fanout_receipts.find_one({"event_id": first.event_id})
        if receipt is None:
            raise RuntimeError("Missing actual Redis delivery receipt")
        rows = await store.redis.xrange(STREAM, min=receipt["stream_id"], max=receipt["stream_id"])
        if not rows or rows[0][1] is None or rows[0][1]["event_id"] != first.event_id:
            raise RuntimeError("Redis stream payload mismatch")
        print(
            json.dumps(
                {
                    "result": "PASS",
                    "actual_services": ["MongoDB", "Redis"],
                    "forbidden_operations_denied": denied,
                    "mongo_write_concern": store.writer.write_concern.document,
                    "idempotency": "identical retry / changed payload denied",
                    "load_test": {
                        "events": 128,
                        "concurrency": 8,
                        "wall_s": duration,
                        "append_median_ms": statistics.median(timings),
                        "append_p95_ms": sorted(timings)[int(len(timings) * 0.95)],
                    },
                    "redis_delivery_verified": True,
                    "fixture_origin": "storage_contract_fixture",
                    "note": "App credentials; fixtures excluded from default incident listing",
                },
                indent=2,
            )
        )
    finally:
        await store.close()


if __name__ == "__main__":
    asyncio.run(main())
