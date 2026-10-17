"""Live dual-namespace read-only development checks; never regenerates stored vectors."""

import asyncio
import json
import time

from aegis_ingestion.dual_store import DualKnowledgeStore
from aegis_ingestion.knowledge import SemanticEmbedding
from dev import ROOT, read_env
from pydantic import SecretStr


async def main():
    env = read_env()
    store = DualKnowledgeStore(
        env["PINECONE_INDEX_HOST"],
        SecretStr(env["PINECONE_API_KEY"]),
        SemanticEmbedding(),
        ROOT / ".run/cloud-knowledge",
    )
    report = {
        "status": "BLOCKED",
        "writes": 0,
        "rows": [],
        "scope": "six fixed development queries; source recall@4, not diagnosis accuracy",
    }
    try:
        report["before"] = [await store.count(), await store.external.count()]
        cases = [
            ("maximum temperature in Celsius before a thermal alarm", "manual", "temperature"),
            ("allowable pressure in kilopascals", "manual", "pressure"),
            (
                "Opta micro PLC industrial controller Industrial IoT",
                "manual",
                "arduino-opta-datasheet",
            ),
            (
                "Raspberry Pi Compute Module embedded industrial carrier board",
                "manual",
                "raspberrypi-compute-module",
            ),
            (
                "hydraulic system condition monitoring cooler pump valve",
                "recovery",
                "uci-hydraulic",
            ),
            ("centrifugal pump vibration measurements CIRA", "recovery", "zenodo-cira-pump"),
        ]
        for query, kind, expected in cases:
            started = time.perf_counter()
            hits = await store.search(query, kind=kind)
            matching = [
                c
                for c in hits
                if (
                    expected in c.text.lower()
                    if expected in {"temperature", "pressure"}
                    else expected == c.metadata.get("source_id")
                )
            ]
            report["rows"].append(
                {
                    "query": query,
                    "kind": kind,
                    "expected": expected,
                    "source_recall_at_4": bool(matching),
                    "namespaces_present": len({c.metadata["synthetic"] for c in hits}) == 2,
                    "elapsed_ms": (time.perf_counter() - started) * 1000,
                    "citations": [store.citation(c) for c in hits],
                }
            )
        report["after"] = [await store.count(), await store.external.count()]
        report["correct"] = sum(row["source_recall_at_4"] for row in report["rows"])
        report["status"] = (
            "PASS"
            if report["correct"] == len(cases)
            and report["before"] == report["after"] == [1235, 103]
            and all(r["namespaces_present"] for r in report["rows"])
            else "PARTIAL"
        )
    finally:
        report["operations"] = [*store.operations, *store.external.operations]
        await store.close()
        (ROOT / "docs/results/cloud-retrieval-live.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )
    print(
        {
            "status": report["status"],
            "source_recall_at_4": report.get("correct"),
            "counts": report.get("after"),
        }
    )


if __name__ == "__main__":
    asyncio.run(main())
