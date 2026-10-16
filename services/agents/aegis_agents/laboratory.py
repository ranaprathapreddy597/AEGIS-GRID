"""Bounded private copies only; no journal, plant, approval or external writes."""

import gzip
import hashlib
import json
from collections import deque
from datetime import UTC, datetime
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from aegis_contracts.laboratory import (
    FuturesEnsemble,
    PreviewRequest,
    PreviewSample,
    ScenarioPreview,
)
from aegis_contracts.models import EdgeIncident, IncidentRecord, ObservedSample, SensorFrame
from aegis_edge.runner import SupervisedTwin
from aegis_edge.twin import scenario_from_file

from aegis_agents.optimizer import digest


def analysis_incident(request: PreviewRequest, library: Path) -> IncidentRecord:
    """Build evidence from delivered observations in a new private analysis instance."""
    scenario = scenario_from_file(Path("data/scenarios"), request.scenario_id, request.seed)
    supervisor = SupervisedTwin(scenario, library)
    history: deque[ObservedSample] = deque(maxlen=21)
    try:
        for _ in range(1200):
            frame, status = supervisor.step()
            if not frame.measurement.packet_available:
                continue
            history.append(
                ObservedSample(
                    version=frame.measurement.sampled_version,
                    time_s=frame.measurement.sampled_time_s,
                    temperatures=[cell.temperature_c for cell in frame.cells],
                )
            )
            if status and status.latched and supervisor.incident_snapshot:
                identifier = digest(
                    {
                        "mode": "isolated_analysis",
                        "request": request.model_dump(),
                        "snapshot": supervisor.incident_snapshot.sha256,
                    }
                )
                event = EdgeIncident(
                    event_id=identifier,
                    run_id=str(uuid5(NAMESPACE_URL, "aegis-analysis:" + identifier)),
                    origin="isolated_analysis",
                    state_version=frame.state_version,
                    simulation_time_s=frame.simulation_time_s,
                    kind="anomaly",
                    evidence=status.evidence,
                    observed=SensorFrame.from_twin(frame),
                    observed_history=list(history),
                    snapshot=supervisor.incident_snapshot,
                )
                return IncidentRecord(
                    incident_id=identifier,
                    ingested_at=datetime.now(UTC).isoformat(),
                    payload_sha256=digest(event.model_dump()),
                    event=event,
                )
        raise ValueError("No detected anomaly in this bounded analysis; refusing invented incident")
    finally:
        supervisor.close()


def preview(request: PreviewRequest, library: Path) -> ScenarioPreview:
    scenario = scenario_from_file(Path("data/scenarios"), request.scenario_id, request.seed)
    baseline = SupervisedTwin(scenario, library, observe_only=True)
    shielded = SupervisedTwin(scenario, library)
    try:
        samples = []
        detection = None
        baseline_peak = shielded_peak = 0.0
        for step in range(1, 1201):
            before, _ = baseline.step()
            after, status = shielded.step()
            baseline_peak = max(
                baseline_peak, *(c.temperature_c for c in before.ground_truth.cells)
            )
            shielded_peak = max(shielded_peak, *(c.temperature_c for c in after.ground_truth.cells))
            if status and status.latched and detection is None:
                detection = after.simulation_time_s
            if step % 20 == 0:
                samples.append(PreviewSample(baseline=before, shielded=after, sentinel=status))
        value = dict(
            artifact_sha256="0" * 64,
            request=request,
            native_binary_sha256=hashlib.sha256(library.read_bytes()).hexdigest(),
            baseline_final_snapshot_sha256=json.loads(baseline.twin.snapshot())["sha256"],
            shielded_final_snapshot_sha256=json.loads(shielded.twin.snapshot())["sha256"],
            detection_s=detection,
            baseline_peak_c=baseline_peak,
            shielded_peak_c=shielded_peak,
            samples=samples,
        )
        report = ScenarioPreview(**value)
        return report.model_copy(
            update={"artifact_sha256": digest(report.model_dump(exclude={"artifact_sha256"}))}
        )
    finally:
        baseline.close()
        shielded.close()


def load_ensemble(directory: Path, library: Path) -> FuturesEnsemble:
    report = FuturesEnsemble.model_validate_json((directory / "ensemble.json").read_bytes())
    if digest(report.model_dump(exclude={"artifact_sha256"})) != report.artifact_sha256:
        raise ValueError("Future artifact integrity mismatch")
    if hashlib.sha256(library.read_bytes()).hexdigest() != report.native_binary_sha256:
        raise ValueError("Future artifact native version mismatch")
    with gzip.open(directory / "rows.json.gz", "rb") as source:
        raw = source.read(4_000_001)
    if len(raw) > 4_000_000 or hashlib.sha256(raw).hexdigest() != report.rows_sha256:
        raise ValueError("Future rows integrity mismatch")
    rows = json.loads(raw)
    if (
        len(rows) != report.pairs
        or sum(b.baseline for b in report.histogram) != report.pairs
        or sum(b.intervention for b in report.histogram) != report.pairs
    ):
        raise ValueError("Future count mismatch")
    return report
