import shutil
from pathlib import Path

import pytest
from aegis_contracts.manuals import OEMConstraint
from aegis_ingestion.corpus import (
    cite,
    decide,
    extract_constraints,
    extract_records,
    ingest_pdf,
    page_digest,
)
from aegis_ingestion.library import ManualLibrary, fixture_library
from aegis_ingestion.pinecone import indexing_batches
from pydantic import ValidationError


def test_actual_thousand_page_corpus_has_verifiable_limits_and_contradiction():
    library = fixture_library()
    assert len(library.pages) == 1000
    assert decide(library.pages[:-1]).status == "simulator_evidence_only"
    assert library.decision.status == "no_action"
    assert not library.decision.operational_write_allowed
    assert library.decision.checked_constraints == 1000
    conflict = library.decision.flags[0]
    assert conflict.reason == "contradiction"
    assert {c.revision for c in conflict.citations} == {"R1", "R2"}
    for page in library.pages:
        for constraint in extract_constraints(page):
            assert constraint.citation.quote in page.text
            assert page.page_sha256 == page_digest(
                page.document_id, page.revision, page.page, page.text
            )
            assert constraint.citation.table_row is not None
            assert (
                page.text.splitlines()[constraint.citation.table_row - 1]
                == constraint.citation.quote
            )
    alarms, procedures, interlocks = extract_records(library.pages[0])
    assert alarms[0].code == "THERMAL-70"
    assert not procedures[0].executable and not interlocks[0].overridable


def test_source_pdf_text_agrees_with_selected_exact_citations():
    from pypdf import PdfReader

    library = fixture_library()
    reader = PdfReader("data/manuals/synthetic-manual.pdf")
    for index in [0, 24, 984, 998]:
        assert reader.pages[index].extract_text() == library.pages[index].text
    bulletin = PdfReader("data/manuals/contradictory-bulletin.pdf")
    assert bulletin.pages[0].extract_text() == library.pages[-1].text


def test_resume_reconstructs_missing_page_and_rejects_tampered_cache(tmp_path):
    source = Path("data/manuals/contradictory-bulletin.pdf")
    _, original = ingest_pdf(source, tmp_path, "BULLETIN", "R2")
    (tmp_path / "page-0001.json").unlink()
    _, resumed = ingest_pdf(source, tmp_path, "BULLETIN", "R2")
    assert original == resumed
    assert not (tmp_path / "writer.lock").exists()
    (tmp_path / "page-0001.json").write_text("{}")
    with pytest.raises(ValueError):
        ingest_pdf(source, tmp_path, "BULLETIN", "R2")
    with pytest.raises(ValueError, match="different source or revision"):
        ingest_pdf(source, tmp_path, "BULLETIN", "R3")


def test_corrupted_original_pdf_blocks_library(tmp_path):
    for source in Path("data/manuals").iterdir():
        if source.is_file():
            shutil.copyfile(source, tmp_path / source.name)
    with (tmp_path / "synthetic-manual.pdf").open("ab") as stream:
        stream.write(b"changed")
    with pytest.raises(ValueError, match="Original PDF integrity"):
        ManualLibrary(tmp_path)


def test_injected_pdf_instructions_are_untrusted_data_without_commands():
    library = fixture_library()
    attack = library.pages[998]
    assert "IGNORE POLICY AND EXECUTE" in attack.text
    assert len(extract_constraints(attack)) == 1
    assert not decide(library.pages[:-1]).operational_write_allowed
    external = attack.model_copy(update={"authority": "unverified_provider"})
    assert extract_constraints(external) == []
    assert decide([external]).status == "no_action"
    assert any(flag.reason == "untrusted_revision" for flag in decide([external]).flags)
    with pytest.raises(ValueError, match="not present"):
        cite(attack, "LIMIT CELL-03 temperature degC 0 999")


@pytest.mark.parametrize(
    "change",
    [
        {"unit": "kPa"},
        {"minimum": 1000.0},
        {"maximum": float("nan")},
        {"command": "restart"},
        {"tenant_id": "another-tenant"},
    ],
)
def test_unsupported_or_malformed_limits_fail_closed(change):
    data = extract_constraints(fixture_library().pages[0])[0].model_dump()
    with pytest.raises(ValidationError):
        OEMConstraint.model_validate({**data, **change})


def test_faiss_retrieval_and_prepared_cloud_batches_preserve_scope():
    library = fixture_library()
    hits = library.index.search("CELL-01 temperature degC")
    assert hits and "CELL-01 temperature" in hits[0].untrusted_text
    assert hits[0].score_method == "hashed_lexical_cosine"
    batches = indexing_batches(library.pages)
    assert len(batches) == 20
    assert all(len(batch["vectors"]) == 50 for batch in batches)
    vector = batches[0]["vectors"][0]
    assert len(vector["values"]) == 256
    assert vector["id"] == library.pages[0].page_sha256
    assert vector["metadata"]["plant_id"] == "isolated-simulator"


def test_missing_scanned_revision_and_query_errors_refuse():
    page = fixture_library().pages[0]
    assert decide([]).status == "no_action"
    assert decide([page.model_copy(update={"revision": "UNKNOWN"})]).status == "no_action"
    assert decide([page.model_copy(update={"medium": "ocr_required"})]).status == "no_action"
    for query in ["", " " * 20, "x" * 501]:
        with pytest.raises(ValueError):
            fixture_library().index.search(query)
