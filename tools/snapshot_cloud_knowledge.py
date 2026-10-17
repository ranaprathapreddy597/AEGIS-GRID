"""Read existing records only; create integrity-pinned local retrieval manifests."""

import asyncio
import json

from aegis_ingestion.knowledge import canonical, digest
from aegis_ingestion.pinecone import PineconeEvidenceReader
from dev import ROOT, read_env
from pydantic import SecretStr

NAMESPACES = {"aegis-synthetic-v1-6e4d75051cbcaf1e": 1235, "real-world-v1": 103}


async def main():
    env = read_env()
    reader = PineconeEvidenceReader(env["PINECONE_INDEX_HOST"], SecretStr(env["PINECONE_API_KEY"]))
    output = ROOT / ".run/cloud-knowledge"
    output.mkdir(parents=True, exist_ok=True)
    receipt = {"mode": "existing-records-read-only", "operations": [], "namespaces": {}}
    try:
        for namespace, expected in NAMESPACES.items():
            ids = []
            token = None
            for _ in range(20):
                params = {"namespace": namespace, "limit": "100"}
                if token:
                    params["paginationToken"] = token
                response = await reader.client.get("/vectors/list", params=params)
                receipt["operations"].append(
                    {"operation": "list", "namespace": namespace, "status": response.status_code}
                )
                response.raise_for_status()
                if len(response.content) > 1048576:
                    raise ValueError("Response bound exceeded")
                value = response.json()
                ids.extend(row["id"] for row in value["vectors"])
                token = value.get("pagination", {}).get("next")
                if not token:
                    break
            if token or len(ids) != expected or len(set(ids)) != expected:
                raise ValueError("Existing namespace record count mismatch")
            rows = []
            for offset in range(0, len(ids), 20):
                batch = ids[offset : offset + 20]
                response = await reader.client.get(
                    "/vectors/fetch",
                    params=[("namespace", namespace), *[("ids", i) for i in batch]],
                )
                receipt["operations"].append(
                    {
                        "operation": "fetch",
                        "namespace": namespace,
                        "status": response.status_code,
                        "count": len(batch),
                    }
                )
                response.raise_for_status()
                if len(response.content) > 1048576:
                    raise ValueError("Response bound exceeded")
                vectors = response.json()["vectors"]
                if set(vectors) != set(batch):
                    raise ValueError("Incomplete fetch")
                for identifier in batch:
                    metadata = dict(vectors[identifier]["metadata"])
                    text = metadata.pop("text")
                    if (
                        metadata["tenant_id"] != "local"
                        or metadata["plant_id"] != "isolated-simulator"
                    ):
                        raise ValueError("Tenant scope mismatch")
                    prefix = "agk1-" if expected == 1235 else "agrw1-"
                    if identifier != prefix + digest(canonical(metadata).encode()) or metadata.get(
                        "text_sha256"
                    ) != digest(text.encode()):
                        raise ValueError("Existing record integrity mismatch")
                    rows.append({"id": identifier, "text": text, "metadata": metadata})
            if (
                expected == 1235
                and digest(canonical(ids).encode())[:16] != namespace.rsplit("-", 1)[1]
            ):
                raise ValueError("Synthetic corpus version mismatch")
            if expected == 103:
                approved = [
                    json.loads(line)
                    for line in (ROOT / ".run/real-world-v1/chunks.jsonl")
                    .read_text("utf-8")
                    .splitlines()
                ]
                if {r["id"]: r for r in rows} != {r["id"]: r for r in approved}:
                    raise ValueError("Real-world approved corpus mismatch")
            path = output / ("synthetic.jsonl" if expected == 1235 else "real-world.jsonl")
            path.write_text("".join(canonical(row) + "\n" for row in rows), encoding="utf-8")
            receipt["namespaces"][namespace] = {
                "file": path.name,
                "count": len(rows),
                "sha256": digest(path.read_bytes()),
            }
    finally:
        await reader.close()
    (ROOT / "data/cloud-knowledge-manifest.json").write_text(
        json.dumps(receipt["namespaces"], indent=2) + "\n"
    )
    (ROOT / "docs/results/cloud-knowledge-snapshot.json").write_text(
        json.dumps(receipt, indent=2) + "\n"
    )
    print({"records_read": sum(v["count"] for v in receipt["namespaces"].values()), "writes": 0})


if __name__ == "__main__":
    asyncio.run(main())
