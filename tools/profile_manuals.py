"""Actual CPU manual retrieval development check; no cloud or semantic-model claim."""

import json
import resource
import statistics
import time

from aegis_ingestion.corpus import extract_constraints
from aegis_ingestion.library import fixture_library


def main() -> None:
    started = time.perf_counter()
    library = fixture_library()
    initialization = time.perf_counter() - started
    matches, timings, rows = 0, [], []
    for cell in range(1, 7):
        for quantity in ["temperature", "pressure", "flow", "load"]:
            query = f"CELL-0{cell} {quantity}"
            begin = time.perf_counter_ns()
            hits = library.index.search(query)
            timings.append((time.perf_counter_ns() - begin) / 1e6)
            page = next(p for p in library.pages if p.page_sha256 == hits[0].citation.page_sha256)
            correct = any(
                c.equipment_id == f"CELL-0{cell}" and c.quantity == quantity
                for c in extract_constraints(page)
            )
            matches += correct
            rows.append(
                {
                    "query": query,
                    "top1_relevant": correct,
                    "page_sha256": page.page_sha256,
                    "score": hits[0].score,
                }
            )
    print(
        json.dumps(
            {
                "execution": "actual CPU FAISS hashed lexical vectors; network-none",
                "pages": len(library.pages),
                "corpus_sha256": library.digest,
                "queries": 24,
                "top1_relevant": matches,
                "query_median_ms": statistics.median(timings),
                "query_p95_ms": sorted(timings)[22],
                "initialization_s": initialization,
                "peak_process_rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
                "decision": library.decision.model_dump(),
                "notes": "Development exact-term queries; not held-out semantic/OEM accuracy",
                "rows": rows,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
