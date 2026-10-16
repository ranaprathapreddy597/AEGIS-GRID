"""Verified Pinecone 2025-10 read adapter and local indexing request preparation."""

import json
import math
import re
from typing import Any

import httpx
from aegis_contracts.manuals import ManualPage
from pydantic import SecretStr

from aegis_ingestion.evolus import ProviderUnavailable
from aegis_ingestion.retrieval import embed


def indexing_batches(pages: list[ManualPage]) -> list[dict[str, Any]]:
    """Prepare bounded upsert payloads locally. Sending a write requires a later gate."""
    vectors = [
        {
            "id": page.page_sha256,
            "values": embed(page.text).tolist(),
            "metadata": {
                "tenant_id": "local",
                "plant_id": "isolated-simulator",
                "source_sha256": page.source_sha256,
                "revision": page.revision,
            },
        }
        for page in pages
    ]
    return [
        {"namespace": "aegis-local-simulator", "vectors": vectors[i : i + 50]}
        for i in range(0, len(vectors), 50)
    ]


class PineconeEvidenceReader:
    def __init__(
        self, host: str, key: SecretStr, transport: httpx.AsyncBaseTransport | None = None
    ) -> None:
        if not re.fullmatch(r"[a-z0-9][a-z0-9.-]{1,200}\.svc\.[a-z0-9.-]*pinecone\.io", host):
            raise ValueError("Expected a provisioned Pinecone index host")
        self.client = httpx.AsyncClient(
            base_url="https://" + host,
            headers={
                "Api-Key": key.get_secret_value(),
                "X-Pinecone-Api-Version": "2025-10",
                "Accept-Encoding": "identity",
            },
            timeout=10,
            trust_env=False,
            follow_redirects=False,
            limits=httpx.Limits(max_keepalive_connections=0, max_connections=1),
            transport=transport,
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def query(self, text: str, pages: list[ManualPage]) -> list[tuple[str, float]]:
        if not text.strip() or len(text) > 500 or not pages:
            raise ValueError("Invalid evidence query")
        body = {
            "namespace": "aegis-local-simulator",
            "vector": embed(text).tolist(),
            "topK": 5,
            "includeMetadata": True,
            "filter": {
                "tenant_id": {"$eq": "local"},
                "plant_id": {"$eq": "isolated-simulator"},
                "source_sha256": {"$in": sorted({p.source_sha256 for p in pages})},
            },
        }
        try:
            async with self.client.stream("POST", "/query", json=body) as response:
                if (
                    response.status_code != 200
                    or response.headers.get("content-encoding", "identity") != "identity"
                ):
                    raise ProviderUnavailable("Pinecone read unavailable")
                data = bytearray()
                async for chunk in response.aiter_bytes(chunk_size=65536):
                    data.extend(chunk)
                    if len(data) > 1024 * 1024:
                        raise ProviderUnavailable("Pinecone response exceeds bound")
                payload = json.loads(data)
        except (httpx.HTTPError, ValueError):
            raise ProviderUnavailable("Pinecone read unavailable") from None
        known = {p.page_sha256: p for p in pages}
        result = []
        if not isinstance(payload, dict):
            raise ProviderUnavailable("Invalid Pinecone result")
        matches = payload.get("matches")
        if not isinstance(matches, list) or len(matches) > 5:
            raise ProviderUnavailable("Invalid Pinecone result")
        for match in matches:
            if not isinstance(match, dict):
                raise ProviderUnavailable("Invalid Pinecone match")
            identifier = match.get("id")
            page = known.get(identifier) if isinstance(identifier, str) else None
            metadata = match.get("metadata", {})
            score = match.get("score")
            if (
                page is None
                or not isinstance(metadata, dict)
                or metadata.get("tenant_id") != "local"
                or metadata.get("plant_id") != "isolated-simulator"
                or metadata.get("source_sha256") != page.source_sha256
                or metadata.get("revision") != page.revision
                or not isinstance(score, (int, float))
                or isinstance(score, bool)
                or not math.isfinite(score)
            ):
                raise ProviderUnavailable("Unverifiable Pinecone citation or scope")
            result.append((page.page_sha256, float(score)))
        return result
