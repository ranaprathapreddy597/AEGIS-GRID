"""Bounded PDF ingestion, exact evidence mapping and deterministic refusal."""

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Literal

from aegis_contracts.manuals import (
    AlarmCode,
    AmbiguityFlag,
    Citation,
    ExtractionConfidence,
    ManualDecision,
    ManualDocument,
    ManualPage,
    OEMConstraint,
    Procedure,
    Revision,
    SafetyInterlock,
)
from pypdf import PdfReader


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def page_digest(document: str, revision: str, page: int, text: str) -> str:
    return sha256(json.dumps([document, revision, page, text], ensure_ascii=True).encode())


def ingest_pdf(
    source: Path,
    checkpoint: Path,
    document_id: str,
    revision: str,
    *,
    window: int = 25,
    authority: Literal["synthetic_fixture", "unverified_provider"] = "unverified_provider",
) -> tuple[ManualDocument, list[ManualPage]]:
    """Local parser, not Evolus/OCR. Resume validated page files; atomic checkpoints."""
    if not 1 <= window <= 100 or source.stat().st_size > 32 * 1024 * 1024:
        raise ValueError("PDF exceeds local ingestion limits")
    raw = source.read_bytes()
    source_hash = sha256(raw)
    reader = PdfReader(source, strict=True)
    if reader.is_encrypted or not 1 <= len(reader.pages) <= 1000:
        raise ValueError("Unsupported encrypted PDF or page count")
    document = ManualDocument(
        document_id=document_id,
        source_sha256=source_hash,
        title="AEGIS synthetic simulator manual - not OEM authority",
        revision=Revision(revision=revision, authority=authority),
        page_count=len(reader.pages),
    )
    checkpoint.mkdir(parents=True, exist_ok=True)
    lock = checkpoint / "writer.lock"
    descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.close(descriptor)
        manifest = checkpoint / "document.json"
        if (
            manifest.exists()
            and ManualDocument.model_validate_json(manifest.read_bytes()) != document
        ):
            raise ValueError("Checkpoint belongs to a different source or revision")
        _atomic(manifest, document.model_dump_json())
        pages = []
        for offset in range(0, len(reader.pages), window):
            for index in range(offset, min(offset + window, len(reader.pages))):
                text = reader.pages[index].extract_text() or ""
                if len(text) > 100000:
                    raise ValueError("Page text exceeds bound")
                page = ManualPage(
                    document_id=document_id,
                    revision=revision,
                    page=index + 1,
                    source_sha256=source_hash,
                    page_sha256=page_digest(document_id, revision, index + 1, text),
                    text=text,
                    medium="born_digital" if text.strip() else "ocr_required",
                    authority=authority,
                    confidence=ExtractionConfidence(derived_method="unmapped"),
                )
                target = checkpoint / f"page-{index + 1:04}.json"
                if target.exists():
                    if ManualPage.model_validate_json(target.read_bytes()) != page:
                        raise ValueError("Cached page differs from original PDF")
                else:
                    _atomic(target, page.model_dump_json())
                pages.append(page)
        return document, pages
    finally:
        lock.unlink(missing_ok=True)


def _atomic(path: Path, data: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def cite(page: ManualPage, quote: str, row: int | None = None) -> Citation:
    if quote not in page.text or page.page_sha256 != page_digest(
        page.document_id, page.revision, page.page, page.text
    ):
        raise ValueError("Evidence is not present on the cited page")
    return Citation(
        document_id=page.document_id,
        revision=page.revision,
        source_sha256=page.source_sha256,
        page_sha256=page.page_sha256,
        page=page.page,
        quote=quote,
        table_row=row,
    )


ROW = re.compile(
    r"LIMIT (CELL-0[1-6]) (temperature|pressure|flow|load) "
    r"(degC|kPa|kg/s|fraction) (-?\d+(?:\.\d+)?) (-?\d+(?:\.\d+)?)"
)


def extract_constraints(page: ManualPage) -> list[OEMConstraint]:
    """Exact synthetic table grammar only. Arbitrary provider prose is never a limit."""
    if page.authority != "synthetic_fixture" or not page.text.startswith(
        "AEGIS SYNTHETIC MANUAL\n"
    ):
        return []
    if f"REVISION {page.revision}\n" not in page.text:
        return []
    constraints = []
    for index, line in enumerate(page.text.splitlines(), 1):
        match = ROW.fullmatch(line)
        if match:
            equipment, quantity, unit, minimum, maximum = match.groups()
            constraints.append(
                OEMConstraint.model_validate(
                    {
                        "equipment_id": equipment,
                        "quantity": quantity,
                        "unit": unit,
                        "minimum": float(minimum),
                        "maximum": float(maximum),
                        "citation": cite(page, line, index),
                    }
                )
            )
    return constraints


def extract_records(
    page: ManualPage,
) -> tuple[list[AlarmCode], list[Procedure], list[SafetyInterlock]]:
    alarms: list[AlarmCode] = []
    procedures: list[Procedure] = []
    interlocks: list[SafetyInterlock] = []
    if page.authority != "synthetic_fixture" or not page.text.startswith(
        "AEGIS SYNTHETIC MANUAL\n"
    ):
        return alarms, procedures, interlocks
    for line in page.text.splitlines():
        match = re.fullmatch(r"(ALARM|PROCEDURE|INTERLOCK) ([A-Z0-9-]+) (.+)", line)
        if match:
            prefix, identifier, description = match.groups()
            evidence = cite(page, line)
            if prefix == "ALARM":
                alarms.append(AlarmCode(code=identifier, meaning=description, citation=evidence))
            elif prefix == "PROCEDURE":
                procedures.append(
                    Procedure(procedure_id=identifier, description=description, citation=evidence)
                )
            else:
                interlocks.append(
                    SafetyInterlock(
                        interlock_id=identifier, description=description, citation=evidence
                    )
                )
    return alarms, procedures, interlocks


def decide(pages: list[ManualPage], equipment_id: str = "CELL-01") -> ManualDecision:
    constraints = [item for page in pages for item in extract_constraints(page)]
    flags = []
    seen: dict[tuple[str, str], OEMConstraint] = {}
    for constraint in constraints:
        key = (constraint.equipment_id, constraint.quantity)
        previous = seen.get(key)
        if previous and (previous.minimum, previous.maximum) != (
            constraint.minimum,
            constraint.maximum,
        ):
            flags.append(
                AmbiguityFlag(
                    reason="contradiction", citations=[previous.citation, constraint.citation]
                )
            )
        seen[key] = constraint
    if any(page.medium == "ocr_required" for page in pages):
        flags.append(AmbiguityFlag(reason="ocr_required", citations=[]))
    required = {"temperature", "pressure", "flow", "load"}
    if {quantity for equipment, quantity in seen if equipment == equipment_id} != required:
        flags.append(AmbiguityFlag(reason="missing_evidence", citations=[]))
    if any(
        page.authority != "synthetic_fixture"
        or f"REVISION {page.revision}\n" not in page.text
        or not page.text.startswith("AEGIS SYNTHETIC MANUAL\n")
        for page in pages
    ):
        flags.append(AmbiguityFlag(reason="untrusted_revision", citations=[]))
    return ManualDecision(
        status="no_action" if flags else "simulator_evidence_only",
        flags=flags[:100],
        checked_constraints=len(constraints),
    )
