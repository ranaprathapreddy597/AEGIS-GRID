"""Append-only checked analysis artifacts, separate from operational plans/actions."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from aegis_contracts.models import IncidentRecord
from aegis_contracts.optimization import RecoveryAssessment
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

from aegis_agents.optimizer import optimize, verify_artifact


class OptimizationService:
    def __init__(self, password: str, library: Path) -> None:
        self.library = library
        self.client: MongoClient[dict[str, Any]] = MongoClient(
            "mongo",
            27017,
            username="aegis_graph",
            password=password,
            authSource="aegis",
            serverSelectionTimeoutMS=1500,
            socketTimeoutMS=3000,
            maxPoolSize=2,
            retryWrites=False,
            w=1,
            journal=True,
        )

    def close(self) -> None:
        self.client.close()

    def read(self, identifier: str) -> RecoveryAssessment | None:
        value = self.client.aegis.analysis_artifacts.find_one({"_id": identifier})
        if value is None:
            return None
        report = RecoveryAssessment.model_validate_json(value["report_json"])
        if report.artifact_sha256 != identifier:
            raise ValueError("Artifact identity mismatch")
        verify_artifact(report)
        return report

    def run(self, record: IncidentRecord) -> RecoveryAssessment:
        if self.client.aegis.analysis_artifacts.count_documents({}, limit=501) > 500:
            raise ValueError("Local analysis artifact quota exceeded")
        report = optimize(record, self.library)
        try:
            self.client.aegis.analysis_artifacts.insert_one(
                {
                    "_id": report.artifact_sha256,
                    "report_json": report.model_dump_json(),
                    "expires_at": datetime.now(UTC) + timedelta(days=30),
                }
            )
        except DuplicateKeyError:
            existing = self.read(report.artifact_sha256)
            if existing != report:
                raise ValueError("Immutable artifact collision") from None
        return report
