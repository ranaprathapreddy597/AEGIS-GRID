"""Bounded public acquisition. The reviewed registry is data, never executable input."""

import asyncio
import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urljoin, urlsplit

import httpx
from aegis_contracts.models import Contract
from pydantic import Field

from aegis_ingestion.knowledge import digest

MAX_FILE = 200_000_000
MAX_TOTAL = 1_000_000_000
PUBLIC_HOSTS = {
    "raw.githubusercontent.com",
    "archive.ics.uci.edu",
    "zenodo.org",
    "www.nist.gov",
    "nvlpubs.nist.gov",
    "www.raspberrypi.com",
}


class AcquisitionBlocked(RuntimeError):
    pass


class Source(Contract):
    source_id: str = Field(pattern=r"^[a-z0-9-]{1,60}$")
    title: str
    attribution: str
    landing_url: str
    download_url: str
    license_id: str
    license_url: str
    license_evidence_url: str
    license_marker: str
    revision: str
    format: Literal["zip", "csv", "pdf", "adoc", "md"]
    origin: str
    expected_md5: str | None = None
    expected_bytes: int | None = None


def public_url(url: str) -> str:
    value = urlsplit(url)
    if (
        value.scheme != "https"
        or value.hostname not in PUBLIC_HOSTS
        or value.username
        or value.password
        or value.port not in (None, 443)
        or value.fragment
    ):
        raise AcquisitionBlocked("Unreviewed public origin")
    return url


def atomic_json(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


class PublicAcquirer:
    """One request at a time; byte budget includes response bodies from failed attempts."""

    def __init__(self, root: Path, transport: httpx.AsyncBaseTransport | None = None) -> None:
        root.mkdir(parents=True, exist_ok=True)
        self.root = root
        self.ledger_path = root / "download-ledger.json"
        self.ledger: dict[str, Any] = (
            json.loads(self.ledger_path.read_bytes())
            if self.ledger_path.exists()
            else {"network_bytes": 0, "files": {}}
        )
        self.stopped = False
        self.operations: list[dict[str, Any]] = []
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30, connect=10),
            trust_env=False,
            follow_redirects=False,
            headers={"User-Agent": "AEGIS-GRID-public-research/1.0", "Accept-Encoding": "identity"},
            limits=httpx.Limits(max_connections=1, max_keepalive_connections=0),
            transport=transport,
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def download(self, url: str, name: str, maximum: int = MAX_FILE) -> Path:
        public_url(url)
        if self.stopped or not re.fullmatch(r"[a-zA-Z0-9._-]{1,140}", name):
            raise AcquisitionBlocked("Acquisition stopped or invalid local filename")
        maximum = min(maximum, MAX_FILE)
        if maximum < 1:
            raise AcquisitionBlocked("Invalid byte bound")
        target = self.root / name
        known = self.ledger["files"].get(name)
        if target.exists():
            if not known or known["url"] != url or digest(target.read_bytes()) != known["sha256"]:
                raise AcquisitionBlocked("Existing original has no matching integrity record")
            return target
        partial = target.with_suffix(target.suffix + ".part")
        if partial.exists():
            raise AcquisitionBlocked("Incomplete original retained; no automatic overwrite")
        current = url
        for attempt in range(3):
            started = time.perf_counter()
            try:
                async with self.client.stream("GET", current) as response:
                    self.operations.append(
                        {
                            "url": current,
                            "http_status": response.status_code,
                            "attempt": attempt + 1,
                        }
                    )
                    if response.status_code in {401, 403, 429}:
                        self.stopped = True
                        raise AcquisitionBlocked("Public-source authorization/quota refusal")
                    if response.status_code in {301, 302, 303, 307, 308}:
                        current = public_url(urljoin(current, response.headers.get("location", "")))
                        continue
                    if response.status_code >= 500 and attempt < 2:
                        await asyncio.sleep(0.5 * (2**attempt))
                        continue
                    if response.status_code != 200:
                        raise AcquisitionBlocked("Public file unavailable")
                    length = response.headers.get("content-length")
                    if length and (not length.isdecimal() or int(length) > maximum):
                        raise AcquisitionBlocked("Advertised file exceeds bound")
                    if length and self.ledger["network_bytes"] + int(length) > MAX_TOTAL:
                        self.stopped = True
                        raise AcquisitionBlocked("Advertised total exceeds acquisition budget")
                    if response.headers.get("content-encoding", "identity") != "identity":
                        raise AcquisitionBlocked("Compressed HTTP response refused")
                    count = 0
                    declared = int(length) if length else None
                    if declared == 0:
                        raise AcquisitionBlocked("Empty public file")
                    piece_size = min(65536, maximum, declared or maximum)
                    pieces = response.aiter_bytes(piece_size).__aiter__()
                    with partial.open("xb") as output:
                        while declared is None or count < declared:
                            # Reserve space before requesting another application-level block.
                            # Unknown-length bodies near the cap are conservatively refused.
                            if (
                                count + piece_size > maximum
                                or self.ledger["network_bytes"] + piece_size > MAX_TOTAL
                            ):
                                self.stopped = True
                                raise AcquisitionBlocked("Acquisition byte reserve exhausted")
                            try:
                                block = await anext(pieces)
                            except StopAsyncIteration:
                                break
                            count += len(block)
                            self.ledger["network_bytes"] += len(block)
                            atomic_json(self.ledger_path, self.ledger)
                            if count > maximum or self.ledger["network_bytes"] > MAX_TOTAL:
                                self.stopped = True
                                raise AcquisitionBlocked("Acquisition byte budget exceeded")
                            if time.perf_counter() - started > 180:
                                raise AcquisitionBlocked("Download deadline exceeded")
                            output.write(block)
                    self.ledger["files"][name] = {
                        "url": url,
                        "resolved_url": current,
                        "bytes": count,
                        "sha256": digest(partial.read_bytes()),
                        "http_status": 200,
                    }
                    partial.rename(target)
                    atomic_json(self.ledger_path, self.ledger)
                    return target
            except httpx.HTTPError:
                if partial.exists() or attempt == 2:
                    raise AcquisitionBlocked("Public download transport unavailable") from None
                await asyncio.sleep(0.5 * (2**attempt))
        raise AcquisitionBlocked("Public redirect/retry budget exhausted")

    async def acquire(self, source: Source) -> dict[str, Any]:
        if source.license_id not in {"CC-BY-4.0", "CC-BY-SA-4.0", "NIST-technical-series"}:
            raise AcquisitionBlocked("Unknown/restricted license")
        evidence = await self.download(
            source.license_evidence_url, source.source_id + "-license-evidence.txt", 2_000_000
        )
        license_text = evidence.read_text("utf-8")
        if source.license_marker not in license_text:
            raise AcquisitionBlocked("Required source-specific license statement absent")
        if (
            source.license_id in {"CC-BY-4.0", "CC-BY-SA-4.0"}
            and "zenodo.org/api/" not in source.license_evidence_url
        ):
            expected = "creativecommons.org/licenses/" + (
                "by-sa/4.0" if source.license_id == "CC-BY-SA-4.0" else "by/4.0"
            )
            if expected not in license_text:
                raise AcquisitionBlocked("Specific Creative Commons license link absent")
        # Verify each Zenodo dataset's own license, never a repository default.
        if source.license_evidence_url.startswith("https://zenodo.org/api/records/"):
            record = json.loads(license_text)
            if record.get("metadata", {}).get("license", {}).get("id") != "cc-by-4.0":
                raise AcquisitionBlocked("Dataset license changed")
            files = [
                f
                for f in record.get("files", [])
                if f.get("links", {}).get("self") == source.download_url
            ]
            if len(files) != 1 or files[0].get("checksum") != "md5:" + str(source.expected_md5):
                raise AcquisitionBlocked("Dataset file provenance changed")
        asset = await self.download(source.download_url, source.source_id + "." + source.format)
        raw = asset.read_bytes()
        if source.expected_bytes is not None and len(raw) != source.expected_bytes:
            raise AcquisitionBlocked("Published file size mismatch")
        if source.expected_md5 is not None:
            observed = hashlib.md5(raw, usedforsecurity=False).hexdigest()
            if observed != source.expected_md5:
                raise AcquisitionBlocked("Published checksum mismatch")
        if source.format == "zip" and not raw.startswith(b"PK\x03\x04"):
            raise AcquisitionBlocked("Not a ZIP archive")
        if source.format == "pdf" and not raw.startswith(b"%PDF-"):
            raise AcquisitionBlocked("Not a PDF")
        if source.format in {"csv", "adoc", "md"}:
            text = raw.decode("utf-8-sig")
            if "\x00" in text or text.lstrip().lower().startswith(("<!doctype html", "<html")):
                raise AcquisitionBlocked("Unexpected binary/HTML in text source")
        return {
            **source.model_dump(),
            "local_path": str(asset.resolve()),
            "bytes": len(raw),
            "sha256": digest(raw),
            "license_evidence_path": str(evidence.resolve()),
            "license_evidence_sha256": digest(evidence.read_bytes()),
            "processing_notice": "Extracted, normalized and chunked by AEGIS GRID on 2026-10-17; "
            "reference only; no source endorsement or plant authorization",
        }
