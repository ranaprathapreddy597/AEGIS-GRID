"""Two native, hosted, read-only authorization demonstrations. No scope widening."""

import argparse
import asyncio
import hashlib
import json
import os
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from aegis_agents.graph import build_graph
from aegis_agents.recovery_gate import recovery_eligibility
from aegis_agents.service import InvestigationService
from aegis_api.authorization import AuthorizationService
from aegis_api.gateway import SimulatorGateway
from aegis_api.storage import TelemetryStore
from aegis_contracts.config import Settings
from aegis_contracts.models import EdgeIncident, ObservedSample, SensorFrame
from aegis_edge.runner import SupervisedTwin
from aegis_edge.twin import scenario_from_file
from aegis_inference.token_factory import TokenFactoryClient
from aegis_ingestion.acquisition import atomic_json
from aegis_ingestion.corpus import decide
from aegis_ingestion.dual_store import DualKnowledgeStore
from aegis_ingestion.knowledge import SemanticEmbedding, digest
from aegis_ingestion.library import fixture_library
from dev import COMPOSE, ROOT


async def persist(event, config):
    journal = TelemetryStore(config)
    try:
        return await journal.append(event)
    finally:
        await journal.close()


def native_event(identifier, library):
    scenario = scenario_from_file(Path("data/scenarios"), identifier)
    supervisor = SupervisedTwin(scenario, library)
    history = []
    try:
        for _ in range(600):
            frame, status = supervisor.step(1.0)
            if frame.measurement.packet_available:
                history.append(
                    ObservedSample(
                        version=frame.measurement.sampled_version,
                        time_s=frame.measurement.sampled_time_s,
                        temperatures=[c.temperature_c for c in frame.cells],
                    )
                )
                history = history[-21:]
            if status and status.latched:
                break
        snapshot = supervisor.incident_snapshot
        if snapshot is None or status is None or not status.evidence:
            raise ValueError("Actual supervised anomaly required")
        run_id = str(uuid4())
        return EdgeIncident(
            event_id=digest((run_id + snapshot.sha256).encode()),
            run_id=run_id,
            kind="anomaly",
            state_version=frame.state_version,
            simulation_time_s=frame.simulation_time_s,
            evidence=status.evidence,
            observed=SensorFrame.from_twin(frame),
            snapshot=snapshot,
            observed_history=history,
        )
    finally:
        supervisor.close()


def protection_state(authorization, gateway):
    resource = gateway.resource()
    return {
        "proposal_count": authorization.client.aegis.auth_proposals.count_documents({}),
        "capability_record_count": authorization.client.aegis.auth_proposals.count_documents(
            {"capability": {"$exists": True}}
        ),
        "ceremony_count": authorization.client.aegis.auth_ceremonies.count_documents({}),
        "resource_version": resource["version"],
        "snapshot_sha256": resource["snapshot"]["sha256"],
        "receipt_count": len(resource["receipts"]),
        "last_receipt_sha256": resource["last_receipt_sha256"],
    }


def worker():
    config = Settings.from_env()
    library = config.twin_library
    manuals = fixture_library()
    model = TokenFactoryClient(config.inference_api_key)
    knowledge = DualKnowledgeStore(
        config.pinecone_index_host,
        config.pinecone_api_key,
        SemanticEmbedding(),
        config.knowledge_directory,
    )
    service = InvestigationService(
        config.graph_password.get_secret_value(), library, hosted_backend=model, knowledge=knowledge
    )
    gateway = SimulatorGateway(
        config.gateway_password.get_secret_value(), library, config.capability_public_key
    )
    authorization = AuthorizationService(config, gateway, service)
    evidence = {
        "status": "BLOCKED",
        "utc": datetime.now(UTC).isoformat(),
        "physical_io": False,
        "pinecone_writes": 0,
        "scenarios": {},
        "source_base_revision": os.environ.get("AEGIS_PROOF_REVISION", "unknown"),
        "worker_sha256": digest(Path(__file__).read_bytes()),
        "graph_sha256": digest(Path(build_graph.__code__.co_filename).read_bytes()),
        "observation_horizon_s": 600,
        "eligibility_gate_sha256": digest(
            Path(recovery_eligibility.__code__.co_filename).read_bytes()
        ),
        "native_binary_sha256": hashlib.sha256(library.read_bytes()).hexdigest(),
    }
    started = time.perf_counter()
    try:
        registry = [
            json.loads(p.read_bytes())
            for p in sorted(Path("data/scenarios").glob("scenario-*.json"))
        ]
        plant_decisions = {
            f"CELL-0{i}": decide(manuals.pages, f"CELL-0{i}").model_dump() for i in range(1, 7)
        }
        compatible = all(d["status"] == "simulator_evidence_only" for d in plant_decisions.values())
        faults = sum(r["config"]["fault_mask"] != 0 for r in registry)
        evidence["applicability_audit"] = {
            "scope": "Static registry eligibility for shared six-cell stop; no manuals excluded",
            "registered_scenarios": len(registry),
            "registered_fault_scenarios": faults,
            "manual_corpus_sha256": manuals.digest,
            "plant_decisions": plant_decisions,
            "noncontradictory_shared_plant_candidates": faults if compatible else 0,
            "gateway_policy": "Fault-free stationary sandbox only; incident scope unavailable",
        }
        evidence["protected_before"] = protection_state(authorization, gateway)
        evidence["counts_before"] = (
            asyncio.run(knowledge.count()),
            asyncio.run(knowledge.external.count()),
        )
        for name, identifier in (("A", "scenario-010"), ("B", "scenario-090")):
            case_started = time.perf_counter()
            event = native_event(identifier, library)
            record = asyncio.run(persist(event, config))
            result = service.run(record, str(uuid4()))
            eligibility = recovery_eligibility(result)
            row = {
                "status": "BLOCKED",
                "native_scenario": identifier,
                "fault_fixture_sha256": digest(
                    (Path("data/scenarios") / (identifier + ".json")).read_bytes()
                ),
                "incident_record": record.model_dump(),
                "investigation": result.model_dump(),
                "eligibility": eligibility.model_dump(),
                "incident_challenge_requested": False,
                "reason": "Approval blocked: manual conflict and unavailable incident scope",
                "recovery_executed": False,
                "emergency_supervision": "Unmodified local shield active; no observe-only mode",
                "elapsed_s": time.perf_counter() - case_started,
            }
            evidence["scenarios"][name] = row
            atomic_json(ROOT / "docs/results/recovery-scenarios-live.json", evidence)
            if model.blocked_until or knowledge.blocked or knowledge.external.blocked:
                evidence["provider_stop"] = (
                    "Authorization/quota circuit opened; no further provider workflow"
                )
                break
        evidence["protected_after"] = protection_state(authorization, gateway)
        evidence["protected_state_unchanged"] = (
            evidence["protected_before"] == evidence["protected_after"]
        )
        if not knowledge.blocked and not knowledge.external.blocked:
            evidence["counts_after"] = (
                asyncio.run(knowledge.count()),
                asyncio.run(knowledge.external.count()),
            )
        b = evidence["scenarios"].get("B")
        if b:
            r = b["investigation"]
            b["unsafe_challenger_rejected"] = bool(
                r["candidates"] and not r["candidates"][0]["red_accepted"]
            )
            b["action_recommended_by_amd"] = bool(
                r["hosted_planning"] and r["hosted_planning"]["recommendation"] != "abstain"
            )
            b["status"] = (
                "PASS"
                if (
                    b["action_recommended_by_amd"]
                    and b["unsafe_challenger_rejected"]
                    and r["manual_decision"] == "no_action"
                    and r["status"] == "paused_no_action"
                    and len({c["namespace"] for c in r["source_citations"]}) == 2
                    and evidence["protected_state_unchanged"]
                )
                else "PARTIAL"
            )
        evidence["status"] = "PARTIAL" if b and b["status"] == "PASS" else "BLOCKED"
    finally:
        evidence["elapsed_s"] = time.perf_counter() - started
        evidence["amd_model_attempts"] = model.calls
        evidence["amd_catalog_attempts"] = model.catalog_calls
        evidence["reserved_tokens"] = model.token_reservations
        evidence["amd_diagnostics"] = model.diagnostics
        evidence["pinecone_operations"] = [*knowledge.operations, *knowledge.external.operations]
        atomic_json(ROOT / "docs/results/recovery-scenarios-live.json", evidence)
        service.close()
        authorization.close()
        gateway.close()
        asyncio.run(model.close())
        asyncio.run(knowledge.close())
    print(
        {
            "status": evidence["status"],
            "scenarios": {k: v["status"] for k, v in evidence["scenarios"].items()},
            "amd_attempts": model.calls,
            "protected_state_unchanged": evidence.get("protected_state_unchanged"),
        }
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        worker()
        return
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    environment = {
        **os.environ,
        "AEGIS_MODEL_CACHE": (Path.home() / ".cache/huggingface").as_posix(),
        "AEGIS_PROOF_REVISION": revision,
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
            "--env",
            "AEGIS_PROOF_REVISION",
            "--volume",
            str(ROOT / "tools") + ":/app/tools:ro",
            "--volume",
            str(ROOT / "docs/results") + ":/app/docs/results",
            "api",
            "python",
            "tools/recovery_scenarios.py",
            "--worker",
        ],
        cwd=ROOT,
        env=environment,
        check=True,
        timeout=360,
    )


if __name__ == "__main__":
    main()
