"""Actual local checkpoint identity isolation; no successful operational writes allowed."""

import json

from aegis_contracts.config import Settings
from pymongo.errors import OperationFailure

from aegis_agents.service import InvestigationService


def main() -> None:
    config = Settings.from_env()
    if config.graph_password is None:
        raise RuntimeError("Real scoped graph credential required")
    service = InvestigationService(config.graph_password.get_secret_value(), config.twin_library)
    try:
        denied = 0
        for name in ["plans", "actions", "audit"]:
            try:
                service.client.aegis[name].insert_one({"_id": "graph-denial-contract-fixture"})
            except OperationFailure as error:
                if error.code != 13:
                    raise RuntimeError("Unexpected refusal") from None
                denied += 1
            else:
                raise RuntimeError("Graph credential escaped checkpoint scope")
        print(
            json.dumps(
                {
                    "result": "PASS",
                    "actual_mongo_denials": denied,
                    "graph_identity": "checkpoints and append-only analysis; no protected writes",
                }
            )
        )
    finally:
        service.close()


if __name__ == "__main__":
    main()
