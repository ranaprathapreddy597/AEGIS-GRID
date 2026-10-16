"""Scoped, persistent investigation service with no execution or public resume operation."""

from pathlib import Path
from typing import Any
from uuid import UUID

from aegis_contracts.investigation import Investigation
from aegis_contracts.models import IncidentRecord
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.mongodb import MongoDBSaver
from langsmith.run_helpers import tracing_context
from pymongo import MongoClient

from aegis_agents.graph import build_graph
from aegis_agents.serde import SafeCheckpointJSON


class InvestigationService:
    def __init__(self, password: str, library: Path) -> None:
        self.client: MongoClient[dict[str, Any]] = MongoClient(
            "mongo",
            27017,
            username="aegis_graph",
            password=password,
            authSource="aegis",
            serverSelectionTimeoutMS=1500,
            socketTimeoutMS=3000,
            maxPoolSize=4,
            retryWrites=False,
            w=1,
            journal=True,
        )
        self.saver = MongoDBSaver(
            self.client,
            db_name="aegis",
            checkpoint_collection_name="graph_checkpoints",
            writes_collection_name="graph_writes",
            serde=SafeCheckpointJSON(),
        )
        # Indexes are pre-provisioned by the admin migration, never by app credentials.
        # Set TTL after construction to avoid upstream 0.5.1's list/tuple index check.
        self.saver.ttl = 30 * 86400
        self.library = library

    def close(self) -> None:
        self.client.close()

    @staticmethod
    def config(identifier: str) -> RunnableConfig:
        return {
            "configurable": {"thread_id": "local:" + str(UUID(identifier))},
            "recursion_limit": 64,
        }

    def read(self, identifier: str) -> Investigation | None:
        saved = self.saver.get_tuple(self.config(identifier))
        if saved is None:
            return None
        return Investigation.model_validate_json(saved.checkpoint["channel_values"]["report_json"])

    def run(self, record: IncidentRecord, identifier: str) -> Investigation:
        config = self.config(identifier)
        existing = self.read(identifier)
        if (
            existing is None
            and self.client.aegis.graph_checkpoints.count_documents({}, limit=5001) > 5000
        ):
            raise ValueError("Local investigation checkpoint quota exceeded")
        if existing:
            if existing.incident_id != record.incident_id:
                raise ValueError("Investigation key belongs to another incident")
            if existing.status != "running":
                return existing
        graph = build_graph(record, self.saver, self.library)
        initial = Investigation(
            investigation_id=str(UUID(identifier)), incident_id=record.incident_id
        )
        try:
            with tracing_context(enabled=False):
                graph.invoke(
                    None if existing else {"report_json": initial.model_dump_json()}, config
                )
        except (ValueError, RuntimeError):
            failed = (self.read(identifier) or initial).model_copy(
                update={"status": "failed_closed", "refusal": "Investigation computation refused"}
            )
            graph.update_state(config, {"report_json": failed.model_dump_json()})
            return failed
        result = self.read(identifier)
        if result is None or result.status == "running":
            raise ValueError("Investigation failed to reach a durable outcome")
        return result
