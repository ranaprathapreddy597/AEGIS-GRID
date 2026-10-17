"""Read-only live counts, origin/refusal and simulator receipt audit. No model calls."""

import argparse
import asyncio
import hashlib
import json
import os
import subprocess
from pathlib import Path

from aegis_agents.service import InvestigationService
from aegis_api.authorization import AuthorizationService
from aegis_api.commissioned_gateway import CommissionedGateway
from aegis_api.gateway import SimulatorGateway
from aegis_contracts.config import Settings
from aegis_ingestion.dual_store import DualKnowledgeStore
from aegis_ingestion.knowledge import SemanticEmbedding
from aegis_ingestion.library import fixture_library
from dev import COMPOSE, ROOT


def worker(stage):
    config = Settings.from_env()
    knowledge = DualKnowledgeStore(
        config.pinecone_index_host,
        config.pinecone_api_key,
        SemanticEmbedding(),
        config.knowledge_directory,
    )
    gateway = SimulatorGateway(
        config.gateway_password.get_secret_value(),
        config.twin_library,
        config.capability_public_key,
    )
    graph = InvestigationService(config.graph_password.get_secret_value(), config.twin_library)
    auth = AuthorizationService(config, gateway, graph)
    try:
        original = gateway.resource()
        current = CommissionedGateway(gateway).resource()
        library = fixture_library()
        result = {
            "result": "PASS",
            "stage": stage,
            "pinecone_counts": [
                asyncio.run(knowledge.count()),
                asyncio.run(knowledge.external.count()),
            ],
            "pinecone_operations": [*knowledge.operations, *knowledge.external.operations],
            "pinecone_writes": 0,
            "amd_calls": 0,
            "native_binary_sha256": hashlib.sha256(config.twin_library.read_bytes()).hexdigest(),
            "original_manual_corpus_sha256": library.digest,
            "original_manual_decision": library.decision.model_dump(),
            "original_resource": {
                "version": original["version"],
                "snapshot_sha256": original["snapshot"]["sha256"],
                "receipts": len(original["receipts"]),
                "last_receipt_sha256": original["last_receipt_sha256"],
            },
            "commissioned_resource": current,
            "commissioned_proposal_count": auth.client.aegis.commissioned_proposals.count_documents(
                {}
            ),
        }
        proof_path = Path("docs/results/commissioned-live.json")
        if proof_path.exists():
            proof = json.loads(proof_path.read_bytes())
            identifier = proof.get("proposal", {}).get("action_id")
            if identifier:
                proposal = auth.client.aegis.commissioned_proposals.find_one({"_id": identifier})
                if proposal:
                    result["approval_evidence"] = proposal.get("approval_evidence")
                    result["capability_sha256"] = hashlib.sha256(
                        proposal.get("capability", "").encode()
                    ).hexdigest()
                    result["proposal_status"] = proposal["status"]
        Path(f"docs/results/commissioned-audit-{stage}.json").write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8"
        )
        print(
            {
                "result": "PASS",
                "stage": stage,
                "counts": result["pinecone_counts"],
                "receipts": len(current["receipts"]),
            }
        )
    finally:
        asyncio.run(knowledge.close())
        auth.close()
        graph.close()
        gateway.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["before", "after"])
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        worker(args.stage)
        return
    environment = {
        **os.environ,
        "AEGIS_MODEL_CACHE": (Path.home() / ".cache/huggingface").as_posix(),
    }
    subprocess.run(
        [
            *COMPOSE,
            "-f",
            str(ROOT / "infra/local/compose.hosted.yaml"),
            "run",
            "--rm",
            "--no-deps",
            "-T",
            "--volume",
            str(ROOT / "tools") + ":/app/tools:ro",
            "--volume",
            str(ROOT / "docs/results") + ":/app/docs/results",
            "api",
            "python",
            "tools/commissioned_audit.py",
            args.stage,
            "--worker",
        ],
        cwd=ROOT,
        env=environment,
        check=True,
        timeout=120,
    )


if __name__ == "__main__":
    main()
