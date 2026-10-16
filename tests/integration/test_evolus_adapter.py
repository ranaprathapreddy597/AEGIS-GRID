"""Explicit HTTP contract doubles from supplied schemas, NOT provider recordings."""

import asyncio
from pathlib import Path

import httpx
import pytest
from aegis_ingestion.evolus import EvolusDocumentExtractor, ProviderUnavailable
from aegis_ingestion.library import fixture_library
from aegis_ingestion.pinecone import PineconeEvidenceReader
from aegis_ingestion.provider_pipeline import extract_existing
from pydantic import SecretStr

APP = "00000000-0000-0000-0000-000000000001"
MEMORY = "00000000-0000-0000-0000-000000000002"
DOCUMENT = "00000000-0000-0000-0000-000000000003"
KEY = SecretStr("contract-test-fixture-only")


def test_verified_headers_safe_routes_and_strict_provider_schema():
    async def run():
        calls = []

        def fake(request):
            calls.append(request)
            assert request.headers["X-ApiKey"] == KEY.get_secret_value()
            assert request.headers["X-Application-Id"] == APP
            assert "Authorization" not in request.headers
            assert request.method == "GET" and request.url.host == "api.evolus.ai"
            return httpx.Response(
                200,
                json={"extensions": [".pdf"], "maxFileSizeMb": 20, "maxFileSizeBytes": 20971520},
            )

        client = EvolusDocumentExtractor(KEY, APP, transport=httpx.MockTransport(fake))
        try:
            assert (await client.formats())["extensions"] == [".pdf"]
            with pytest.raises(ProviderUnavailable, match="personal user auth"):
                await client.memories()
            with pytest.raises(ValueError):
                await client.chunks("../admin", DOCUMENT)
            with pytest.raises(ValueError, match="Unverified"):
                await client._get("/api/v1/imaginary-extractor")
            assert len(calls) == 1
        finally:
            await client.close()

    asyncio.run(run())


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(200, json={"extensions": "pdf", "maxFileSizeMb": 10}),
        httpx.Response(200, json={"extensions": [], "commands": ["restart"]}),
        httpx.Response(302, headers={"Location": "https://attacker.invalid"}),
        httpx.Response(401, text="do not echo provider error or secrets"),
        httpx.Response(200, content=b"not-json"),
        httpx.Response(200, content=b"x" * (4 * 1024 * 1024 + 1)),
        httpx.Response(200, headers={"Content-Encoding": "br"}, content=b""),
    ],
)
def test_bad_or_unbounded_provider_response_is_sanitized(response):
    async def run():
        client = EvolusDocumentExtractor(
            KEY, APP, transport=httpx.MockTransport(lambda request: response)
        )
        try:
            with pytest.raises(ProviderUnavailable) as failure:
                await client.formats()
            assert KEY.get_secret_value() not in str(failure.value)
            assert "do not echo" not in str(failure.value)
        finally:
            await client.close()

    asyncio.run(run())


def test_bounded_read_retry_and_personal_user_auth():
    async def run():
        attempts = []

        def fake(request):
            attempts.append(1)
            assert request.headers["X-User-ApiKey"] == KEY.get_secret_value()
            return httpx.Response(503) if len(attempts) < 3 else httpx.Response(200, json=[])

        client = EvolusDocumentExtractor(
            KEY, APP, auth_kind="user", transport=httpx.MockTransport(fake)
        )
        try:
            assert await client.memories() == []
            assert len(attempts) == 3
        finally:
            await client.close()

    asyncio.run(run())


def test_existing_document_read_pipeline_maps_only_exact_source_citations(tmp_path):
    async def run():
        routes = []

        def fake(request):
            routes.append(request.url.path)
            assert request.method == "GET"
            if request.url.path.endswith("/download"):
                return httpx.Response(
                    200, content=Path("data/manuals/contradictory-bulletin.pdf").read_bytes()
                )
            assert request.url.path.endswith("/chunks")
            return httpx.Response(
                200,
                json=[
                    {"id": "fixture-1", "body": "LIMIT CELL-01 temperature degC 0 95"},
                    {"id": "fixture-2", "body": "invented dangerous limit"},
                ],
            )

        client = EvolusDocumentExtractor(KEY, APP, transport=httpx.MockTransport(fake))
        try:
            report = await extract_existing(client, MEMORY, DOCUMENT, tmp_path, "UNVERIFIED-R2")
            assert report["decision"] == "no_action"
            assert report["matched_chunks"] == report["unmapped_chunks"] == 1
            assert report["provider_confidence"] is None
            assert not report["provider_page_citations"]
            assert len(routes) == 2 and (tmp_path / "extraction.json").is_file()
        finally:
            await client.close()

    asyncio.run(run())


def test_pinecone_read_filters_and_rejects_foreign_citations():
    async def run():
        page = fixture_library().pages[0]

        def fake(request):
            import json

            body = json.loads(request.content)
            assert request.url.path == "/query"
            assert request.headers["X-Pinecone-Api-Version"] == "2025-10"
            assert body["namespace"] == "aegis-local-simulator"
            assert body["filter"]["tenant_id"] == {"$eq": "local"}
            return httpx.Response(
                200,
                json={
                    "matches": [
                        {
                            "id": page.page_sha256,
                            "score": 0.9,
                            "metadata": {
                                "tenant_id": "foreign",
                                "plant_id": "isolated-simulator",
                                "source_sha256": page.source_sha256,
                                "revision": page.revision,
                            },
                        }
                    ]
                },
            )

        client = PineconeEvidenceReader(
            "test.svc.region.pinecone.io", KEY, transport=httpx.MockTransport(fake)
        )
        try:
            with pytest.raises(ProviderUnavailable, match="scope"):
                await client.query("temperature", [page])
        finally:
            await client.close()

    asyncio.run(run())
