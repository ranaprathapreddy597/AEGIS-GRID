"""Read-only, pinned dual-namespace retrieval for the isolated simulator."""

import json
from pathlib import Path
from typing import Any

import httpx
from pydantic import SecretStr

from aegis_ingestion.evolus import ProviderUnavailable
from aegis_ingestion.knowledge import (
    EMBEDDING_ID,
    KnowledgeChunk,
    SemanticEmbedding,
    canonical,
    digest,
)
from aegis_ingestion.real_store import RealWorldStore
from aegis_ingestion.semantic_store import SemanticStore

SYNTHETIC_NAMESPACE = "aegis-synthetic-v1-6e4d75051cbcaf1e"
REAL_NAMESPACE = "real-world-v1"


class HostedReferenceReader(RealWorldStore):
    async def append_new(self, chunks: list[KnowledgeChunk], *, maximum: int = 50) -> None:
        raise ProviderUnavailable("Hosted ingestion disabled")


class DualKnowledgeStore(SemanticStore):
    gate_label = "MI300X/Evolus BLOCKED; Pinecone dual references verified"

    def __init__(
        self,
        host: str,
        key: SecretStr,
        embedding: SemanticEmbedding,
        directory: Path,
        manifest: Path = Path("data/cloud-knowledge-manifest.json"),
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        pins = json.loads(manifest.read_bytes())
        corpora: dict[str, list[KnowledgeChunk]] = {}
        for ns, count, filename in (
            (SYNTHETIC_NAMESPACE, 1235, "synthetic.jsonl"),
            (REAL_NAMESPACE, 103, "real-world.jsonl"),
        ):
            raw = (directory / filename).read_bytes()
            pin = pins[ns]
            if pin != {"file": filename, "count": count, "sha256": digest(raw)}:
                raise ValueError("Cloud knowledge integrity pin mismatch")
            rows = [json.loads(line) for line in raw.splitlines()]
            chunks = [KnowledgeChunk(row["id"], row["text"], row["metadata"]) for row in rows]
            if len(chunks) != count or len({c.identifier for c in chunks}) != count:
                raise ValueError("Cloud knowledge count mismatch")
            for chunk in chunks:
                m = chunk.metadata
                if (
                    m.get("tenant_id") != "local"
                    or m.get("plant_id") != "isolated-simulator"
                    or m.get("synthetic") is not (ns == SYNTHETIC_NAMESPACE)
                    or (ns == REAL_NAMESPACE and not m.get("license_id"))
                    or m.get("embedding") != EMBEDDING_ID
                    or m.get("text_sha256") != digest(chunk.text.encode())
                    or chunk.identifier
                    != ("agk1-" if ns == SYNTHETIC_NAMESPACE else "agrw1-")
                    + digest(canonical(m).encode())
                ):
                    raise ValueError("Cloud knowledge scope/license mismatch")
            corpora[ns] = chunks
        expected_artifacts = json.loads(
            (manifest.parent / "cloud-embedding-manifest.json").read_bytes()
        )
        if embedding.artifacts != expected_artifacts:
            raise ValueError("Embedding artifact integrity mismatch")
        super().__init__(host, key, embedding, corpora[SYNTHETIC_NAMESPACE], transport)
        if self.namespace != SYNTHETIC_NAMESPACE:
            raise ValueError("Synthetic namespace pin mismatch")
        self.external = HostedReferenceReader(
            host, key, embedding, corpora[REAL_NAMESPACE], transport
        )
        self.chunks.update(self.external.chunks)
        self.searches = 0

    async def request(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        if path not in {"/query", "/describe_index_stats"}:
            raise ProviderUnavailable("Hosted application permits Pinecone reads only")
        return await super().request(path, body)

    async def upsert(self) -> dict[str, Any]:
        raise ProviderUnavailable("Hosted ingestion disabled")

    async def cleanup_test(self) -> None:
        raise ProviderUnavailable("Hosted deletion disabled")

    def matches_kind(self, chunk: KnowledgeChunk, kind: str | None) -> bool:
        return chunk.metadata.get("synthetic") is True and super().matches_kind(chunk, kind)

    async def close(self) -> None:
        await super().close()
        await self.external.close()

    async def search(self, query: str, *, kind: str | None = None) -> list[KnowledgeChunk]:
        if self.searches >= 12 or self.blocked or self.external.blocked:
            raise ProviderUnavailable("Hosted retrieval session quota/circuit open")
        self.searches += 1
        synthetic = await super().search(query, kind=kind)
        external = await self.external.search(query, kind=kind)
        # No external manual is mapped to this fictional plant. Keep contextual references
        # visible, but never rank unrelated OEM hardware as plant-specific authority.
        return [*synthetic[:2], *external[:2]]

    def citation(self, chunk: KnowledgeChunk) -> dict[str, Any]:
        m = chunk.metadata
        synthetic = m["synthetic"]
        return {
            "reference_id": chunk.identifier,
            "namespace": SYNTHETIC_NAMESPACE if synthetic else REAL_NAMESPACE,
            "title": str(m.get("title", m.get("source_id", m["source"]))),
            "source": str(m["source"]),
            "revision": str(m["revision"]),
            "source_sha256": str(m["source_sha256"]),
            "license": "repository synthetic fixture" if synthetic else str(m["license_id"]),
            "attribution": str(m.get("attribution", "AEGIS GRID synthetic simulator")),
            "synthetic": synthetic,
            "applicability": "synthetic_simulator_evidence"
            if synthetic
            else "external_context_only",
            "tenant_id": "local",
            "plant_id": "isolated-simulator",
        }
