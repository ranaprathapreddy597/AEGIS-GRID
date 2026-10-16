"""Read existing Evolus documents and derive citations only from exact source matches."""

from pathlib import Path

from aegis_ingestion.corpus import _atomic, cite, ingest_pdf, sha256
from aegis_ingestion.evolus import EvolusDocumentExtractor, ProviderUnavailable


async def extract_existing(
    client: EvolusDocumentExtractor,
    memory_id: str,
    document_id: str,
    checkpoint: Path,
    revision: str,
) -> dict[str, object]:
    raw = await client.download(memory_id, document_id)
    if not raw.startswith(b"%PDF-"):
        raise ProviderUnavailable("Original document is not a supported PDF")
    checkpoint.mkdir(parents=True, exist_ok=True)
    source = checkpoint / "source.pdf"
    if source.exists() and sha256(source.read_bytes()) != sha256(raw):
        raise ProviderUnavailable("Provider source changed; use a new revision checkpoint")
    # Download is read-only. Write only to this local caller-owned checkpoint directory.
    temporary = checkpoint / "source.pdf.tmp"
    temporary.write_bytes(raw)
    temporary.replace(source)
    _, pages = ingest_pdf(source, checkpoint / "pages", document_id, revision)
    chunks = await client.chunks(memory_id, document_id)
    mappings = []
    unmapped = 0
    for chunk in chunks:
        body = chunk.get("body")
        matches = [
            page
            for page in pages
            if isinstance(body, str) and body.strip() and len(body) <= 2000 and body in page.text
        ]
        if len(matches) == 1:
            mappings.append(cite(matches[0], body).model_dump())
        else:
            unmapped += 1
    # Unknown revisions, cross-page chunks, OCR and ambiguous matches never authorize actions.
    report: dict[str, object] = {
        "source_sha256": sha256(raw),
        "pages": len(pages),
        "matched_chunks": len(mappings),
        "unmapped_chunks": unmapped,
        "derived_citations": mappings,
        "provider_confidence": None,
        "provider_page_citations": False,
        "revision_authority": "unverified_provider",
        "decision": "no_action",
    }
    import json

    _atomic(checkpoint / "extraction.json", json.dumps(report, indent=2, sort_keys=True))
    return report
