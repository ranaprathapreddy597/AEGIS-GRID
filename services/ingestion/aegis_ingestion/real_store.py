"""Append-only protocol for reviewed external references. No deletion or blind upsert."""

import asyncio
import json
import re
from typing import Any

import httpx
import numpy as np
from pydantic import SecretStr

from aegis_ingestion.evolus import ProviderUnavailable
from aegis_ingestion.knowledge import EMBEDDING_ID, KnowledgeChunk, SemanticEmbedding
from aegis_ingestion.real_world import REAL_NAMESPACE
from aegis_ingestion.semantic_store import SemanticStore


class RealWorldStore(SemanticStore):
    gate_label = "MI300X/Evolus BLOCKED; Pinecone real-world references verified"
    retrieval_method = "native256-dense-plus-source-routing-and-semantic-rerank-v1"

    def __init__(
        self,
        host: str,
        key: SecretStr,
        embedding: SemanticEmbedding,
        chunks: list[KnowledgeChunk],
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        super().__init__(host, key, embedding, chunks, transport)
        self.namespace = REAL_NAMESPACE
        self.uploaded: list[str] = []
        self.skipped: list[str] = []
        self.unconfirmed: list[str] = []

    async def request(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        if path not in {"/query", "/describe_index_stats"}:
            raise ProviderUnavailable("Only approved reads available")
        return await super().request(path, body)

    async def upsert(self) -> dict[str, Any]:
        raise ProviderUnavailable("Use append_new with existence checks")

    async def cleanup_test(self) -> None:
        raise ProviderUnavailable("Deletion unavailable for external references")

    def allowed_sources(self, kind: str | None) -> list[str]:
        if kind not in {None, "manual", "recovery", "reference"}:
            raise ValueError("Invalid external-reference role")
        return sorted(
            {
                c.metadata["source_id"]
                for c in self.chunks.values()
                if kind in (None, "reference")
                or (
                    kind == "manual"
                    and c.metadata["origin"]
                    in {"official_oem_documentation", "government_technical_reference"}
                )
                or (kind == "recovery" and c.metadata["origin"].startswith("measured_"))
            }
        )

    def search_scope(self, kind: str | None) -> dict[str, Any]:
        return {
            "tenant_id": {"$eq": "local"},
            "plant_id": {"$eq": "isolated-simulator"},
            "synthetic": {"$eq": False},
            "embedding": {"$eq": EMBEDDING_ID},
            "authority": {"$eq": "external_reference_not_plant_authority"},
            "source_id": {"$in": self.allowed_sources(kind)},
        }

    def matches_kind(self, chunk: KnowledgeChunk, kind: str | None) -> bool:
        return chunk.metadata["source_id"] in self.allowed_sources(kind)

    async def search(self, query: str, *, kind: str | None = None) -> list[KnowledgeChunk]:
        raw = await super().search(query, kind=kind)
        sources = self.allowed_sources(kind)
        if not sources:
            return []
        # Static token averaging can over-weight long numeric payloads. Route by
        # genuine semantic source descriptors, then rerank returned source-grounded text.
        descriptors = [
            next(
                c.metadata["title"] + " " + c.metadata["origin"].replace("_", " ")
                for c in self.chunks.values()
                if c.metadata["source_id"] == source
            )
            for source in sources
        ]
        vector = self.embedding.encode([query])[0]
        source_scores = self.embedding.encode(descriptors) @ vector
        order = np.argsort(-source_scores, kind="stable")[:2]
        selected = [sources[int(i)] for i in order]
        routed = []
        for source in selected:
            scope = self.search_scope(kind)
            scope["source_id"] = {"$eq": source}
            value = await self.request(
                "/query",
                {
                    "namespace": self.namespace,
                    "vector": vector.tolist(),
                    "topK": 3,
                    "includeMetadata": True,
                    "filter": scope,
                },
            )
            hits = self.validate_matches(value, kind)
            if any(c.metadata["source_id"] != source for c in hits):
                raise ProviderUnavailable("Source routing filter ignored")
            routed.extend(hits)
        candidates = {c.identifier: c for c in raw + routed}
        if not candidates:
            return []
        rows = list(candidates.values())
        # Strip numeric JSON only from the reranking view, never from stored evidence
        # or stored vectors. No record is rewritten to repair the pilot.
        views = [
            c.metadata["title"] + "\n" + re.sub(r"\{.*\}", " ", c.text, flags=re.S) for c in rows
        ]
        scores = self.embedding.encode(views) @ vector
        ranked = np.argsort(-scores, kind="stable")[:5]
        return [rows[int(i)] for i in ranked]

    @staticmethod
    async def bounded_body(response: httpx.Response) -> dict[str, Any]:
        if response.headers.get("content-encoding", "identity") != "identity":
            raise ProviderUnavailable("Unsupported response encoding")
        raw = bytearray()
        async for part in response.aiter_bytes(16384):
            raw.extend(part)
            if len(raw) > 1_048_576:
                raise ProviderUnavailable("Response exceeds bound")
        try:
            value = json.loads(raw)
        except ValueError:
            raise ProviderUnavailable("Invalid JSON response") from None
        if not isinstance(value, dict):
            raise ProviderUnavailable("Invalid response object")
        return value

    async def fetch(self, identifiers: list[str]) -> dict[str, Any]:
        if not 1 <= len(identifiers) <= 50 or any(i not in self.chunks for i in identifiers):
            raise ValueError("Fetch outside reviewed manifest")
        try:
            return await asyncio.wait_for(self._fetch(identifiers), timeout=35)
        except TimeoutError:
            raise ProviderUnavailable("Fetch total deadline exceeded") from None

    async def _fetch(self, identifiers: list[str]) -> dict[str, Any]:
        if self.blocked:
            raise ProviderUnavailable("Pinecone quota/auth circuit open")
        for attempt in range(3):
            try:
                async with self.client.stream(
                    "GET",
                    "/vectors/fetch",
                    params=[("namespace", self.namespace), *[("ids", i) for i in identifiers]],
                ) as response:
                    self.operations.append(
                        {
                            "operation": "/vectors/fetch",
                            "http_status": response.status_code,
                            "attempt": attempt + 1,
                            "namespace": self.namespace,
                        }
                    )
                    if response.status_code in {401, 403, 429}:
                        self.blocked = True
                        raise ProviderUnavailable("Pinecone auth/quota refused")
                    if response.status_code >= 500 and attempt < 2:
                        await asyncio.sleep(0.5 * (2**attempt))
                        continue
                    if response.status_code != 200:
                        raise ProviderUnavailable("Pinecone fetch refused")
                    value = await self.bounded_body(response)
                    records = value.get("vectors")
                    if not isinstance(records, dict) or not set(records).issubset(identifiers):
                        raise ProviderUnavailable("Invalid fetch response")
                    return records
            except httpx.HTTPError:
                if attempt == 2:
                    raise ProviderUnavailable("Pinecone fetch unavailable") from None
                await asyncio.sleep(0.5 * (2**attempt))
        raise ProviderUnavailable("Pinecone fetch unavailable")

    def verify_records(self, records: dict[str, Any]) -> None:
        for identifier, record in records.items():
            chunk = self.chunks.get(identifier)
            if chunk is None or not isinstance(record, dict):
                raise ProviderUnavailable("Unrecognized persisted record")
            if record.get("metadata") != {**chunk.metadata, "text": chunk.text}:
                raise ProviderUnavailable("Existing record differs; overwrite refused")
            raw = record.get("values")
            if not isinstance(raw, list) or any(type(v) not in (float, int) for v in raw):
                raise ProviderUnavailable("Persisted vector invalid")
            try:
                values = np.asarray(raw, dtype=np.float64)
            except (TypeError, ValueError):
                raise ProviderUnavailable("Persisted vector invalid") from None
            expected = self.embedding.encode([chunk.text])[0]
            if (
                values.shape != (256,)
                or not np.isfinite(values).all()
                or not np.allclose(values, expected, atol=1e-6, rtol=1e-5)
            ):
                raise ProviderUnavailable("Persisted embedding mismatch")

    async def append_new(self, chunks: list[KnowledgeChunk], *, maximum: int = 50) -> None:
        if (
            not 1 <= maximum <= 50
            or not 1 <= len(chunks) <= maximum
            or any(self.chunks.get(c.identifier) != c for c in chunks)
        ):
            raise ValueError("Append outside manifest/batch bound")
        existing = await self.fetch([c.identifier for c in chunks])
        self.verify_records(existing)
        self.skipped.extend(existing)
        pending = [c for c in chunks if c.identifier not in existing]
        if not pending:
            return
        if self.blocked:
            raise ProviderUnavailable("Pinecone quota/auth circuit open")
        values = self.embedding.encode([c.text for c in pending])
        body = {
            "namespace": self.namespace,
            "vectors": [
                {
                    "id": c.identifier,
                    "values": v.tolist(),
                    "metadata": {**c.metadata, "text": c.text},
                }
                for c, v in zip(pending, values, strict=True)
            ],
        }
        if len(json.dumps(body).encode()) > 1_900_000:
            raise ValueError("Append byte bound exceeded")
        try:
            await asyncio.wait_for(self._append_once(body), timeout=35)
        except (httpx.HTTPError, TimeoutError, ProviderUnavailable):
            # No write retry: a response may have been lost after persistence.
            self.unconfirmed.extend(c.identifier for c in pending)
            self.blocked = True
            raise ProviderUnavailable("Append unconfirmed; all further writes stopped") from None
        self.uploaded.extend(c.identifier for c in pending)

    async def _append_once(self, body: dict[str, Any]) -> None:
        async with self.client.stream("POST", "/vectors/upsert", json=body) as response:
            self.operations.append(
                {
                    "operation": "/vectors/upsert",
                    "http_status": response.status_code,
                    "namespace": self.namespace,
                    "count": len(body["vectors"]),
                    "attempt": 1,
                }
            )
            if response.status_code != 200:
                raise ProviderUnavailable("Append refused")
            value = await self.bounded_body(response)
            if value.get("upsertedCount") != len(body["vectors"]):
                raise ProviderUnavailable("Append acknowledgement mismatch")
