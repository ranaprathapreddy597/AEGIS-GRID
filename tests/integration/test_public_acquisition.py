"""Explicit offline doubles for public acquisition and append-only Pinecone boundaries."""

import asyncio
import csv
import io
import json
import zipfile
from pathlib import Path

import httpx
import pytest
from aegis_ingestion.acquisition import (
    MAX_TOTAL,
    AcquisitionBlocked,
    PublicAcquirer,
    public_url,
)
from aegis_ingestion.evolus import ProviderUnavailable
from aegis_ingestion.knowledge import KnowledgeChunk
from aegis_ingestion.real_store import RealWorldStore
from aegis_ingestion.real_world import archive_arrays, clean_text, pump_sections
from pydantic import SecretStr
from test_semantic_knowledge import EmbeddingDouble


@pytest.mark.parametrize(
    "url",
    [
        "http://zenodo.org/a",
        "https://127.0.0.1/a",
        "https://u:p@zenodo.org/a",
        "https://evil.com/a",
        "https://zenodo.org:99/a",
    ],
)
def test_public_origin_allowlist(url):
    with pytest.raises(AcquisitionBlocked):
        public_url(url)


@pytest.mark.parametrize("status", [401, 403, 429])
def test_public_auth_quota_stops_all_following_downloads(tmp_path, status):
    async def run():
        calls = []

        def handler(request):
            calls.append(request)
            assert "authorization" not in request.headers
            return httpx.Response(status)

        client = PublicAcquirer(tmp_path, httpx.MockTransport(handler))
        try:
            for name in ["first.csv", "second.csv"]:
                with pytest.raises(AcquisitionBlocked):
                    await client.download("https://zenodo.org/data", name)
            assert len(calls) == 1 and client.stopped
        finally:
            await client.close()

    asyncio.run(run())


def test_file_total_limits_and_redirects_do_not_bypass_policy(tmp_path):
    async def run():
        for mode in ("file", "total", "redirect"):

            def handler(request, mode=mode):
                if mode == "redirect":
                    return httpx.Response(302, headers={"location": "https://evil.com/payload"})
                return httpx.Response(200, content=b"12345")

            client = PublicAcquirer(tmp_path / mode, httpx.MockTransport(handler))
            if mode == "total":
                client.ledger["network_bytes"] = MAX_TOTAL - 1
            try:
                with pytest.raises(AcquisitionBlocked):
                    await client.download(
                        "https://zenodo.org/data", "data.csv", maximum=4 if mode == "file" else 100
                    )
                assert not (tmp_path / mode / "data.csv").exists()
            finally:
                await client.close()

    asyncio.run(run())


def chunk():
    return KnowledgeChunk(
        "agrw1-test",
        "untrusted measured pump reference",
        {
            "source_id": "measured",
            "origin": "measured_test_rig",
            "synthetic": False,
            "kind": "reference",
            "authority": "external_reference_not_plant_authority",
        },
    )


def store(handler):
    return RealWorldStore(
        "test.svc.pinecone.io",
        SecretStr("http-double-only"),
        EmbeddingDouble(),
        [chunk()],
        httpx.MockTransport(handler),
    )


@pytest.mark.parametrize("mismatch", [False, True])
def test_existing_records_are_never_overwritten(mismatch):
    async def run():
        calls = []
        c = chunk()

        def handler(request):
            calls.append(request.method)
            assert request.method == "GET"
            metadata = {**c.metadata, "text": "changed" if mismatch else c.text}
            return httpx.Response(
                200,
                json={
                    "vectors": {c.identifier: {"metadata": metadata, "values": [1.0] + [0.0] * 255}}
                },
            )

        client = store(handler)
        try:
            if mismatch:
                with pytest.raises(ProviderUnavailable, match="overwrite refused"):
                    await client.append_new([c])
            else:
                await client.append_new([c])
                assert client.skipped == [c.identifier] and client.uploaded == []
            assert calls == ["GET"]
            with pytest.raises(ProviderUnavailable):
                await client.upsert()
            with pytest.raises(ProviderUnavailable):
                await client.cleanup_test()
        finally:
            await client.close()

    asyncio.run(run())


@pytest.mark.parametrize("status", [200, 401, 403, 429, 500])
def test_append_is_single_attempt_and_stops_on_any_unconfirmed_write(status):
    async def run():
        calls = []

        def handler(request):
            calls.append(request.method)
            if request.method == "GET":
                assert request.url.params["namespace"] == "real-world-v1"
                return httpx.Response(200, json={"vectors": {}})
            value = json.loads(request.content)
            assert value["namespace"] == "real-world-v1" and len(value["vectors"]) == 1
            return httpx.Response(status, json={"upsertedCount": 1})

        client = store(handler)
        try:
            if status == 200:
                await client.append_new([chunk()], maximum=20)
                assert client.uploaded == [chunk().identifier]
            else:
                with pytest.raises(ProviderUnavailable):
                    await client.append_new([chunk()], maximum=20)
                with pytest.raises(ProviderUnavailable):
                    await client.append_new([chunk()], maximum=20)
                assert client.unconfirmed == [chunk().identifier]
            assert calls == ["GET", "POST"]
        finally:
            await client.close()

    asyncio.run(run())


def test_code_blocks_and_unsafe_archives_are_not_processed(tmp_path):
    text = "Useful\n```sh\nexecute EVIL\n```\n<script>BAD()</script>\ninclude::remote[]\nEvidence"
    assert clean_text(text) == "Useful\n\nEvidence"
    path = tmp_path / "bad.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("../run.py", "malicious()")
    with pytest.raises(AcquisitionBlocked, match="Unsafe archive"):
        archive_arrays(path)


def test_missing_measurements_are_counted_and_never_imputed(tmp_path):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Timestamp", *[f"signal{i}" for i in range(10)]])
    for _ in range(20):
        writer.writerow(["2024-04-10T12:00:00Z", "", *([2.0] * 9)])
    path = tmp_path / "data.csv"
    path.write_text(buffer.getvalue(), encoding="utf-8")
    result = pump_sections(path)
    assert any('"missing":2' in text and '"mean":null' in text for _, text in result)
    assert all("operating limit" in text for _, text in result)


def test_failed_bulk_run_reports_blocked_and_releases_local_lock(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(Path("tools").resolve()))
    import acquire_real_world as pipeline

    work = tmp_path / "work"
    work.mkdir()
    (tmp_path / "docs/results").mkdir(parents=True)
    raw = work / "pump.csv"
    raw.write_text("Timestamp,value\n2024-04-10,1\n", encoding="utf-8")
    (work / "source-manifest.json").write_text(
        json.dumps({"accepted": [{"source_id": "zenodo-cira-pump", "local_path": str(raw)}]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(pipeline, "ROOT", tmp_path)
    monkeypatch.setattr(pipeline, "WORK", work)
    monkeypatch.setattr(pipeline, "verified_chunks", lambda manifest: [])

    async def failed_upload(manifest, chunks, report):
        report["status"] = "PILOT_VERIFIED_BULK_RUNNING"
        raise AcquisitionBlocked("Controlled post-pilot failure")

    monkeypatch.setattr(pipeline, "upload", failed_upload)
    monkeypatch.setattr("sys.argv", ["acquire_real_world.py", "upload"])
    pipeline.main()
    report = json.loads((tmp_path / "docs/results/real-world-ingestion.json").read_bytes())
    assert report["status"] == "BLOCKED"
    assert report["blocker"] == "Controlled post-pilot failure"
    assert not (work / "pipeline.lock").exists()
