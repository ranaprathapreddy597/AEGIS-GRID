"""Live Pinecone reads inside the actual native LangGraph; no hosted inference or writes."""

import argparse
import asyncio
import hashlib
import json
import os
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from aegis_agents.graph import build_graph
from aegis_agents.serde import SafeCheckpointJSON
from aegis_contracts.investigation import Investigation
from aegis_contracts.models import EdgeIncident, IncidentRecord, SensorFrame
from aegis_edge.runner import SupervisedTwin
from aegis_edge.twin import scenario_from_file
from aegis_ingestion.acquisition import AcquisitionBlocked, atomic_json
from aegis_ingestion.knowledge import KnowledgeChunk, SemanticEmbedding, canonical, digest
from aegis_ingestion.real_store import RealWorldStore
from dev import ROOT, read_env
from langgraph.checkpoint.memory import InMemorySaver
from pydantic import SecretStr


def load_chunks():
    work = ROOT / ".run/real-world-v1"
    source_manifest = json.loads((work / "source-manifest.json").read_bytes())
    sources = {s["source_id"]: s for s in source_manifest["accepted"]}
    chunks = []
    for line in (work / "chunks.jsonl").read_text("utf-8").splitlines():
        row = json.loads(line)
        metadata = row["metadata"]
        source = sources[metadata["source_id"]]
        if (
            row["id"] != "agrw1-" + digest(canonical(metadata).encode())
            or metadata["text_sha256"] != digest(row["text"].encode())
            or metadata["source_sha256"] != source["sha256"]
            or metadata["license_evidence_sha256"] != source["license_evidence_sha256"]
            or metadata["license_id"] != source["license_id"]
            or metadata["source"] != source["download_url"]
            or metadata["authority"] != "external_reference_not_plant_authority"
            or metadata["synthetic"] is not False
        ):
            raise AcquisitionBlocked("External source manifest mismatch")
        chunks.append(KnowledgeChunk(row["id"], row["text"], metadata))
    receipt = json.loads((ROOT / "docs/results/real-world-ingestion.json").read_bytes())
    if receipt["status"] != "PASS" or receipt["corpus_sha256"] != digest(
        canonical([c.identifier for c in chunks]).encode()
    ):
        raise AcquisitionBlocked("Corpus has no matching passing ingestion evidence")
    return chunks


def worker() -> None:
    started = time.perf_counter()
    chunks = load_chunks()
    store = RealWorldStore(
        os.environ["PINECONE_INDEX_HOST"],
        SecretStr(os.environ["PINECONE_API_KEY"]),
        SemanticEmbedding(),
        chunks,
    )
    library = Path("/build/libaegis_twin.so")
    supervisor = SupervisedTwin(scenario_from_file(Path("data/scenarios"), "scenario-090"), library)
    report = {"status": "BLOCKED", "external_calls": "Pinecone reads only; no AMD calls or writes"}
    try:
        for _ in range(300):
            frame, safety = supervisor.step(1.0)
            if safety.latched:
                break
        snapshot = supervisor.incident_snapshot
        if snapshot is None:
            raise ValueError("No actual native fault incident")
        event = EdgeIncident(
            event_id=hashlib.sha256(snapshot.sha256.encode()).hexdigest(),
            run_id=str(uuid4()),
            kind="anomaly",
            state_version=frame.state_version,
            simulation_time_s=frame.simulation_time_s,
            evidence=safety.evidence,
            observed=SensorFrame.from_twin(frame),
            snapshot=snapshot,
        )
        record = IncidentRecord(
            incident_id=event.event_id,
            ingested_at=datetime.now(UTC).isoformat(),
            payload_sha256=digest(event.model_dump_json().encode()),
            event=event,
        )
        graph = build_graph(
            record, InMemorySaver(serde=SafeCheckpointJSON()), library, knowledge=store
        )
        initial = Investigation(investigation_id=str(uuid4()), incident_id=record.incident_id)
        output = graph.invoke(
            {"report_json": initial.model_dump_json()},
            {"configurable": {"thread_id": initial.investigation_id}, "recursion_limit": 64},
        )
        result = Investigation.model_validate_json(output["report_json"])
        passed = bool(output.get("__interrupt__")) and bool(result.retrieved_source_ids)
        passed = (
            passed
            and not result.operational_write_allowed
            and result.manual_decision == "no_action"
        )
        report.update(
            status="PASS" if passed else "FAIL",
            investigation=result.model_dump(),
            interrupted=bool(output.get("__interrupt__")),
            source_references=[
                {"id": i, **store.chunks[i].metadata} for i in result.retrieved_source_ids
            ],
            checkpoint_scope="Primitive-only in-memory acceptance; not hosted Mongo proof",
            actual_native_fault=True,
            physical_io=False,
        )
    finally:
        supervisor.close()
        report["elapsed_s"] = time.perf_counter() - started
        report["pinecone_operations"] = store.operations
        atomic_json(ROOT / "docs/results/real-world-langgraph.json", report)
        asyncio.run(store.close())
    print(json.dumps({"status": report["status"], "evidence": "real-world-langgraph.json"}))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        worker()
        return
    values = read_env()
    names = ["PINECONE_API_KEY", "PINECONE_INDEX_HOST"]
    environment = {**os.environ, **{n: values[n] for n in names}}
    cache = Path.home() / ".cache/huggingface/hub/models--minishlab--potion-base-8M"
    command = [
        "docker",
        "run",
        "--rm",
        "--network",
        "bridge",
        "--read-only",
        "--memory",
        "768m",
        "--cpus",
        "2",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges:true",
    ]
    for name in names:
        command += ["--env", name]
    command += [
        "--env",
        "HF_HUB_CACHE=/models",
        "--env",
        "HF_HUB_OFFLINE=1",
        "--volume",
        str(cache) + ":/models/models--minishlab--potion-base-8M:ro",
        "--volume",
        str(ROOT / "tools") + ":/app/tools:ro",
        "--volume",
        str(ROOT / ".run/real-world-v1") + ":/app/.run/real-world-v1:ro",
        "--volume",
        str(ROOT / "docs/results") + ":/app/docs/results",
        "aegis-grid-qa:real-world-v1",
        "python",
        "tools/check_real_world_graph.py",
        "--worker",
    ]
    subprocess.run(command, env=environment, check=True, timeout=300)


if __name__ == "__main__":
    main()
