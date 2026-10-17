"""Authenticated engineering fixture; no external manual or model can change this policy."""

import base64
import hashlib
import json
from collections import deque
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from aegis_contracts.commissioned import StopCertificate
from aegis_contracts.models import (
    EdgeIncident,
    IncidentRecord,
    ObservedSample,
    Scenario,
    SensorFrame,
)
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from aegis_edge.runner import SupervisedTwin
from aegis_edge.sentinel import SafetyShield
from aegis_edge.twin import NativeTwin

PLANT = "commissioned-simulator-01"
REVISION = "commissioned-stop-v1"
RULES_SHA256 = "a22dbd91274b67c8fd7f099a5f5a36ede6e8382967d5eca6b699e4b7d0fbe4e7"
PUBLIC_KEY = "HQOIfkIsaVO0LD89fl7cD7wuZXdYDVdiIcUX+08fX44="
DIRECTORY = Path("data/commissioned")


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def rules(directory: Path = DIRECTORY) -> dict[str, Any]:
    raw = (directory / "rules.json").read_bytes()
    signature = json.loads((directory / "signature.json").read_bytes())
    if (
        sha(raw) != RULES_SHA256
        or signature["public_key"] != PUBLIC_KEY
        or signature["sha256"] != RULES_SHA256
        or signature["algorithm"] != "Ed25519"
    ):
        raise ValueError("Commissioned rule origin/integrity pin refused")
    try:
        Ed25519PublicKey.from_public_bytes(base64.b64decode(PUBLIC_KEY)).verify(
            base64.b64decode(signature["signature"], validate=True), raw
        )
    except InvalidSignature:
        raise ValueError("Commissioned rule package signature refused") from None
    value: dict[str, Any] = json.loads(raw)
    if sha((directory / "scenario.json").read_bytes()) != value["scenario_sha256"]:
        raise ValueError("Commissioned scenario integrity refused")
    if (
        value["plant_id"] != PLANT
        or value["revision"] != REVISION
        or value["cells"] != [f"CELL-0{i}" for i in range(1, 7)]
        or value["controls"] != SafetyShield.emergency_controls().model_dump()
        or value["temperature_lt_c"] != 70
        or value["operating_stop_guard_c"] != 65
    ):
        raise ValueError("Shared plant rule applicability refused")
    return value


def scenario() -> Scenario:
    rules()
    return Scenario.model_validate_json((DIRECTORY / "scenario.json").read_bytes())


def incident(library: Path) -> IncidentRecord:
    supervisor = SupervisedTwin(scenario(), library)
    history: deque[ObservedSample] = deque(maxlen=21)
    try:
        for _ in range(600):
            frame, status = supervisor.step(1.0)
            if not frame.measurement.packet_available:
                continue
            history.append(
                ObservedSample(
                    version=frame.measurement.sampled_version,
                    time_s=frame.measurement.sampled_time_s,
                    temperatures=[c.temperature_c for c in frame.cells],
                )
            )
            snapshot = supervisor.incident_snapshot
            if status and status.latched and snapshot and status.evidence:
                # Frozen replay fork of the real pre-stop trigger. The source supervisor
                # has ALREADY applied the independent stop to its own native instance.
                identifier = sha(canonical({"plant": PLANT, "snapshot": snapshot.sha256}))
                event = EdgeIncident(
                    event_id=identifier,
                    run_id=str(uuid5(NAMESPACE_URL, PLANT + identifier)),
                    origin="isolated_analysis",
                    kind="anomaly",
                    state_version=frame.state_version,
                    simulation_time_s=frame.simulation_time_s,
                    evidence=status.evidence,
                    observed=SensorFrame.from_twin(frame),
                    observed_history=list(history),
                    snapshot=snapshot,
                )
                return IncidentRecord(
                    incident_id=identifier,
                    payload_sha256=sha(canonical(event.model_dump())),
                    ingested_at=datetime.now(UTC).isoformat(),
                    event=event,
                )
        raise ValueError("No real supervised incident in commissioned observation horizon")
    finally:
        supervisor.close()


def stop_certificate(snapshot: dict[str, Any], library: Path) -> StopCertificate:
    policy = rules()
    state = json.loads(snapshot["payload"])
    if (
        state["scenario"] != scenario().model_dump()
        or sha(snapshot["payload"].encode()) != snapshot["sha256"]
    ):
        raise ValueError("Wrong commissioned native scenario/snapshot")
    controls = SafetyShield.emergency_controls()
    if not SafetyShield.authorize(controls, state["version"], state["version"]):
        raise ValueError("Independent shield refused shared stop")
    with NativeTwin(scenario(), library) as twin:
        twin.restore(canonical(snapshot))
        rollout = twin.rollout(controls, policy["duration_s"], 0)
    if (
        rollout.violation_mask
        or rollout.maximum_temperature_c >= policy["temperature_lt_c"]
        or rollout.maximum_pressure_kpa > policy["pressure_max_kpa"] + 1e-6
        or rollout.maximum_feeder_power_w > policy["feeder_max_w"] + 1e-6
    ):
        raise ValueError("Independent all-six-cell native stop certificate refused")
    content = dict(
        snapshot_sha256=snapshot["sha256"],
        rules_sha256=RULES_SHA256,
        native_binary_sha256=sha(library.read_bytes()),
        maximum_temperature_c=rollout.maximum_temperature_c,
        maximum_pressure_kpa=rollout.maximum_pressure_kpa,
        maximum_feeder_power_w=rollout.maximum_feeder_power_w,
        duration_s=120,
        cells_checked=6,
    )
    return StopCertificate(sha256=sha(canonical(content)), **content)


def genesis(library: Path) -> dict[str, Any]:
    record = incident(library)
    if record.event.snapshot is None:
        raise ValueError("Native incident snapshot required")
    snapshot = {
        "sha256": record.event.snapshot.sha256,
        "payload": record.event.snapshot.payload_json,
    }
    stop_certificate(snapshot, library)
    return {
        "_id": PLANT,
        "policy": REVISION,
        "rules_sha256": RULES_SHA256,
        "incident_id": record.incident_id,
        "incident": record.model_dump(),
        "version": 1,
        "snapshot": snapshot,
        "receipts": [],
        "nonces": [],
        "last_receipt_sha256": "0" * 64,
    }
