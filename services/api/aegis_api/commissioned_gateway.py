"""Independent commissioned simulator policy, signature verifier and atomic native executor."""

import base64
import hashlib
import json
import struct
import time
from typing import Any

from aegis_agents.commissioned import verify_report
from aegis_contracts.authorization import ExecutionEnvelope
from aegis_contracts.commissioned import (
    CommissionedCapability,
    CommissionedPlan,
    CommissionedReceipt,
    CommissionedReport,
)
from aegis_contracts.models import IncidentRecord, TwinMeasurement
from aegis_edge.commissioning import (
    PLANT,
    REVISION,
    RULES_SHA256,
    canonical,
    rules,
    scenario,
    sha,
    stop_certificate,
)
from aegis_edge.sentinel import SafetyShield
from aegis_edge.twin import NativeTwin
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from aegis_api.capabilities import decode, encode, private_key
from aegis_api.gateway import SimulatorGateway


def sign(capability: CommissionedCapability, seed: str) -> str:
    payload = canonical(capability.model_dump())
    return encode(payload) + "." + encode(private_key(seed).sign(payload))


def verify(
    envelope: ExecutionEnvelope, public_spki: str
) -> tuple[CommissionedPlan, CommissionedCapability]:
    parts = envelope.capability.split(".")
    if len(parts) != 2:
        raise ValueError("Commissioned capability encoding refused")
    payload, signature = (decode(p) for p in parts)
    key = serialization.load_der_public_key(base64.b64decode(public_spki, validate=True))
    if not isinstance(key, Ed25519PublicKey):
        raise ValueError("Commissioned signature algorithm refused")
    try:
        key.verify(signature, payload)
    except InvalidSignature:
        raise ValueError("Commissioned capability signature refused") from None
    cap = CommissionedCapability.model_validate_json(payload)
    plan = CommissionedPlan.model_validate_json(envelope.action_json)
    now = int(time.time())
    if (
        not cap.iat <= now + 2
        or not now < cap.exp <= cap.iat + 60
        or cap.exp > plan.expires_at
        or now >= plan.expires_at
        or sha(envelope.action_json.encode()) != cap.plan_sha256
        or cap.jti != plan.nonce
        or any(
            getattr(cap, k) != getattr(plan, k)
            for k in (
                "action_id",
                "plant_id",
                "resource_id",
                "scope",
                "incident_id",
                "rules_revision",
                "rules_sha256",
                "expected_database_version",
                "expected_state_version",
            )
        )
    ):
        raise ValueError("Commissioned capability binding/expiration refused")
    return plan, cap


def receipt_digest(receipt: CommissionedReceipt) -> str:
    # Explicit IEEE754 encoding avoids Python/JS decimal-rendering differences.
    content = receipt.model_dump(exclude={"receipt_sha256"})
    for name in ("temperatures_before_c", "temperatures_after_c"):
        content[name] = [struct.pack(">d", value).hex() for value in content[name]]
    content["maximum_temperature_c"] = struct.pack(">d", receipt.maximum_temperature_c).hex()
    return sha(canonical(content))


class CommissionedGateway:
    def __init__(self, gateway: SimulatorGateway) -> None:
        self.client, self.library, self.public_key = (
            gateway.client,
            gateway.library,
            gateway.public_key,
        )

    def resource(self) -> dict[str, Any]:
        rules()
        value = self.client.aegis.commissioned_resources.find_one({"_id": PLANT})
        if value is None or value["policy"] != REVISION or value["rules_sha256"] != RULES_SHA256:
            raise ValueError("Commissioned administrative bootstrap required")
        record = IncidentRecord.model_validate(value["incident"])
        if (
            record.incident_id != value["incident_id"]
            or sha(canonical(record.event.model_dump())) != record.payload_sha256
        ):
            raise ValueError("Commissioned incident integrity refused")
        if record.event.snapshot is None or record.incident_id != sha(
            canonical({"plant": PLANT, "snapshot": record.event.snapshot.sha256})
        ):
            raise ValueError("Commissioned plant/incident origin binding refused")
        previous = "0" * 64
        version = 1
        snapshot = record.event.snapshot
        if snapshot is None:
            raise ValueError("Commissioned incident snapshot absent")
        snapshot_hash = snapshot.sha256
        for item in value["receipts"]:
            r = CommissionedReceipt.model_validate(item)
            if (
                receipt_digest(r) != r.receipt_sha256
                or r.previous_receipt_sha256 != previous
                or r.database_version_before != version
                or r.database_version_after != version + 1
                or r.snapshot_sha256_before != snapshot_hash
                or r.native_version_after != r.native_version_before + 120
                or r.incident_id != record.incident_id
                or r.rules_sha256 != RULES_SHA256
            ):
                raise ValueError("Commissioned receipt chain refused")
            previous, version, snapshot_hash = (
                r.receipt_sha256,
                version + 1,
                r.snapshot_sha256_after,
            )
        if (
            value["last_receipt_sha256"] != previous
            or value["version"] != version
            or value["snapshot"]["sha256"] != snapshot_hash
        ):
            raise ValueError("Commissioned committed state integrity refused")
        return value

    def report(self, identifier: str) -> CommissionedReport:
        value = self.client.aegis.commissioned_reports.find_one({"_id": identifier})
        if value is None:
            raise ValueError("Immutable commissioned report absent")
        return CommissionedReport.model_validate(value["report"])

    def check_current(self, plan: CommissionedPlan, resource: dict[str, Any]) -> None:
        policy = rules()
        report = self.report(plan.investigation_id)
        record = IncidentRecord.model_validate(resource["incident"])
        verify_report(report, record)
        certificate = stop_certificate(resource["snapshot"], self.library)
        state = json.loads(resource["snapshot"]["payload"])
        if (
            plan.rules_sha256 != RULES_SHA256
            or plan.incident_id != resource["incident_id"]
            or plan.investigation_sha256 != report.report_sha256
            or plan.expected_database_version != resource["version"]
            or plan.expected_state_version != state["version"]
            or plan.source_snapshot_sha256 != resource["snapshot"]["sha256"]
            or report.certificate != certificate
            or plan.native_binary_sha256 != hashlib.sha256(self.library.read_bytes()).hexdigest()
            or plan.safety_rollout_sha256 != certificate.sha256
            or plan.controls.model_dump() != policy["controls"]
            or state["scenario"] != scenario().model_dump()
            or not SafetyShield.authorize(
                plan.controls, plan.expected_state_version, state["version"]
            )
        ):
            raise ValueError("Commissioned scope, native state, rules or shared shield refused")

    def execute(
        self, envelope: ExecutionEnvelope, *, fail_before_commit: bool = False
    ) -> CommissionedReceipt:
        plan, cap = verify(envelope, self.public_key)
        proposal = self.client.aegis.commissioned_proposals.find_one({"_id": plan.action_id})
        if (
            proposal is None
            or proposal["status"] != "approved"
            or proposal["plan_sha256"] != cap.plan_sha256
            or proposal.get("capability") != envelope.capability
            or proposal["action_json"] != envelope.action_json
        ):
            raise ValueError("Durable commissioned human approval absent")
        resource = self.resource()
        if cap.jti in resource["nonces"] or resource["receipts"]:
            raise ValueError("Commissioned one-incident replay/repeat execution refused")
        self.check_current(plan, resource)
        state = json.loads(resource["snapshot"]["payload"])
        before = [c[0] for c in state["cells"]]
        maximum = max(before)
        with NativeTwin(scenario(), self.library) as twin:
            twin.restore(canonical(resource["snapshot"]))
            twin.controls(plan.expected_state_version, plan.controls)
            for _ in range(120):
                frame = twin.step(1.0)
                maximum = max(maximum, *(c.temperature_c for c in frame.ground_truth.cells))
                if (
                    maximum >= 70
                    or frame.loop_pressure_kpa > 180
                    or frame.ground_truth.feeder_power_w > 14500 + 1e-6
                ):
                    raise ValueError(
                        "Commissioned native verification refused; private copy discarded"
                    )
            frame = TwinMeasurement.model_validate_json(twin.raw())
            after = json.loads(twin.snapshot())
            final = json.loads(after["payload"])
            temperatures = [c.temperature_c for c in frame.ground_truth.cells]
            if max(temperatures) >= max(before) or final["scenario"] != state["scenario"]:
                raise ValueError("No measured cooldown or fault changed; private copy discarded")
            receipt = CommissionedReceipt(
                incident_id=plan.incident_id,
                action_id=plan.action_id,
                nonce=cap.jti,
                plan_sha256=cap.plan_sha256,
                rules_sha256=RULES_SHA256,
                previous_receipt_sha256=resource["last_receipt_sha256"],
                receipt_sha256="0" * 64,
                database_version_before=resource["version"],
                database_version_after=resource["version"] + 1,
                native_version_before=plan.expected_state_version,
                native_version_after=twin.current_version(),
                snapshot_sha256_before=plan.source_snapshot_sha256,
                snapshot_sha256_after=after["sha256"],
                native_binary_sha256=plan.native_binary_sha256,
                temperatures_before_c=before,
                temperatures_after_c=temperatures,
                maximum_temperature_c=maximum,
            )
        receipt = receipt.model_copy(update={"receipt_sha256": receipt_digest(receipt)})
        if fail_before_commit:
            raise ValueError("Injected commissioned failure before atomic commit")
        result = self.client.aegis.commissioned_resources.update_one(
            {
                "_id": PLANT,
                "version": plan.expected_database_version,
                "snapshot.sha256": plan.source_snapshot_sha256,
                "nonces": {"$ne": cap.jti},
                "receipts": [],
            },
            {
                "$set": {"snapshot": after, "last_receipt_sha256": receipt.receipt_sha256},
                "$inc": {"version": 1},
                "$push": {"receipts": receipt.model_dump(), "nonces": cap.jti},
            },
        )
        if result.modified_count != 1:
            raise ValueError("Commissioned state race refused; private copy discarded")
        return receipt
