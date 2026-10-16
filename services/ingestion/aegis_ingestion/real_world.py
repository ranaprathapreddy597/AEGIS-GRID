"""Source-grounded transformations. External references never become plant authority."""

import csv
import html
import io
import json
import re
import subprocess
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

import numpy as np

from aegis_ingestion.acquisition import AcquisitionBlocked
from aegis_ingestion.knowledge import EMBEDDING_ID, KnowledgeChunk, canonical, digest

REAL_NAMESPACE = "real-world-v1"
PIPELINE = "public-reference-v1"


def clean_text(text: str) -> str:
    # Never follow includes/links, render HTML, execute code blocks or load images.
    text = re.sub(r"(?s)^---\s*\n.*?\n---\s*\n", "", text)
    text = re.sub(r"(?s)<(?:script|style)\b.*?</(?:script|style)>", "", text, flags=re.I)
    result = []
    fence: str | None = None
    for line in text.splitlines():
        stripped = line.strip()
        marker = next((m for m in ("```", "~~~", "----", "....") if stripped.startswith(m)), None)
        if marker:
            fence = None if fence == marker else marker if fence is None else fence
            continue
        if fence or stripped.startswith(("include::", "image::", "image:", "[source,")):
            continue
        line = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", line)
        line = re.sub(r"<[^>]*>", " ", line)
        line = html.unescape(line)
        line = "".join(c for c in line if c in "\t" or ord(c) >= 32)
        result.append(re.sub(r"\s+", " ", line).strip())
    return "\n".join(result).strip()


def pdf_pages(path: Path, workspace: Path) -> list[dict[str, Any]]:
    # The only executed program is this repository's own worker. PDF bytes are mounted read-only.
    command = [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        "--read-only",
        "--memory",
        "256m",
        "--cpus",
        "1",
        "--pids-limit",
        "32",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges:true",
        "--volume",
        str(path.resolve()) + ":/input/document.pdf:ro",
        "--volume",
        str((workspace / "tools/extract_public_pdf.py").resolve()) + ":/worker.py:ro",
        "aegis-grid-qa:phase12",
        "python",
        "/worker.py",
    ]
    result = subprocess.run(command, capture_output=True, check=False, timeout=60)  # noqa: S603,S607 - fixed sandbox command
    if result.returncode or len(result.stdout) > 1_000_000:
        raise AcquisitionBlocked("Sandboxed PDF extraction refused")
    value = json.loads(result.stdout)
    pages = value["pages"]
    if not any("not subject to copyright" in p["text"] for p in pages):
        raise AcquisitionBlocked("NIST authorship/copyright disclaimer not found")
    return [p for p in pages if p["page"] not in {1, 2}]


def archive_arrays(path: Path) -> tuple[Any, Any, Any]:
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            parts = PurePosixPath(info.filename)
            if (
                parts.is_absolute()
                or ".." in parts.parts
                or parts.suffix != ".txt"
                or "\\" in info.filename
                or info.flag_bits & 1
                or (info.external_attr >> 16) & 0o170000 == 0o120000
                or info.file_size > 200_000_000
            ):
                raise AcquisitionBlocked("Unsafe archive member")
        arrays = []
        for name, size in [
            ("profile.txt", 1_000_000),
            ("TS1.txt", 10_000_000),
            ("FS1.txt", 20_000_000),
        ]:
            info = archive.getinfo(name)
            if info.file_size > size or info.file_size > max(1, info.compress_size) * 300:
                raise AcquisitionBlocked("Archive expansion exceeds bound")
            # Read only explicit numeric members. No filesystem extraction or script execution.
            arrays.append(np.loadtxt(io.BytesIO(archive.read(info)), dtype=np.float64))
    profile, temperature, flow = arrays
    if (
        profile.shape != (2205, 5)
        or temperature.shape != (2205, 60)
        or flow.shape != (2205, 600)
        or any(not np.isfinite(a).all() for a in arrays)
    ):
        raise AcquisitionBlocked("Unexpected hydraulic dataset shape/numbers")
    expected = [{3, 20, 100}, {73, 80, 90, 100}, {0, 1, 2}, {90, 100, 115, 130}, {0, 1}]
    if any(not set(profile[:, i]).issubset(values) for i, values in enumerate(expected)):
        raise AcquisitionBlocked("Unexpected hydraulic condition labels")
    return profile, temperature, flow


def hydraulic_sections(path: Path) -> list[tuple[str, str]]:
    profile, temperature, flow = archive_arrays(path)
    sections = []
    for cooler in (3, 20, 100):
        for pump in (0, 1, 2):
            rows = np.flatnonzero((profile[:, 0] == cooler) & (profile[:, 2] == pump))
            if not len(rows):
                continue
            t, f = temperature[rows], flow[rows]
            observation = {
                "cooler_condition_percent": cooler,
                "internal_pump_leakage_class": pump,
                "pump_labels": {0: "no leakage", 1: "weak leakage", 2: "severe leakage"}[pump],
                "cycles": len(rows),
                "cycle_duration_s": 60,
                "TS1_temperature_C": {
                    "mean": float(t.mean()),
                    "min": float(t.min()),
                    "max": float(t.max()),
                },
                "FS1_volume_flow_l_min": {
                    "mean": float(f.mean()),
                    "min": float(f.min()),
                    "max": float(f.max()),
                },
                "cycle_membership_sha256": digest(canonical((rows + 1).tolist()).encode()),
                "stable_cycles": int((profile[rows, 4] == 0).sum()),
            }
            text = (
                "Measured hydraulic test-rig cooler efficiency, pump internal leakage, "
                "temperature and flow. "
            )
            text += canonical(observation)
            text += (
                ". Aggregated across matching profile.txt cycles; "
                "valve and accumulator conditions vary. "
            )
            text += (
                "Descriptive measurements, not causal proof, "
                "operating limits or a recovery procedure."
            )
            sections.append(
                (f"profile.txt cooler={cooler},pump={pump}; TS1.txt/FS1.txt matching cycles", text)
            )
    return sections


def pump_sections(path: Path) -> list[tuple[str, str]]:
    raw = path.read_text("utf-8-sig")
    delimiter = ";" if raw.splitlines()[0].count(";") > raw.splitlines()[0].count(",") else ","
    reader = csv.DictReader(io.StringIO(raw), delimiter=delimiter)
    rows = list(reader)
    fields = reader.fieldnames or []
    if not 10 <= len(fields) <= 12 or not 20 <= len(rows) <= 200000:
        raise AcquisitionBlocked("Unexpected pump CSV schema/row count")
    timestamp = next((f for f in fields if f.lower() == "timestamp"), None)
    if timestamp is None:
        raise AcquisitionBlocked("Pump CSV has no timestamp")
    numeric = [f for f in fields if f != timestamp]
    # Empty cells remain explicitly missing. Never impute a measurement.
    values = np.asarray(
        [[float(row[f]) if row[f].strip() else np.nan for f in numeric] for row in rows],
        dtype=np.float64,
    )
    if np.isinf(values).any():
        raise AcquisitionBlocked("Infinite pump data")
    sections = []
    for indices in np.array_split(np.arange(len(rows)), 16):
        if not len(indices):
            continue
        first, last = int(indices[0]), int(indices[-1])
        selected = values[indices]
        stats = {}
        for i, field in enumerate(numeric):
            valid = selected[:, i][np.isfinite(selected[:, i])]
            stats[field] = {
                "mean": round(float(valid.mean()), 6) if len(valid) else None,
                "min": float(valid.min()) if len(valid) else None,
                "max": float(valid.max()) if len(valid) else None,
                "valid": len(valid),
                "missing": len(indices) - len(valid),
            }
        # Two small source-grounded records per window preserve all columns without long vectors.
        for start in range(0, len(numeric), 5):
            subset = {k: stats[k] for k in numeric[start : start + 5]}
            text = (
                "Measured CIRA heating-plant centrifugal pump A operational observations, "
                "2024-04-10. "
            )
            text += canonical(
                {
                    "rows": [first + 1, last + 1],
                    "samples": len(indices),
                    "start": rows[first][timestamp],
                    "end": rows[last][timestamp],
                    "measurements_raw_column_names": subset,
                }
            )
            text += (
                ". Motor/pump vibration, temperature or outlet-pressure readings "
                "as named by the source. "
            )
            text += "Units are not normalized; empty cells excluded with valid/missing counts. "
            text += "No fault label, causal diagnosis or operating limit inferred."
            sections.append(
                (f"CSV data rows {first + 1}-{last + 1}; columns {start + 1}-{start + 5}", text)
            )
    return sections


def process_sources(manifest: dict[str, Any], workspace: Path) -> list[KnowledgeChunk]:
    chunks: dict[str, KnowledgeChunk] = {}
    for source in manifest["accepted"]:
        path = Path(source["local_path"])
        if digest(path.read_bytes()) != source["sha256"]:
            raise AcquisitionBlocked("Original file integrity mismatch")
        if source["format"] == "zip":
            sections = hydraulic_sections(path)
        elif source["format"] == "csv":
            sections = pump_sections(path)
        elif source["format"] == "pdf":
            sections = [
                (f"PDF page {p['page']}", clean_text(p["text"])) for p in pdf_pages(path, workspace)
            ]
        else:
            sections = [("normalized documentation text", clean_text(path.read_text("utf-8")))]
        for location, text in sections:
            for start in range(0, len(text), 1040):
                content = text[start : start + 1200].strip()
                if len(content) < 80:
                    continue
                metadata = {
                    "tenant_id": "local",
                    "plant_id": "isolated-simulator",
                    "namespace_version": REAL_NAMESPACE,
                    "synthetic": False,
                    "authority": "external_reference_not_plant_authority",
                    "kind": "reference",
                    "source_id": source["source_id"],
                    "source": source["download_url"],
                    "source_url": source["landing_url"],
                    "source_sha256": source["sha256"],
                    "title": source["title"],
                    "revision": source["revision"],
                    "origin": source["origin"],
                    "location": location,
                    "section_sha256": digest(text.encode()),
                    "normalized_start": start,
                    "normalized_end": min(start + 1200, len(text)),
                    "text_sha256": digest(content.encode()),
                    "embedding": EMBEDDING_ID,
                    "pipeline": PIPELINE,
                    "license_id": source["license_id"],
                    "license_url": source["license_url"],
                    "license_evidence_sha256": source["license_evidence_sha256"],
                    "attribution": source["attribution"],
                    "processing_notice": source["processing_notice"],
                }
                identifier = "agrw1-" + digest(canonical(metadata).encode())
                chunks[identifier] = KnowledgeChunk(identifier, content, metadata)
    return [chunks[k] for k in sorted(chunks)]
