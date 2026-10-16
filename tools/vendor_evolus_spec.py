"""Derive the inspected provider contract without changing the supplied source."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    raw = (ROOT / "api-1.json").read_bytes()
    source = json.loads(raw.decode("utf-8-sig"))
    prefix = "/api/v1/memories"
    paths = {
        path: {method: op for method, op in methods.items() if method == "get"}
        for path, methods in source["paths"].items()
        if path == prefix or path.startswith(prefix + "/") and "document" in path
    }
    for path in ("/api/v1/agents", "/api/v1/agents/{agentId}"):
        paths[path] = {"get": source["paths"][path]["get"]}
    result = {
        "openapi": source["openapi"],
        "info": source["info"],
        "servers": source["servers"],
        "security": source["security"],
        "components": source["components"],
        "paths": {path: ops for path, ops in paths.items() if ops},
        "x-aegis-source-sha256": hashlib.sha256(raw).hexdigest(),
        "x-aegis-note": "Supplied specification; read-only subset, not live service evidence",
    }
    target = ROOT / "services/ingestion/aegis_ingestion/evolus-read-contract.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("Provider read contract derived; original input unchanged")


if __name__ == "__main__":
    main()
