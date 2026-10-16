"""Real LangGraph + C++ rollouts; in-memory checkpoint double is explicitly test-only."""

import hashlib
import json
from pathlib import Path

import pytest
from aegis_agents.graph import build_graph
from aegis_agents.serde import SafeCheckpointJSON
from aegis_contracts.investigation import Investigation
from aegis_contracts.models import EdgeIncident, IncidentRecord, IncidentSnapshot, SensorFrame
from aegis_edge.runner import SupervisedTwin
from aegis_edge.twin import scenario_from_file
from aegis_inference.client import OfflineDevelopmentBackend
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

LIBRARY = Path("/build/libaegis_twin.so")


def native_record():
    supervisor = SupervisedTwin(scenario_from_file(Path("data/scenarios"), "scenario-090"), LIBRARY)
    try:
        for _ in range(300):
            frame, status = supervisor.step(1.0)
            if status.latched:
                break
        snapshot = supervisor.incident_snapshot
        assert snapshot is not None
        event = EdgeIncident(
            event_id="a" * 64,
            run_id="00000000-0000-0000-0000-000000000001",
            kind="anomaly",
            state_version=frame.state_version,
            simulation_time_s=frame.simulation_time_s,
            evidence=status.evidence,
            observed=SensorFrame.from_twin(frame),
            snapshot=IncidentSnapshot.model_validate(snapshot.model_dump()),
        )
        return IncidentRecord(
            incident_id=event.event_id,
            ingested_at="2026-10-16T00:00:00Z",
            payload_sha256=hashlib.sha256(event.model_dump_json().encode()).hexdigest(),
            event=event,
        )
    finally:
        supervisor.close()


class CaptureBackend(OfflineDevelopmentBackend):
    captured = []

    async def investigate(self, untrusted_evidence, max_tokens=512):
        self.captured.append(json.loads(untrusted_evidence))
        assert not any(
            key in untrusted_evidence for key in ["fault_mask", "ground_truth", "seed", "snapshot"]
        )
        return await super().investigate(untrusted_evidence, max_tokens)


def test_actual_graph_cycles_runs_native_referee_and_pauses_without_mutation():
    record = native_record()
    memory = InMemorySaver(serde=SafeCheckpointJSON())
    backend = CaptureBackend()
    graph = build_graph(record, memory, LIBRARY, backend)
    report = Investigation(
        investigation_id="00000000-0000-0000-0000-000000000007", incident_id=record.incident_id
    )
    config = {"configurable": {"thread_id": "unit-only"}, "recursion_limit": 64}
    output = graph.invoke({"report_json": report.model_dump_json()}, config)
    report = Investigation.model_validate_json(output["report_json"])
    assert output["__interrupt__"]
    assert report.status == "paused_no_action" and report.iteration == 2
    assert report.candidates[0].red_accepted is False
    assert report.candidates[1].red_accepted is True
    assert all(
        candidate.simulation_checked and not candidate.executable for candidate in report.candidates
    )
    assert report.manual_decision == "no_action" and not report.operational_write_allowed
    assert report.hypotheses[0].cause == "sensor_bias"
    assert report.native_binary_sha256 == hashlib.sha256(LIBRARY.read_bytes()).hexdigest()
    assert len([item for item in report.traces if item.node == "evidence_collector"]) == 2
    assert len(backend.captured) == 2
    with pytest.raises(ValueError, match="No resume"):
        graph.invoke(Command(resume={"approved": True}), config)
