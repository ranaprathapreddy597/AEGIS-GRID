"""Explicit user-authorized synthetic Pinecone ingestion and AMD/LangGraph acceptance."""

import argparse
import asyncio
import hashlib
import json
import os
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import httpx
import numpy as np
from aegis_agents.graph import build_graph
from aegis_agents.serde import SafeCheckpointJSON
from aegis_contracts.investigation import Investigation
from aegis_contracts.models import EdgeIncident, IncidentRecord, SensorFrame
from aegis_edge.runner import SupervisedTwin
from aegis_edge.twin import scenario_from_file
from aegis_inference.token_factory import TokenFactoryClient
from aegis_ingestion.evolus import ProviderUnavailable
from aegis_ingestion.knowledge import (
    EMBEDDING_ID,
    SemanticEmbedding,
    build_corpus,
    corpus_digest,
)
from aegis_ingestion.semantic_store import SemanticStore
from dev import read_env
from langgraph.checkpoint.memory import InMemorySaver
from pydantic import SecretStr

ROOT = Path(__file__).resolve().parents[1]
QUALITY = [
    ("maximum temperature in Celsius before a thermal alarm", "temperature"),
    ("heat overheating thermal engineering envelope", "temperature"),
    ("allowable pressure in kilopascals", "pressure"),
    ("hydraulic pressure limit kPa", "pressure"),
    ("coolant flow kilograms per second", "flow"),
    ("liquid flow rate kg/s", "flow"),
    ("machine workload load fraction operating limit", "load"),
    ("allowed production load fraction", "load"),
    ("human approval may not defeat a latched interlock", "LATCH-01"),
    ("preserve local stop and request human review", "STOP-01"),
    ("physical equipment connection permitted", "No physical I/O"),
    ("is this real OEM documentation", "NOT OEM AUTHORITY"),
]


async def wait_count(store: SemanticStore, expected: int) -> int:
    for _ in range(30):
        count = await store.count()
        if count == expected:
            return count
        await asyncio.sleep(2)
    raise ProviderUnavailable("Persisted namespace count did not converge")


async def ingest(values: dict[str, str], report: dict) -> None:
    chunks = build_corpus(ROOT)
    embedding = SemanticEmbedding(local_only=False)
    report.update(
        embedding=EMBEDDING_ID,
        native_dimension=embedding.model.dim,
        model_artifacts_sha256=embedding.artifacts,
        corpus_sha256=corpus_digest(chunks),
        expected_vectors=len(chunks),
        kinds=dict(Counter(c.metadata["kind"] for c in chunks)),
        synthetic=True,
    )
    host, key = values["PINECONE_INDEX_HOST"], SecretStr(values["PINECONE_API_KEY"])
    # Actual control-plane check before writing. Never persist the host/key or response body.
    async with httpx.AsyncClient(timeout=15, trust_env=False, follow_redirects=False) as client:
        response = await client.get(
            "https://api.pinecone.io/indexes/aegis-grid-memory",
            headers={"Api-Key": key.get_secret_value(), "X-Pinecone-Api-Version": "2025-10"},
        )
        report["index_metadata_http"] = response.status_code
        value = response.json() if response.status_code == 200 else {}
        if (
            value.get("host") != host
            or value.get("dimension") != 256
            or value.get("metric") != "cosine"
            or value.get("status", {}).get("ready") is not True
        ):
            raise ProviderUnavailable("Index identity/dimension/metric/readiness not verified")
    store = SemanticStore(host, key, embedding, chunks)
    report["namespace"] = store.namespace
    try:
        report["namespace_count_before"] = await store.count()
        report["upsert"] = await store.upsert()
        report["persisted_vectors"] = await wait_count(store, len(chunks))
        # Repeat an identical batch: idempotent IDs must not increase persisted counts.
        one = SemanticStore(host, key, embedding, chunks[:2])
        one.namespace = store.namespace
        try:
            report["idempotent_repeat"] = await one.upsert()
            report["count_after_repeat"] = await wait_count(store, len(chunks))
        finally:
            await one.close()
        rows = []
        for query, expected in QUALITY:
            hits = await store.search(query, kind="manual")
            rows.append(
                {
                    "query": query,
                    "expected": expected,
                    "top1_relevant": bool(hits and expected in hits[0].text),
                    "top5_relevant": any(expected in c.text for c in hits),
                    "ids": [c.identifier for c in hits],
                }
            )
        report["retrieval"] = {
            "scope": "12 fixed development queries; repeated synthetic manual pages, not held out",
            "top1_correct": sum(r["top1_relevant"] for r in rows),
            "top5_correct": sum(r["top5_relevant"] for r in rows),
            "queries": len(rows),
            "rows": rows,
        }
        vectors = embedding.encode(["coolant blockage", "flow obstruction", "music and dancing"])
        report["embedding_quality"] = {
            "repeat_exact": bool(
                np.array_equal(
                    vectors,
                    embedding.encode(["coolant blockage", "flow obstruction", "music and dancing"]),
                )
            ),
            "related_cosine": float(vectors[0] @ vectors[1]),
            "unrelated_cosine": float(vectors[0] @ vectors[2]),
            "unit_norm_finite": bool(
                np.isfinite(vectors).all() and np.allclose(np.linalg.norm(vectors, axis=1), 1)
            ),
        }
        # A wrong tenant filter must return no hits even for a stored vector.
        negative = await store.request(
            "/query",
            {
                "namespace": store.namespace,
                "vector": vectors[0].tolist(),
                "topK": 5,
                "filter": {"tenant_id": {"$eq": "unrelated-tenant-never-written"}},
            },
        )
        report["wrong_tenant_matches"] = len(negative.get("matches", []))
        if report["wrong_tenant_matches"]:
            raise ProviderUnavailable("Tenant filter acceptance failed")
        test = SemanticStore(
            host, key, embedding, chunks[:2], test_namespace="aegis-integration-test-" + uuid4().hex
        )
        try:
            report["isolated_test"] = {"namespace": test.namespace, "upsert": await test.upsert()}
            report["isolated_test"]["persisted_before_cleanup"] = await wait_count(test, 2)
        finally:
            try:
                await test.cleanup_test()
                report["isolated_test"]["persisted_after_cleanup"] = await wait_count(test, 0)
                report["isolated_test"]["operations"] = test.operations
            finally:
                await test.close()
        report["status"] = "PASS"
    finally:
        report["operations"] = store.operations
        await store.close()


def graph_proof(values: dict[str, str], report: dict, library: Path) -> None:
    chunks = build_corpus(ROOT)
    store = SemanticStore(
        values["PINECONE_INDEX_HOST"],
        SecretStr(values["PINECONE_API_KEY"]),
        SemanticEmbedding(),
        chunks,
    )
    model = TokenFactoryClient(SecretStr(values["INFERENCE_API_KEY"]))
    # Generate a new actual native fault; deliver only observed evidence to the hosted model.
    supervisor = SupervisedTwin(
        scenario_from_file(ROOT / "data/scenarios", "scenario-090"), library
    )
    try:
        for _ in range(300):
            frame, safety = supervisor.step(1.0)
            if safety.latched:
                break
        snapshot = supervisor.incident_snapshot
        if snapshot is None:
            raise ValueError("Native fault did not produce an incident")
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
            payload_sha256=hashlib.sha256(event.model_dump_json().encode()).hexdigest(),
            event=event,
        )
    finally:
        supervisor.close()
    graph = build_graph(record, InMemorySaver(serde=SafeCheckpointJSON()), library, model, store)
    initial = Investigation(
        investigation_id=str(uuid4()), incident_id=record.incident_id, model_token_budget=16384
    )
    try:
        output = graph.invoke(
            {"report_json": initial.model_dump_json()},
            {"configurable": {"thread_id": initial.investigation_id}, "recursion_limit": 64},
        )
        result = Investigation.model_validate_json(output["report_json"])
        report.update(
            status="PASS"
            if result.hosted_diagnosis and result.hosted_planning and result.retrieved_source_ids
            else "PARTIAL",
            investigation=result.model_dump(),
            interrupted=bool(output.get("__interrupt__")),
            checkpoint_scope="Safe JSON in-memory acceptance; Mongo persistence tested separately",
            plant_scope="Fresh native synthetic fault; C++ counterfactual recovery, no execution",
            source_references=[
                {"id": identifier, **store.chunks[identifier].metadata}
                for identifier in result.retrieved_source_ids
            ],
        )
    finally:
        report["amd_diagnostics"] = model.diagnostics
        report["amd_last_diagnostic"] = model.last_diagnostic
        report["amd_calls"] = model.calls
        report["amd_token_reservations"] = model.token_reservations
        report["pinecone_operations"] = store.operations
        asyncio.run(model.close())
        asyncio.run(store.close())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["ingest", "graph"])
    parser.add_argument("--library", type=Path, default=Path("/usr/local/lib/libaegis_twin.so"))
    args = parser.parse_args()
    values = {
        **read_env(),
        **{
            k: v
            for k, v in os.environ.items()
            if k in {"PINECONE_INDEX_HOST", "PINECONE_API_KEY", "INFERENCE_API_KEY"}
        },
    }
    report = {"status": "BLOCKED", "mi300x": "BLOCKED", "evolus": "BLOCKED"}
    started = time.perf_counter()
    output = ROOT / f"docs/results/live-knowledge-{args.mode}.json"
    try:
        if args.mode == "ingest":
            asyncio.run(ingest(values, report))
        else:
            graph_proof(values, report, args.library)
    except Exception as error:
        report["error_class"] = type(error).__name__
        # Never include exception strings/provider bodies, which may contain credentials/input.
        raise SystemExit(
            f"{args.mode}: blocked ({type(error).__name__}); see sanitized evidence"
        ) from None
    finally:
        report["elapsed_s"] = time.perf_counter() - started
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "evidence": output.name}))


if __name__ == "__main__":
    main()
