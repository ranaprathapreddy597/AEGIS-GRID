"""Versioned synthetic knowledge with native 256-D pretrained semantic embeddings."""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from huggingface_hub import snapshot_download
from model2vec import StaticModel

from aegis_ingestion.library import fixture_library

MODEL_ID = "minishlab/potion-base-8M"
MODEL_REVISION = "bf8b056651a2c21b8d2565580b8569da283cab23"
EMBEDDING_ID = MODEL_ID + "@" + MODEL_REVISION
PIPELINE = "synthetic-knowledge-v1"


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


class SemanticEmbedding:
    """Loads frozen upstream weights; never slices, pads, projects or randomizes vectors."""

    def __init__(self, *, local_only: bool = True) -> None:
        path = snapshot_download(
            MODEL_ID,
            revision=MODEL_REVISION,
            allow_patterns=["config.json", "model.safetensors", "tokenizer.json", "modules.json"],
            local_files_only=local_only,
        )
        self.artifacts = {
            name: digest((Path(path) / name).read_bytes())
            for name in ("config.json", "model.safetensors", "tokenizer.json")
        }
        self.model = StaticModel.from_pretrained(path, normalize=True, max_length=None)
        if self.model.dim != 256:
            raise ValueError("Embedding model is not natively 256 dimensional")

    def encode(self, texts: list[str]) -> Any:
        if not texts or len(texts) > 128 or any(not t.strip() or len(t) > 2000 for t in texts):
            raise ValueError("Embedding input exceeds bounds")
        vectors = np.asarray(self.model.encode(texts), dtype=np.float32)
        if (
            vectors.shape != (len(texts), 256)
            or not np.isfinite(vectors).all()
            or not np.allclose(np.linalg.norm(vectors, axis=1), 1, atol=1e-5)
        ):
            raise ValueError("Invalid semantic embedding")
        return vectors


@dataclass(frozen=True)
class KnowledgeChunk:
    identifier: str
    text: str
    metadata: dict[str, Any]


def build_corpus(root: Path) -> list[KnowledgeChunk]:
    """Fixed allowlist, deterministic source ordering/chunking, exact provenance and dedup."""
    rows: list[tuple[str, str, str, str, dict[str, Any]]] = []
    for page in fixture_library().pages:
        rows.append(
            (
                "manual",
                "data/manuals/pages.jsonl",
                page.source_sha256,
                page.text,
                {
                    "revision": page.revision,
                    "document_id": page.document_id,
                    "page": page.page,
                    "page_sha256": page.page_sha256,
                },
            )
        )
    for path in sorted((root / "data/scenarios").glob("scenario-*.json")):
        raw = path.read_bytes()
        rows.append(
            (
                "scenario",
                path.relative_to(root).as_posix(),
                digest(raw),
                canonical(json.loads(raw)),
                {"revision": digest(raw)},
            )
        )
    benchmark = root / "docs/results/phase12-benchmark-after-hardening.json"
    raw = benchmark.read_bytes()
    for row in json.loads(raw)["rows"]:
        rows.append(
            (
                "incident",
                benchmark.relative_to(root).as_posix(),
                digest(raw),
                "Synthetic incident observation and measured recovery: " + canonical(row),
                {"revision": digest(raw), "scenario_id": row["scenario_id"]},
            )
        )
    profile = root / "docs/results/phase8-profile.json"
    raw = profile.read_bytes()
    value = json.loads(raw)
    record = value["incident"]
    # Validated stored incident, no raw full-state snapshot in model evidence.
    from aegis_contracts.models import IncidentRecord
    from aegis_contracts.optimization import RecoveryAssessment

    incident = IncidentRecord.model_validate(record)
    assessment = RecoveryAssessment.model_validate(value["assessment"])
    observed = {
        "observed": incident.event.observed.model_dump() if incident.event.observed else None,
        "evidence": [e.model_dump() for e in incident.event.evidence],
    }
    rows.append(
        (
            "incident",
            profile.relative_to(root).as_posix(),
            digest(raw),
            "Validated synthetic incident: " + canonical(observed),
            {"revision": digest(raw), "incident_id": incident.incident_id},
        )
    )
    rows.append(
        (
            "recovery",
            profile.relative_to(root).as_posix(),
            digest(raw),
            "Validated synthetic minimax recovery evidence, not executable authority: "
            + assessment.model_dump_json(),
            {"revision": digest(raw), "artifact_sha256": assessment.artifact_sha256},
        )
    )
    chunks: dict[str, KnowledgeChunk] = {}
    for kind, source, source_hash, text, extra in rows:
        for offset in range(0, len(text), 1040):
            content = text[offset : offset + 1200]
            if not content.strip():
                continue
            metadata = {
                "tenant_id": "local",
                "plant_id": "isolated-simulator",
                "synthetic": True,
                "authority": "synthetic_fixture_not_oem",
                "kind": kind,
                "source": source,
                "source_sha256": source_hash,
                "chunk_start": offset,
                "chunk_end": offset + len(content),
                "text_sha256": digest(content.encode()),
                "embedding": EMBEDDING_ID,
                "pipeline": PIPELINE,
                **extra,
            }
            identifier = "agk1-" + digest(canonical(metadata).encode())
            chunks[identifier] = KnowledgeChunk(identifier, content, metadata)
    return [chunks[key] for key in sorted(chunks)]


def corpus_digest(chunks: list[KnowledgeChunk]) -> str:
    return digest(canonical([c.identifier for c in chunks]).encode())


def namespace(chunks: list[KnowledgeChunk]) -> str:
    return "aegis-synthetic-v1-" + corpus_digest(chunks)[:16]
