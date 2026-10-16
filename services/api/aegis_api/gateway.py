"""Protected simulator gateway. Snapshot, version, nonce and receipt commit atomically."""

import hashlib
import json
from pathlib import Path
from typing import Any

from aegis_agents.optimizer import canonical, digest
from aegis_contracts.authorization import (
    ExecutionEnvelope,
    MutationReceipt,
    ProposedPlan,
    receipt_hash_fields,
)
from aegis_contracts.models import SimulatorControls
from aegis_edge.sentinel import SafetyShield
from aegis_edge.twin import NativeTwin, scenario_from_file
from pymongo import MongoClient

from aegis_api.capabilities import verify

RESOURCE = "authorization-sandbox-01"
POLICY = "authorization-test-sandbox-v1"


def genesis(library: Path) -> dict[str, Any]:
    with NativeTwin(scenario_from_file(Path("data/scenarios"), "scenario-000"), library) as twin:
        for _ in range(30):
            twin.step(1.0)
        return {
            "_id": RESOURCE,
            "version": 1,
            "policy": POLICY,
            "snapshot": json.loads(twin.snapshot()),
            "receipts": [],
            "nonces": [],
            "last_receipt_sha256": "0" * 64,
        }


def certificate(snapshot: dict[str, Any], library: Path) -> str:
    with NativeTwin(scenario_from_file(Path("data/scenarios"), "scenario-000"), library) as twin:
        twin.restore(canonical(snapshot))
        result = twin.rollout(SafetyShield.emergency_controls(), 120, 0)
        if (
            result.violation_mask
            or result.maximum_temperature_c >= 70
            or result.maximum_pressure_kpa > 180.000001
            or result.maximum_feeder_power_w > 14500.000001
        ):
            raise ValueError("Independent native safety certificate refused")
        return digest(
            {
                "snapshot_sha256": snapshot["sha256"],
                "policy": POLICY,
                "binary_sha256": hashlib.sha256(library.read_bytes()).hexdigest(),
                "rollout": result.model_dump(),
            }
        )


class SimulatorGateway:
    def __init__(self, password: str, library: Path, public_key: str) -> None:
        self.library, self.public_key = library, public_key
        self.client: MongoClient[dict[str, Any]] = MongoClient(
            "mongo",
            27017,
            username="aegis_gateway",
            password=password,
            authSource="aegis",
            serverSelectionTimeoutMS=1500,
            socketTimeoutMS=3000,
            maxPoolSize=4,
            retryWrites=False,
            w=1,
            journal=True,
        )

    def close(self) -> None:
        self.client.close()

    def resource(self) -> dict[str, Any]:
        value = self.client.aegis.sandbox_resources.find_one({"_id": RESOURCE})
        if value is None or value["policy"] != POLICY:
            raise ValueError("Provisioned isolated authorization sandbox required")
        previous = "0" * 64
        version = 1
        for item in value["receipts"]:
            receipt = MutationReceipt.model_validate(item)
            content = receipt_hash_fields(receipt)
            if (
                digest(content) != receipt.receipt_sha256
                or receipt.previous_receipt_sha256 != previous
                or receipt.database_version_before != version
                or receipt.database_version_after != version + 1
                or receipt.native_version_after != receipt.native_version_before + 60
            ):
                raise ValueError("Receipt chain or version integrity refused")
            previous, version = receipt.receipt_sha256, version + 1
        if value["last_receipt_sha256"] != previous or value["version"] != version:
            raise ValueError("Resource/receipt chain integrity refused")
        if (
            value["receipts"]
            and value["snapshot"]["sha256"] != value["receipts"][-1]["snapshot_sha256_after"]
        ):
            raise ValueError("Committed snapshot differs from receipt")
        hashes = [
            item.get("maintenance_record_sha256")
            for item in value["receipts"]
            if item.get("maintenance_record_sha256")
        ]
        if hashes and digest(value.get("maintenance")) != hashes[-1]:
            raise ValueError("Maintenance record differs from committed receipt")
        return value

    def check_current(self, plan: ProposedPlan, resource: dict[str, Any]) -> None:
        snapshot = resource["snapshot"]
        state = json.loads(snapshot["payload"])
        if plan.maintenance:
            record = resource.get("maintenance", {"record_version": 0, "status": "not_recorded"})
            if (
                plan.maintenance.expected_record_version != record["record_version"]
                or plan.maintenance.status_before != record["status"]
            ):
                raise ValueError("Operational maintenance record is stale")
        if (
            plan.expected_database_version != resource["version"]
            or plan.expected_state_version != state["version"]
            or plan.source_snapshot_sha256 != snapshot["sha256"]
            or plan.native_binary_sha256 != hashlib.sha256(self.library.read_bytes()).hexdigest()
            or state["scenario"]["fault_mask"] != 0
            or plan.before_controls
            != SimulatorControls(
                pump=state["pump_target"],
                loads=state["load_targets"],
                valves=state["valve_targets"],
            )
            or plan.safety_rollout_sha256 != certificate(snapshot, self.library)
            or not SafetyShield.authorize(
                plan.controls, plan.expected_state_version, state["version"]
            )
        ):
            raise ValueError("Current state, native certificate or independent shield refused")

    def execute(
        self, envelope: ExecutionEnvelope, *, fail_before_commit: bool = False
    ) -> MutationReceipt:
        plan, capability = verify(envelope, self.public_key)
        proposal = self.client.aegis.auth_proposals.find_one({"_id": plan.action_id})
        if (
            proposal is None
            or proposal["status"] not in {"approved", "executed"}
            or proposal["plan_sha256"] != capability.plan_sha256
            or proposal.get("capability") != envelope.capability
            or proposal["action_json"] != envelope.action_json
        ):
            raise ValueError("Durable human approval absent or changed")
        resource = self.resource()
        for receipt in resource["receipts"]:
            if receipt["action_id"] == plan.action_id:
                if (
                    receipt["plan_sha256"] != capability.plan_sha256
                    or receipt["nonce"] != capability.jti
                ):
                    raise ValueError("Idempotency scope conflict")
                return MutationReceipt.model_validate(receipt)
        if capability.jti in resource["nonces"] or len(resource["receipts"]) >= 256:
            raise ValueError("Capability replay or local sandbox receipt quota")
        self.check_current(plan, resource)
        with NativeTwin(
            scenario_from_file(Path("data/scenarios"), "scenario-000"), self.library
        ) as twin:
            twin.restore(canonical(resource["snapshot"]))
            twin.controls(plan.expected_state_version, plan.controls)
            for _ in range(60):
                frame = twin.step(1.0)
                if max(cell.temperature_c for cell in frame.ground_truth.cells) >= 70:
                    raise ValueError("Simulator verification failed; private copy discarded")
            after = json.loads(twin.snapshot())
            maintenance = resource.get("maintenance")
            if plan.maintenance:
                maintenance = {
                    "record_id": plan.maintenance.record_id,
                    "record_version": plan.maintenance.expected_record_version + 1,
                    "status": plan.maintenance.status_after,
                    "reason": plan.maintenance.reason,
                    "last_action_id": plan.action_id,
                }
            receipt = MutationReceipt(
                receipt_format="sandbox-receipt-v2",
                tool="local_mongo_and_simulator" if plan.maintenance else "isolated_simulator",
                maintenance_record_sha256=digest(maintenance) if maintenance else None,
                receipt_sha256="0" * 64,
                previous_receipt_sha256=resource["last_receipt_sha256"],
                action_id=plan.action_id,
                nonce=capability.jti,
                plan_sha256=capability.plan_sha256,
                database_version_before=resource["version"],
                database_version_after=resource["version"] + 1,
                native_version_before=plan.expected_state_version,
                native_version_after=twin.current_version(),
                snapshot_sha256_after=after["sha256"],
                native_binary_sha256=plan.native_binary_sha256,
            )
        content = receipt_hash_fields(receipt)
        receipt = receipt.model_copy(update={"receipt_sha256": digest(content)})
        if fail_before_commit:
            raise ValueError("Injected test-only failure before atomic commit; copy discarded")
        fields = {"snapshot": after, "last_receipt_sha256": receipt.receipt_sha256}
        if maintenance:
            fields["maintenance"] = maintenance
        result = self.client.aegis.sandbox_resources.update_one(
            {
                "_id": RESOURCE,
                "version": plan.expected_database_version,
                "snapshot.sha256": plan.source_snapshot_sha256,
                "nonces": {"$ne": capability.jti},
            },
            {
                "$set": fields,
                "$inc": {"version": 1},
                "$push": {"receipts": receipt.model_dump(), "nonces": capability.jti},
            },
        )
        if result.modified_count != 1:
            for existing in self.resource()["receipts"]:
                if existing == receipt.model_dump():
                    return receipt
            raise ValueError("Atomic state/version race refused; private copy discarded")
        return receipt
