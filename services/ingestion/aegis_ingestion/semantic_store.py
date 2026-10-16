"""Scoped Pinecone semantic operations; no production/plant mutation authority."""

import asyncio
import json
import math
import re
import time
from typing import Any

import httpx
from pydantic import SecretStr

from aegis_ingestion.evolus import ProviderUnavailable
from aegis_ingestion.knowledge import (
    EMBEDDING_ID,
    KnowledgeChunk,
    SemanticEmbedding,
    namespace,
)
from aegis_ingestion.pinecone import PineconeEvidenceReader


class SemanticStore(PineconeEvidenceReader):
    def __init__(
        self,
        host: str,
        key: SecretStr,
        embedding: SemanticEmbedding,
        chunks: list[KnowledgeChunk],
        transport: httpx.AsyncBaseTransport | None = None,
        *,
        test_namespace: str | None = None,
    ) -> None:
        super().__init__(host, key, transport)
        self.embedding = embedding
        self.chunks = {c.identifier: c for c in chunks}
        self.namespace = test_namespace or namespace(chunks)
        self._cleanup_namespace = test_namespace
        if test_namespace and not re.fullmatch(
            r"aegis-integration-test-[0-9a-f]{32}", test_namespace
        ):
            raise ValueError("Invalid isolated test namespace")
        self.operations: list[dict[str, Any]] = []
        self.blocked = False

    async def request(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        try:
            return await asyncio.wait_for(self._request(path, body), timeout=35)
        except TimeoutError:
            raise ProviderUnavailable("Pinecone total operation deadline exceeded") from None

    async def _request(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        if self.blocked:
            raise ProviderUnavailable("Pinecone quota/auth circuit open")
        started = time.perf_counter()
        for attempt in range(3):
            try:
                async with self.client.stream("POST", path, json=body) as response:
                    self.operations.append(
                        {
                            "operation": path,
                            "http_status": response.status_code,
                            "attempt": attempt + 1,
                            "namespace": self.namespace,
                            "elapsed_ms": (time.perf_counter() - started) * 1000,
                        }
                    )
                    if response.status_code in {401, 403, 429}:
                        self.blocked = True
                        raise ProviderUnavailable("Pinecone auth/quota refused")
                    if response.status_code >= 500 and attempt < 2:
                        await asyncio.sleep(0.5 * (2**attempt))
                        continue
                    if response.status_code != 200:
                        raise ProviderUnavailable("Pinecone operation refused")
                    if response.headers.get("content-encoding", "identity") != "identity":
                        raise ProviderUnavailable("Pinecone encoding refused")
                    raw = bytearray()
                    async for part in response.aiter_bytes(16384):
                        raw.extend(part)
                        if len(raw) > 1048576:
                            raise ProviderUnavailable("Pinecone response exceeds bound")
                    value = json.loads(raw)
                    if not isinstance(value, dict):
                        raise ProviderUnavailable("Invalid Pinecone response")
                    return value
            except (httpx.HTTPError, ValueError):
                # Ambiguous writes are repeatable only through identical versioned IDs.
                if attempt == 2:
                    raise ProviderUnavailable("Pinecone transport/response unavailable") from None
                await asyncio.sleep(0.5 * (2**attempt))
        raise ProviderUnavailable("Pinecone operation unavailable")

    async def count(self) -> int:
        value = await self.request("/describe_index_stats", {})
        if value.get("dimension") != 256:
            raise ProviderUnavailable("Pinecone dimension mismatch")
        count = value.get("namespaces", {}).get(self.namespace, {}).get("vectorCount", 0)
        if type(count) is not int or count < 0:
            raise ProviderUnavailable("Invalid Pinecone count")
        return count

    async def upsert(self) -> dict[str, Any]:
        uploaded = 0
        failed: list[str] = []
        receipts = []
        chunks = list(self.chunks.values())
        for offset in range(0, len(chunks), 50):
            batch = chunks[offset : offset + 50]
            vectors = self.embedding.encode([c.text for c in batch])
            body = {
                "namespace": self.namespace,
                "vectors": [
                    {
                        "id": c.identifier,
                        "values": vector.tolist(),
                        "metadata": {**c.metadata, "text": c.text},
                    }
                    for c, vector in zip(batch, vectors, strict=True)
                ],
            }
            if len(json.dumps(body).encode()) > 1900000:
                raise ValueError("Pinecone batch exceeds byte bound")
            try:
                result = await self.request("/vectors/upsert", body)
                if result.get("upsertedCount") != len(batch):
                    raise ProviderUnavailable("Pinecone batch acknowledgement mismatch")
                uploaded += len(batch)
                receipts.append({"offset": offset, "acknowledged": len(batch)})
            except ProviderUnavailable:
                failed.extend(c.identifier for c in batch)
                # Stop promptly: unattempted records are also explicitly reported.
                failed.extend(c.identifier for c in chunks[offset + len(batch) :])
                break
        return {
            "acknowledged_vectors": uploaded,
            "failed_or_unconfirmed_ids": failed,
            "batches": receipts,
        }

    async def search(self, query: str, *, kind: str | None = None) -> list[KnowledgeChunk]:
        if not query.strip() or len(query) > 500:
            raise ValueError("Query exceeds bound")
        scope: dict[str, Any] = {
            "tenant_id": {"$eq": "local"},
            "plant_id": {"$eq": "isolated-simulator"},
            "synthetic": {"$eq": True},
            "embedding": {"$eq": EMBEDDING_ID},
        }
        if kind:
            if kind not in {"manual", "scenario", "incident", "recovery"}:
                raise ValueError("Invalid knowledge kind")
            scope["kind"] = {"$eq": kind}
        value = await self.request(
            "/query",
            {
                "namespace": self.namespace,
                "vector": self.embedding.encode([query])[0].tolist(),
                "topK": 5,
                "includeMetadata": True,
                "filter": scope,
            },
        )
        matches = value.get("matches")
        if not isinstance(matches, list) or len(matches) > 5:
            raise ProviderUnavailable("Invalid Pinecone matches")
        hits = []
        for match in matches:
            if not isinstance(match, dict):
                raise ProviderUnavailable("Invalid Pinecone match")
            identifier = match.get("id")
            chunk = self.chunks.get(identifier) if isinstance(identifier, str) else None
            score = match.get("score")
            if (
                chunk is None
                or match.get("metadata") != {**chunk.metadata, "text": chunk.text}
                or (kind and chunk.metadata["kind"] != kind)
                or not isinstance(score, (float, int))
                or isinstance(score, bool)
                or not math.isfinite(score)
                or not -1.001 <= score <= 1.001
            ):
                raise ProviderUnavailable("Unverifiable semantic source or scope")
            hits.append(chunk)
        return hits

    async def cleanup_test(self) -> None:
        if self._cleanup_namespace is None or self.namespace != self._cleanup_namespace:
            raise ValueError("Only isolated test namespaces can be cleaned")
        await self.request("/vectors/delete", {"namespace": self.namespace, "deleteAll": True})
