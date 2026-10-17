"""Real local Mongo authorization boundaries; no successful operational writes."""

import json
from typing import Any

from aegis_contracts.config import Settings
from pymongo import MongoClient
from pymongo.errors import OperationFailure


def main() -> None:
    config = Settings.from_env()
    identities = [
        (
            "aegis_graph",
            config.graph_password,
            (
                "sandbox_resources",
                "auth_credentials",
                "auth_proposals",
                "commissioned_resources",
                "commissioned_proposals",
            ),
        ),
        (
            "aegis_approver",
            config.approver_password,
            (
                "sandbox_resources",
                "plans",
                "actions",
                "audit",
                "commissioned_resources",
                "commissioned_reports",
            ),
        ),
        (
            "aegis_gateway",
            config.gateway_password,
            (
                "auth_credentials",
                "auth_proposals",
                "plans",
                "actions",
                "audit",
                "commissioned_proposals",
                "commissioned_reports",
            ),
        ),
        (
            "aegis_ingestor",
            config.mongo_writer_password,
            (
                "sandbox_resources",
                "auth_proposals",
                "commissioned_resources",
                "commissioned_reports",
                "commissioned_proposals",
            ),
        ),
    ]
    denied = 0
    for username, password, collections in identities:
        if password is None:
            raise RuntimeError("Real scoped credential required")
        client: MongoClient[dict[str, Any]] = MongoClient(
            "mongo",
            27017,
            username=username,
            password=password.get_secret_value(),
            authSource="aegis",
            serverSelectionTimeoutMS=1500,
            socketTimeoutMS=2000,
            retryWrites=False,
        )
        try:
            for name in collections:
                try:
                    client.aegis[name].update_one(
                        {"_id": "nonexistent-acl-contract-fixture"}, {"$set": {"forbidden": True}}
                    )
                except OperationFailure as error:
                    if error.code != 13:
                        raise RuntimeError("Unexpected role refusal") from None
                    denied += 1
                else:
                    raise RuntimeError("Forbidden update privilege granted")
        finally:
            client.close()
    print(
        json.dumps(
            {
                "result": "PASS",
                "actual_mongo_privilege_denials": denied,
                "successful_operational_writes": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
