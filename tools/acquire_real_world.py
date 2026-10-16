"""Public acquisition, deterministic processing, gated pilot and append-only Pinecone ingestion."""

import argparse
import asyncio
import csv
import json
import os
import re
from collections import Counter
from pathlib import Path

import httpx
from aegis_ingestion.acquisition import AcquisitionBlocked, PublicAcquirer, Source, atomic_json
from aegis_ingestion.evolus import ProviderUnavailable
from aegis_ingestion.knowledge import SemanticEmbedding, canonical, digest
from aegis_ingestion.real_store import RealWorldStore
from aegis_ingestion.real_world import REAL_NAMESPACE, process_sources
from dev import ROOT, read_env
from pydantic import SecretStr

WORK = ROOT / ".run/real-world-v1"
QUERIES = [
    ("Opta micro PLC industrial controller Industrial IoT", "arduino-opta-datasheet"),
    ("DIN rail industrial programmable logic controller connectivity", "arduino-opta-datasheet"),
    ("Raspberry Pi Compute Module embedded industrial carrier board", "raspberrypi-compute-module"),
    ("compact embedded computer module custom carrier board", "raspberrypi-compute-module"),
    ("NIST smart manufacturing test bed digital thread MTConnect", "nist-sms-test-bed"),
    ("digital thread design fabrication inspection data exchange", "nist-sms-test-bed"),
    ("hydraulic test rig cooler efficiency internal pump leakage flow", "uci-hydraulic"),
    ("sixty second oil cooling test cycles and internal pump leakage", "uci-hydraulic"),
    ("CIRA heating plant centrifugal pump motor vibration temperature", "zenodo-cira-pump"),
    ("heating boiler water pump recorded vibration and outlet pressure", "zenodo-cira-pump"),
]


async def acquire() -> dict:
    registry = json.loads((ROOT / "data/real-world-sources.json").read_bytes())
    client = PublicAcquirer(WORK / "originals")
    accepted, failures = [], []
    try:
        for row in registry["sources"]:
            source = Source.model_validate(row)
            try:
                accepted.append(await client.acquire(source))
            except AcquisitionBlocked as error:
                failures.append(
                    {"source_id": source.source_id, "status": "BLOCKED", "reason": str(error)}
                )
                if client.stopped:
                    break
    finally:
        manifest = {
            "accepted": accepted,
            "failures": failures,
            "excluded": registry["excluded"],
            "network_bytes": client.ledger["network_bytes"],
            "operations": client.operations,
            "authorization_or_quota_stop": client.stopped,
        }
        atomic_json(WORK / "source-manifest.json", manifest)
        await client.close()
    return manifest


def verified_chunks(manifest: dict):
    registry = json.loads((ROOT / "data/real-world-sources.json").read_bytes())
    approved = {s.source_id: s for row in registry["sources"] if (s := Source.model_validate(row))}
    for source in manifest["accepted"]:
        expected = approved[source["source_id"]]
        if any(source[k] != v for k, v in expected.model_dump().items()):
            raise AcquisitionBlocked("Source differs from reviewed registry")
        evidence = Path(source["license_evidence_path"]).read_bytes()
        if digest(evidence) != source["license_evidence_sha256"]:
            raise AcquisitionBlocked("License evidence integrity mismatch")
    chunks = process_sources(manifest, ROOT)
    (WORK / "chunks.jsonl").write_text(
        "".join(
            canonical({"id": c.identifier, "text": c.text, "metadata": c.metadata}) + "\n"
            for c in chunks
        ),
        encoding="utf-8",
    )
    return chunks


async def query_checks(store: RealWorldStore) -> dict:
    rows = []
    for query, expected in QUERIES:
        hits = await store.search(query)
        rows.append(
            {
                "query": query,
                "expected_source": expected,
                "top1_correct": bool(hits and hits[0].metadata["source_id"] == expected),
                "top5_correct": any(c.metadata["source_id"] == expected for c in hits),
                "ids": [c.identifier for c in hits],
            }
        )
    return {
        "method": store.retrieval_method,
        "queries": len(rows),
        "top1_correct": sum(r["top1_correct"] for r in rows),
        "top5_correct": sum(r["top5_correct"] for r in rows),
        "rows": rows,
        "scope": "Fixed development source-relevance queries, not fault diagnosis accuracy",
    }


async def persisted(store: RealWorldStore, expected: int) -> int:
    for _ in range(30):
        count = await store.count()
        if count == expected:
            return count
        await asyncio.sleep(2)
    raise ProviderUnavailable("Namespace count did not converge")


async def upload(manifest: dict, chunks: list, report: dict) -> None:
    values = {
        **read_env(),
        **{
            k: os.environ[k] for k in ("PINECONE_API_KEY", "PINECONE_INDEX_HOST") if k in os.environ
        },
    }
    key = SecretStr(values["PINECONE_API_KEY"])
    async with httpx.AsyncClient(timeout=15, trust_env=False, follow_redirects=False) as client:
        response = await client.get(
            "https://api.pinecone.io/indexes/aegis-grid-memory",
            headers={"Api-Key": key.get_secret_value(), "X-Pinecone-Api-Version": "2025-10"},
        )
        report["index_metadata_http"] = response.status_code
        metadata = response.json() if response.status_code == 200 else {}
        if (
            metadata.get("host") != values["PINECONE_INDEX_HOST"]
            or metadata.get("dimension") != 256
            or metadata.get("metric") != "cosine"
            or not metadata.get("status", {}).get("ready")
        ):
            raise ProviderUnavailable("Index identity/metric/dimension/readiness not verified")
    embedding = SemanticEmbedding()
    prior = json.loads((ROOT / "docs/results/live-knowledge-ingest.json").read_bytes())
    if prior["model_artifacts_sha256"] != embedding.artifacts:
        raise AcquisitionBlocked("Semantic model differs from verified artifacts")
    report["embedding_artifacts_sha256"] = embedding.artifacts
    store = RealWorldStore(values["PINECONE_INDEX_HOST"], key, embedding, chunks)
    try:
        before = await store.request("/describe_index_stats", {})
        initial = await store.count()
        report["namespace_count_before"] = initial
        # Four deterministic leading chunks per source; first live write has at most 20 records.
        pilot = []
        for source_id in sorted({c.metadata["source_id"] for c in chunks}):
            selected = sorted(
                [c for c in chunks if c.metadata["source_id"] == source_id],
                key=lambda c: (
                    [int(n) for n in re.findall(r"\d+", c.metadata["location"])],
                    c.metadata["normalized_start"],
                    c.identifier,
                ),
            )
            pilot.extend(selected[:4])
        if not 1 <= len(pilot) <= 20:
            raise AcquisitionBlocked("Pilot record bound exceeded")
        pilot_ids = [c.identifier for c in pilot]
        report["pilot"] = {"status": "RUNNING", "selected_ids": pilot_ids}
        atomic_json(ROOT / "docs/results/real-world-ingestion.json", report)
        await store.append_new(pilot, maximum=20)
        report["pilot"]["persisted_namespace_count"] = await persisted(
            store, initial + len(store.uploaded)
        )
        records = await store.fetch(pilot_ids)
        if set(records) != set(pilot_ids):
            raise ProviderUnavailable("Pilot fetch incomplete")
        store.verify_records(records)
        report["pilot"]["metadata_and_vectors_verified"] = len(records)
        checks = await query_checks(store)
        report["pilot"]["retrieval"] = checks
        if checks["top5_correct"] != checks["queries"]:
            raise AcquisitionBlocked("Pilot retrieval gate failed; bulk writes forbidden")
        negative = await store.request(
            "/query",
            {
                "namespace": REAL_NAMESPACE,
                "vector": embedding.encode([QUERIES[0][0]])[0].tolist(),
                "topK": 5,
                "filter": {"tenant_id": {"$eq": "unrelated-tenant-never-written"}},
            },
        )
        if negative.get("matches") != []:
            raise ProviderUnavailable("Pilot negative metadata filter failed")
        report["pilot"].update(status="PASS", negative_filter_matches=0)
        report["status"] = "PILOT_VERIFIED_BULK_RUNNING"
        atomic_json(ROOT / "docs/results/real-world-ingestion.json", report)
        # Only the explicit passing pilot branch reaches bulk writes.
        remaining = [c for c in chunks if c.identifier not in pilot_ids]
        for offset in range(0, len(remaining), 50):
            await store.append_new(remaining[offset : offset + 50])
        report["namespace_count_after"] = await persisted(store, initial + len(store.uploaded))
        for offset in range(0, len(chunks), 50):
            requested = [c.identifier for c in chunks[offset : offset + 50]]
            records = await store.fetch(requested)
            if set(records) != set(requested):
                raise ProviderUnavailable("Final persisted manifest fetch incomplete")
            store.verify_records(records)
        report["retrieval"] = await query_checks(store)
        after = await store.request("/describe_index_stats", {})
        others_before = {k: v for k, v in before["namespaces"].items() if k != REAL_NAMESPACE}
        others_after = {k: v for k, v in after["namespaces"].items() if k != REAL_NAMESPACE}
        report["other_namespace_counts_unchanged"] = others_before == others_after
        if not report["other_namespace_counts_unchanged"]:
            raise ProviderUnavailable("Other namespace counts changed during run")
        report["verified_owned_records"] = len(chunks)
        report["status"] = (
            "PASS" if report["retrieval"]["top5_correct"] == len(QUERIES) else "PARTIAL"
        )
    finally:
        report.update(
            uploaded_records=len(store.uploaded),
            skipped_existing=len(store.skipped),
            failed_or_unconfirmed_ids=store.unconfirmed,
            operations=store.operations,
        )
        report["not_attempted_or_skipped_ids"] = sorted(
            set(c.identifier for c in chunks)
            - set(store.uploaded)
            - set(store.skipped)
            - set(store.unconfirmed)
        )
        await store.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["acquire", "process", "upload", "all"])
    args = parser.parse_args()
    output_name = (
        "real-world-ingestion.json"
        if args.mode in {"upload", "all"}
        else (
            "real-world-acquisition.json"
            if args.mode == "acquire"
            else "real-world-processing.json"
        )
    )
    WORK.mkdir(parents=True, exist_ok=True)
    lock = WORK / "pipeline.lock"
    descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(descriptor)
    report = {"status": "BLOCKED", "namespace": REAL_NAMESPACE, "index": "aegis-grid-memory"}
    try:
        manifest = (
            asyncio.run(acquire())
            if args.mode in {"acquire", "all"}
            else json.loads((WORK / "source-manifest.json").read_bytes())
        )
        report["acquisition"] = manifest
        if manifest.get("authorization_or_quota_stop"):
            raise AcquisitionBlocked("Authorization/quota/budget stop; no further provider actions")
        if args.mode in {"process", "upload", "all"}:
            chunks = verified_chunks(manifest)
            report.update(
                eligible_chunks=len(chunks),
                chunks_by_source=dict(Counter(c.metadata["source_id"] for c in chunks)),
                corpus_sha256=digest(canonical([c.identifier for c in chunks]).encode()),
            )
            pump = next(s for s in manifest["accepted"] if s["source_id"] == "zenodo-cira-pump")
            with Path(pump["local_path"]).open(encoding="utf-8-sig", newline="") as stream:
                rows = list(csv.DictReader(stream))
            report["pump_quality"] = {
                "rows": len(rows),
                "missing_cells": sum(not v.strip() for row in rows for v in row.values()),
                "imputation": False,
                "units_normalized": False,
                "schema_note": "Provider description uses some .SV field suffixes; CSV uses .PV. "
                "No unit conversion, fault diagnosis or limits inferred.",
            }
            if args.mode in {"upload", "all"}:
                asyncio.run(upload(manifest, chunks, report))
            else:
                report["status"] = "PROCESSED"
        else:
            report["status"] = "ACQUIRED"
    except Exception as error:
        report["status"] = "BLOCKED"
        report["error_class"] = type(error).__name__
        if isinstance(error, (AcquisitionBlocked, ProviderUnavailable)):
            report["blocker"] = str(error)
        print(json.dumps({"status": "BLOCKED", "error_class": type(error).__name__}))
    finally:
        atomic_json(ROOT / "docs/results" / output_name, report)
        lock.unlink()
    print(
        json.dumps(
            {"status": report["status"], "uploaded_records": report.get("uploaded_records", 0)}
        )
    )


if __name__ == "__main__":
    main()
