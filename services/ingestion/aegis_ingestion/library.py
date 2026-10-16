"""Read-only fixture library with source and logical-page integrity verification."""

import json
from functools import lru_cache
from pathlib import Path

from aegis_contracts.manuals import ManualDocument, ManualEvidence, ManualPage

from aegis_ingestion.corpus import decide, page_digest, sha256
from aegis_ingestion.retrieval import ManualIndex


class ManualLibrary:
    def __init__(self, folder: Path) -> None:
        catalog = json.loads((folder / "catalog.json").read_text("utf-8"))
        raw = (folder / "pages.jsonl").read_bytes()
        if len(raw) > 16 * 1024 * 1024 or sha256(raw) != catalog["corpus_sha256"]:
            raise ValueError("Manual corpus integrity mismatch")
        self.pages = [ManualPage.model_validate_json(line) for line in raw.splitlines()]
        documents = [ManualDocument.model_validate(item) for item in catalog["documents"]]
        if len(self.pages) != catalog["pages"] or catalog["source"] != "synthetic_fixture":
            raise ValueError("Invalid corpus manifest")
        for name, document in zip(
            ["synthetic-manual.pdf", "contradictory-bulletin.pdf"], documents, strict=True
        ):
            if sha256((folder / name).read_bytes()) != document.source_sha256:
                raise ValueError("Original PDF integrity mismatch")
            pages = [p for p in self.pages if p.document_id == document.document_id]
            if [p.page for p in pages] != list(range(1, document.page_count + 1)):
                raise ValueError("Missing or duplicate source page")
            for page in pages:
                if (
                    page.source_sha256 != document.source_sha256
                    or page.revision != document.revision.revision
                    or page.page_sha256
                    != page_digest(page.document_id, page.revision, page.page, page.text)
                ):
                    raise ValueError("Page provenance mismatch")
        if {p.document_id for p in self.pages} != {d.document_id for d in documents}:
            raise ValueError("Uncatalogued document")
        self.digest = sha256(raw)
        self.index = ManualIndex(self.pages)
        self.decision = decide(self.pages)

    def evidence(self, query: str) -> ManualEvidence:
        return ManualEvidence(
            source="synthetic_fixture",
            corpus_sha256=self.digest,
            pages=len(self.pages),
            hits=self.index.search(query),
            decision=self.decision,
        )


@lru_cache(maxsize=1)
def fixture_library() -> ManualLibrary:
    return ManualLibrary(Path("data/manuals"))
