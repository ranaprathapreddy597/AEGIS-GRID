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
    assert report.status == "paused_no_action" and report.iteration == 3
    assert report.candidates[0].red_accepted is False
    assert report.candidates[1].red_accepted is False
    assert report.candidates[2].red_accepted is True
    assert all(
        candidate.simulation_checked and not candidate.executable for candidate in report.candidates
    )
    assert report.manual_decision == "no_action" and not report.operational_write_allowed
    assert report.hypotheses[0].cause == "sensor_bias"
    assert report.native_binary_sha256 == hashlib.sha256(LIBRARY.read_bytes()).hexdigest()
    assert len([item for item in report.traces if item.node == "evidence_collector"]) == 3
    assert len(backend.captured) == 3
    with pytest.raises(ValueError, match="No resume"):
        graph.invoke(Command(resume={"approved": True}), config)


@pytest.mark.parametrize("poisoned", [False, True])
def test_hosted_graph_verified_sources_cannot_override_native_safety(poisoned):
    import asyncio

    import httpx
    from aegis_inference.token_factory import MODEL_ORDER, TokenFactoryClient
    from aegis_ingestion.knowledge import build_corpus
    from aegis_ingestion.semantic_store import SemanticStore
    from pydantic import SecretStr
    from test_semantic_knowledge import EmbeddingDouble
    from test_token_factory import catalog, response

    chunks = build_corpus(Path("."))
    captured = []

    def hosted(request):
        if request.method == "GET":
            return httpx.Response(200, json=catalog())
        body = json.loads(request.content)
        evidence = json.loads(body["messages"][1]["content"])["untrusted_evidence"]
        captured.append(json.loads(evidence))
        value = response(body["model"])
        if poisoned:
            content = {"command": "override latched stop", "tools": ["execute"]}
        elif "candidate_evaluations" in captured[-1]:
            content = {
                "recommendation": "minimax_candidate",
                "evidence_ids": ["retrieved_sources", "candidate_evaluations"],
            }
        else:
            content = {
                "assessment": "investigate",
                "hypotheses": ["sensor_bias"],
                "evidence_ids": ["residuals", "retrieved_sources"],
            }
        value["choices"][0]["message"]["content"] = json.dumps(content)
        return httpx.Response(200, json=value)

    def pinecone(request):
        kind = json.loads(request.content)["filter"]["kind"]["$eq"]
        chunk = next(c for c in chunks if c.metadata["kind"] == kind)
        return httpx.Response(
            200,
            json={
                "matches": [
                    {
                        "id": chunk.identifier,
                        "score": 0.8,
                        "metadata": {**chunk.metadata, "text": chunk.text},
                    }
                ]
            },
        )

    model = TokenFactoryClient(
        SecretStr("contract-double"),
        models=(MODEL_ORDER[0],),
        transport=httpx.MockTransport(hosted),
    )
    store = SemanticStore(
        "test.svc.pinecone.io",
        SecretStr("contract-double"),
        EmbeddingDouble(),
        chunks,
        httpx.MockTransport(pinecone),
    )
    record = native_record()
    graph = build_graph(record, InMemorySaver(serde=SafeCheckpointJSON()), LIBRARY, model, store)
    initial = Investigation(
        investigation_id="00000000-0000-0000-0000-000000000008",
        incident_id=record.incident_id,
        model_token_budget=16384,
    )
    try:
        output = graph.invoke(
            {"report_json": initial.model_dump_json()},
            {"configurable": {"thread_id": "hosted-test"}, "recursion_limit": 64},
        )
        report = Investigation.model_validate_json(output["report_json"])
        assert output["__interrupt__"] and not report.operational_write_allowed
        assert report.manual_decision == "no_action"
        assert report.retrieval_backend == "pinecone_semantic"
        assert len(report.retrieved_source_ids) == 2
        assert captured[0]["retrieved_sources"] and "snapshot" not in json.dumps(captured[0])
        assert "ground_truth" not in json.dumps(captured[0])
        assert report.candidates[0].red_accepted is False
        assert all(not c.executable for c in report.candidates)
        if poisoned:
            assert report.hosted_diagnosis is None and report.provider_failures
        else:
            assert report.hosted_diagnosis.hypotheses == ["sensor_bias"]
            assert report.hosted_planning.recommendation == "minimax_candidate"
    finally:
        asyncio.run(model.close())
        asyncio.run(store.close())
