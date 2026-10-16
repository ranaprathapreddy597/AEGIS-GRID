"""Opt-in documented read-only provider checks; never print credentials or content."""

import asyncio
import json

from aegis_ingestion.evolus import EvolusDocumentExtractor, ProviderUnavailable
from dev import read_env
from pydantic import SecretStr


async def main() -> None:
    values = read_env()
    key, application = values.get("EVOLUS_API_KEY"), values.get("EVOLUS_APPLICATION_ID")
    if not key or not application:
        print(
            json.dumps(
                {
                    "status": "BLOCKED",
                    "live_verified": False,
                    "reason": "EVOLUS_API_KEY and application scope required locally",
                }
            )
        )
        return
    client = EvolusDocumentExtractor(
        SecretStr(key), application, auth_kind=values.get("EVOLUS_AUTH_KIND", "application")
    )
    try:
        formats = await client.formats()
        result = {
            "status": "READ_AUTH_VERIFIED",
            "formats_received": bool(formats),
            "extraction_verified": False,
            "external_writes": 0,
        }
        memory, document = values.get("EVOLUS_MEMORY_ID"), values.get("EVOLUS_DOCUMENT_ID")
        if memory and document:
            chunks = await client.chunks(memory, document)
            result["chunks_received"] = len(chunks)
            # ChunkResponse has no guaranteed page/revision/confidence. Do not invent them.
            result["page_citations_verified"] = False
        print(json.dumps(result))
    except (ProviderUnavailable, ValueError):
        print(
            json.dumps(
                {
                    "status": "BLOCKED",
                    "live_verified": False,
                    "reason": "Provider authentication/read/schema not verified",
                }
            )
        )
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
