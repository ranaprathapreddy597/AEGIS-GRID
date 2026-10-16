"""Read-only Evolus adapter derived from the user-supplied OpenAPI 3.0.4 file."""

import asyncio
import json
from pathlib import Path
from typing import Any
from uuid import UUID

import httpx
from jsonschema import Draft4Validator
from pydantic import SecretStr


class ProviderUnavailable(RuntimeError):
    pass


def _nullable(value: Any) -> Any:
    """Translate OpenAPI 3.0 nullable to Draft4 without changing provider fields."""
    if isinstance(value, list):
        return [_nullable(item) for item in value]
    if not isinstance(value, dict):
        return value
    result = {k: _nullable(v) for k, v in value.items() if k != "nullable"}
    if value.get("nullable"):
        return {"anyOf": [result, {"type": "null"}]}
    return result


class EvolusDocumentExtractor:
    """Existing memory documents only. No implicit upload, billing, retry or reindex write."""

    def __init__(
        self,
        api_key: SecretStr,
        application_id: str,
        *,
        auth_kind: str = "application",
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.application_id = str(UUID(application_id))
        if auth_kind not in {"application", "user"}:
            raise ValueError("Unknown provider auth scheme")
        self.auth_kind = auth_kind
        self.contract = _nullable(
            json.loads(Path(__file__).with_name("evolus-read-contract.json").read_text("utf-8"))
        )
        self.client = httpx.AsyncClient(
            base_url="https://api.evolus.ai",
            headers={
                "X-ApiKey"
                if auth_kind == "application"
                else "X-User-ApiKey": api_key.get_secret_value(),
                "X-Application-Id": self.application_id,
                "Accept": "application/json",
                "Accept-Encoding": "identity",
            },
            timeout=httpx.Timeout(15, connect=5),
            follow_redirects=False,
            trust_env=False,
            transport=transport,
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def _get(
        self, template: str, parameters: dict[str, str] | None = None, *, binary: bool = False
    ) -> Any:
        if template not in self.contract["paths"]:
            raise ValueError("Unverified provider route")
        path = template
        for key, value in (parameters or {}).items():
            path = path.replace("{" + key + "}", str(UUID(value)))
        # Bounded retry for safe reads only. Never log exception URLs, headers or bodies.
        for attempt in range(3):
            try:
                async with self.client.stream("GET", path) as response:
                    if response.status_code in {429, 502, 503, 504} and attempt < 2:
                        await asyncio.sleep(0.1 * 2**attempt)
                        continue
                    if response.status_code != 200:
                        raise ProviderUnavailable(
                            f"Evolus read refused (HTTP {response.status_code})"
                        )
                    if response.headers.get("content-encoding", "identity") != "identity":
                        raise ProviderUnavailable("Unexpected provider content encoding")
                    limit = 32 * 1024 * 1024 if binary else 4 * 1024 * 1024
                    data = bytearray()
                    async for chunk in response.aiter_bytes(chunk_size=65536):
                        data.extend(chunk)
                        if len(data) > limit:
                            raise ProviderUnavailable("Provider response exceeds local bound")
                    if binary:
                        return bytes(data)
                    try:
                        payload = json.loads(data)
                        schema = self.contract["paths"][template]["get"]["responses"]["200"][
                            "content"
                        ]["application/json"]["schema"]
                        validator = Draft4Validator(
                            {**schema, "components": self.contract["components"]}
                        )
                        if not validator.is_valid(payload):
                            raise ProviderUnavailable(
                                "Provider response violates supplied contract"
                            )
                        return payload
                    except (ValueError, KeyError, RecursionError):
                        raise ProviderUnavailable("Invalid provider response") from None
            except httpx.HTTPError:
                if attempt == 2:
                    raise ProviderUnavailable("Evolus transport unavailable") from None
                await asyncio.sleep(0.1 * 2**attempt)
        raise ProviderUnavailable("Read retry budget exhausted")

    async def formats(self) -> Any:
        result = await self._get("/api/v1/memories/document-formats")
        if (
            not isinstance(result.get("extensions"), list)
            or not result["extensions"]
            or (type(result.get("maxFileSizeBytes")) is not int or result["maxFileSizeBytes"] <= 0)
        ):
            raise ProviderUnavailable("Provider did not supply usable document limits")
        return result

    async def memories(self) -> Any:
        if self.auth_kind != "user":
            raise ProviderUnavailable("Memory discovery requires documented personal user auth")
        return await self._get("/api/v1/memories")

    async def documents(self, memory_id: str) -> Any:
        return await self._get("/api/v1/memories/{memoryId}/documents", {"memoryId": memory_id})

    async def chunks(self, memory_id: str, document_id: str) -> Any:
        return await self._get(
            "/api/v1/memories/{memoryId}/documents/{documentId}/chunks",
            {"memoryId": memory_id, "documentId": document_id},
        )

    async def download(self, memory_id: str, document_id: str) -> bytes:
        result: bytes = await self._get(
            "/api/v1/memories/{memoryId}/documents/{documentId}/download",
            {"memoryId": memory_id, "documentId": document_id},
            binary=True,
        )
        return result
