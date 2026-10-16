"""Append-only monitoring journal. Runtime credentials cannot update/delete records."""

import asyncio
import hashlib
import json
import os
import sys
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from aegis_contracts.config import Settings
from aegis_contracts.models import (
    EdgeIncident,
    IncidentPage,
    IncidentRecord,
    IncidentReplay,
    StorageStatus,
)
from pymongo import AsyncMongoClient
from pymongo.errors import DuplicateKeyError, PyMongoError
from redis.asyncio import Redis
from redis.exceptions import RedisError

DB_NAME = "aegis"
STREAM = "aegis:telemetry:events"
MONITORING = ("events", "incidents", "snapshots", "fanout_receipts")
ALL_COLLECTIONS = (*MONITORING, "plans", "actions", "audit", "migrations")
GRAPH_COLLECTIONS = ("graph_checkpoints", "graph_writes")
ANALYSIS_COLLECTIONS = ("analysis_artifacts",)


class StorageUnavailable(RuntimeError):
    pass


class EventConflict(ValueError):
    pass


class TelemetryStore:
    def __init__(self, config: Settings) -> None:
        self.config = config
        self.writer: AsyncMongoClient[dict[str, Any]] | None = None
        self.reader: AsyncMongoClient[dict[str, Any]] | None = None
        self.redis: Redis | None = None
        self.mongo_state: Literal["disabled", "ready", "unavailable"] = "disabled"
        self.redis_state: Literal["disabled", "ready", "unavailable"] = "disabled"
        if config.storage_enabled:
            if (
                config.mongo_writer_password is None
                or config.mongo_reader_password is None
                or config.redis_writer_password is None
                or config.ingest_token is None
            ):
                raise ValueError("Persistent storage requires separately scoped local credentials")
            self.writer = AsyncMongoClient(
                "mongo",
                27017,
                username="aegis_ingestor",
                password=config.mongo_writer_password.get_secret_value(),
                authSource=DB_NAME,
                serverSelectionTimeoutMS=1500,
                connectTimeoutMS=1000,
                socketTimeoutMS=2000,
                maxPoolSize=8,
                w=1,
                journal=True,
                retryWrites=False,
                tz_aware=True,
            )
            self.reader = AsyncMongoClient(
                "mongo",
                27017,
                username="aegis_reader",
                password=config.mongo_reader_password.get_secret_value(),
                authSource=DB_NAME,
                serverSelectionTimeoutMS=1500,
                connectTimeoutMS=1000,
                socketTimeoutMS=2000,
                maxPoolSize=8,
                retryWrites=False,
                tz_aware=True,
            )
            self.redis = Redis(
                host="redis",
                port=6379,
                username="aegis_ingestor",
                password=config.redis_writer_password.get_secret_value(),
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=2,
                max_connections=8,
            )
            self.mongo_state = self.redis_state = "unavailable"

    async def close(self) -> None:
        if self.writer is not None:
            await self.writer.close()
        if self.reader is not None:
            await self.reader.close()
        if self.redis is not None:
            await self.redis.aclose()

    async def probe(self) -> StorageStatus:
        if self.writer is not None and self.reader is not None:
            try:
                await self.writer[DB_NAME].command("ping")
                await self.reader[DB_NAME].command("ping")
                self.mongo_state = "ready"
            except PyMongoError:
                self.mongo_state = "unavailable"
        if self.redis is not None:
            try:
                await self.redis.ping()
                self.redis_state = "ready"
            except RedisError:
                self.redis_state = "unavailable"
        return StorageStatus(mongo=self.mongo_state, redis=self.redis_state)

    def _writer(self) -> AsyncMongoClient[dict[str, Any]]:
        if self.writer is None:
            raise StorageUnavailable("Persistent journal is disabled")
        return self.writer

    def _reader(self) -> AsyncMongoClient[dict[str, Any]]:
        if self.reader is None:
            raise StorageUnavailable("Persistent journal is disabled")
        return self.reader

    @staticmethod
    def _record(document: dict[str, Any]) -> IncidentRecord:
        raw = document["payload_json"]
        if json.loads(raw) != document["payload"]:
            raise StorageUnavailable("Journal payload representation mismatch")
        event = EdgeIncident.model_validate_json(raw)
        digest = hashlib.sha256(raw.encode()).hexdigest()
        if digest != document["payload_sha256"]:
            raise StorageUnavailable("Journal record integrity mismatch")
        return IncidentRecord(
            incident_id=event.event_id,
            payload_sha256=digest,
            ingested_at=document["ingested_at"].isoformat(),
            event=event,
        )

    async def append(self, event: EdgeIncident) -> IncidentRecord:
        client = self._writer()
        now = datetime.now(UTC)
        now = now.replace(microsecond=now.microsecond // 1000 * 1000)
        digest = hashlib.sha256(event.model_dump_json().encode()).hexdigest()
        document = {
            "tenant_id": "local",
            "event_id": event.event_id,
            "run_id": event.run_id,
            "state_version": event.state_version,
            "schema_version": 1,
            "payload": event.model_dump(),
            "payload_json": event.model_dump_json(),
            "payload_sha256": digest,
            "ingested_at": now,
            "expires_at": now + timedelta(days=30),
        }
        try:
            await client[DB_NAME].events.insert_one(document)
        except DuplicateKeyError:
            existing = await client[DB_NAME].events.find_one(
                {"tenant_id": "local", "event_id": event.event_id}
            )
            if existing is None or existing["payload_sha256"] != digest:
                raise EventConflict(
                    "Event ID already exists with a different canonical payload"
                ) from None
            document = existing
        self.mongo_state = "ready"
        await self._materialize(document)
        return self._record(document)

    async def _materialize(self, document: dict[str, Any]) -> None:
        client = self._writer()
        event = EdgeIncident.model_validate(document["payload"])
        targets = []
        if event.kind == "anomaly":
            targets.append("incidents")
        if event.snapshot is not None:
            targets.append("snapshots")
        for collection in targets:
            try:
                await client[DB_NAME][collection].insert_one(
                    {k: v for k, v in document.items() if k != "_id"}
                )
            except DuplicateKeyError:
                pass  # Immutable derived view; canonical event uniqueness was checked above.

    async def publish_pending(self) -> int:
        if self.writer is None or self.redis is None:
            return 0
        # Mongo is authoritative. A failed Redis publish never removes a canonical event.
        cursor = await self.writer[DB_NAME].events.aggregate(
            [
                {"$match": {"tenant_id": "local"}},
                {
                    "$lookup": {
                        "from": "fanout_receipts",
                        "localField": "event_id",
                        "foreignField": "event_id",
                        "as": "receipts",
                    }
                },
                {"$match": {"receipts": {"$size": 0}}},
                {"$sort": {"_id": 1}},
                {"$limit": 100},
                {"$project": {"receipts": 0}},
            ]
        )
        count = 0
        async for document in cursor:
            await self._materialize(document)
            event = self._record(document)
            try:
                stream_id = await self.redis.xadd(
                    STREAM,
                    {
                        "event_id": event.incident_id,
                        "payload_sha256": event.payload_sha256,
                        "kind": event.event.kind,
                        "run_id": event.event.run_id,
                        "state_version": str(event.event.state_version),
                    },
                    maxlen=10000,
                    approximate=False,
                )
                await self.writer[DB_NAME].fanout_receipts.insert_one(
                    {
                        "tenant_id": "local",
                        "event_id": event.incident_id,
                        "stream_id": stream_id,
                        "expires_at": document["expires_at"],
                    }
                )
                self.redis_state = "ready"
                count += 1
            except DuplicateKeyError:
                pass
            except RedisError:
                self.redis_state = "unavailable"
                break
        return count

    async def incidents(self) -> IncidentPage:
        cursor = (
            self._reader()[DB_NAME]
            .incidents.find({"tenant_id": "local", "payload.origin": "edge_observer"})
            .sort("_id", -1)
            .limit(50)
        )
        return IncidentPage(items=[self._record(document) async for document in cursor])

    async def replay(self, incident_id: str) -> IncidentReplay | None:
        client = self._reader()
        document = await client[DB_NAME].incidents.find_one(
            {"tenant_id": "local", "event_id": incident_id}
        )
        if document is None:
            return None
        incident = self._record(document)
        cursor = (
            client[DB_NAME]
            .events.find({"tenant_id": "local", "run_id": incident.event.run_id})
            .sort([("state_version", 1), ("event_id", 1)])
            .limit(101)
        )
        fetched = [self._record(item) async for item in cursor]
        events = fetched[:100]
        digest = hashlib.sha256(
            "|".join(item.payload_sha256 for item in events).encode()
        ).hexdigest()
        return IncidentReplay(
            incident=incident,
            events=events,
            reproducibility_sha256=digest,
            snapshot_available=incident.event.snapshot is not None,
            truncated=len(fetched) > 100,
        )


async def migrate() -> None:
    # Only the disposable migration container receives admin bootstrap credentials.
    admin: AsyncMongoClient[dict[str, Any]] = AsyncMongoClient(
        "mongo",
        27017,
        username="aegis_local_admin",
        password=os.environ["AEGIS_MONGO_PASSWORD"],
        authSource="admin",
        serverSelectionTimeoutMS=5000,
        retryWrites=False,
    )
    redis_admin = Redis(
        host="redis",
        port=6379,
        password=os.environ["AEGIS_REDIS_PASSWORD"],
        decode_responses=True,
        socket_timeout=5,
    )
    try:
        database = admin[DB_NAME]
        existing = await database.list_collection_names()
        for name in (*ALL_COLLECTIONS, *GRAPH_COLLECTIONS, *ANALYSIS_COLLECTIONS):
            if name not in existing:
                await database.create_collection(name)
        await database.graph_checkpoints.create_index(
            [("thread_id", 1), ("checkpoint_ns", 1), ("checkpoint_id", -1)], unique=True
        )
        await database.graph_writes.create_index(
            [
                ("thread_id", 1),
                ("checkpoint_ns", 1),
                ("checkpoint_id", -1),
                ("task_id", 1),
                ("idx", 1),
            ],
            unique=True,
        )
        for name in GRAPH_COLLECTIONS:
            await database[name].create_index("created_at", expireAfterSeconds=30 * 86400)
        await database.analysis_artifacts.create_index("expires_at", expireAfterSeconds=0)
        for name in (*MONITORING, "plans", "actions", "audit"):
            await database[name].create_index([("tenant_id", 1), ("event_id", 1)], unique=True)
            await database[name].create_index("expires_at", expireAfterSeconds=0)
        await database.events.create_index([("tenant_id", 1), ("run_id", 1), ("state_version", 1)])
        await database.incidents.create_index([("tenant_id", 1), ("ingested_at", -1)])
        for name in ("events", "incidents", "snapshots"):
            await database.command(
                "collMod",
                name,
                validator={
                    "$jsonSchema": {
                        "bsonType": "object",
                        "required": [
                            "tenant_id",
                            "event_id",
                            "payload",
                            "payload_sha256",
                            "ingested_at",
                            "expires_at",
                        ],
                        "properties": {
                            "tenant_id": {"enum": ["local"]},
                            "event_id": {"bsonType": "string", "pattern": "^[0-9a-f]{64}$"},
                            "payload": {"bsonType": "object"},
                            "payload_sha256": {"bsonType": "string", "pattern": "^[0-9a-f]{64}$"},
                            "ingested_at": {"bsonType": "date"},
                            "expires_at": {"bsonType": "date"},
                        },
                    }
                },
                validationLevel="strict",
                validationAction="error",
            )
        writer_privileges = [
            {"resource": {"db": DB_NAME, "collection": name}, "actions": ["find", "insert"]}
            for name in MONITORING
        ]
        reader_privileges = [
            {"resource": {"db": DB_NAME, "collection": name}, "actions": ["find"]}
            for name in ALL_COLLECTIONS
            if name != "migrations"
        ]
        for role, privileges in [
            ("monitoring_append", writer_privileges),
            ("monitoring_read", reader_privileges),
            (
                "graph_checkpoint",
                [
                    {
                        "resource": {"db": DB_NAME, "collection": name},
                        "actions": ["find", "insert", "update", "listIndexes"],
                    }
                    for name in GRAPH_COLLECTIONS
                ]
                + [
                    {
                        "resource": {"db": DB_NAME, "collection": "analysis_artifacts"},
                        "actions": ["find", "insert"],
                    }
                ],
            ),
        ]:
            found = await database.command("rolesInfo", role)
            await database.command(
                "updateRole" if found["roles"] else "createRole",
                role,
                privileges=privileges,
                roles=[],
            )
        for user, role, name in [
            ("aegis_ingestor", "monitoring_append", "AEGIS_MONGO_WRITER_PASSWORD"),
            ("aegis_reader", "monitoring_read", "AEGIS_MONGO_READER_PASSWORD"),
            ("aegis_graph", "graph_checkpoint", "AEGIS_GRAPH_PASSWORD"),
        ]:
            found = await database.command("usersInfo", user)
            await database.command(
                "updateUser" if found["users"] else "createUser",
                user,
                pwd=os.environ[name],
                roles=[{"role": role, "db": DB_NAME}],
            )
        # redis-py shares sync/async command annotations; this client is asynchronous.
        await redis_admin.acl_setuser(
            "aegis_ingestor",
            enabled=True,
            reset=True,
            passwords=["+" + os.environ["AEGIS_REDIS_WRITER_PASSWORD"]],
            keys=[STREAM],
            categories=["-all"],
            commands=["+ping", "+xadd", "+xrange", "+xread", "+xlen", "+client|setinfo"],
        )
        await redis_admin.acl_save()
        await database.migrations.update_one(
            {"_id": "phase4-v1"},
            {"$setOnInsert": {"applied_at": datetime.now(UTC), "revision": 1}},
            upsert=True,
        )
        print(
            json.dumps(
                {
                    "migration": "phase4-v1",
                    "result": "PASS",
                    "runtime_privileges": "append-only monitoring; no update/delete/admin",
                }
            )
        )
    finally:
        await admin.close()
        await redis_admin.aclose()


if __name__ == "__main__":
    if sys.argv[1:] != ["migrate"]:
        raise SystemExit("Only explicit local migration invocation is supported")
    try:
        asyncio.run(migrate())
    except (PyMongoError, RedisError, KeyError):
        raise SystemExit(
            "Storage migration failed; check local configuration without printing secrets"
        ) from None
