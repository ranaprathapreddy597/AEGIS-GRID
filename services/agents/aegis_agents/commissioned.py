"""Separate commissioned replay graph; never mutates a plant or issues capabilities."""

import asyncio
import json
import time
from typing import Any, TypedDict
from uuid import UUID

from aegis_contracts.commissioned import CommissionedReport
from aegis_contracts.inference import ModelOpinion, PlanningOpinion
from aegis_contracts.investigation import ModelAttribution, SourceCitation
from aegis_contracts.models import IncidentRecord
from aegis_edge.commissioning import PLANT, RULES_SHA256, canonical, rules, sha, stop_certificate
from aegis_edge.sentinel import SafetyShield
from aegis_inference.client import InferenceUnavailable
from aegis_inference.token_factory import RESPONSE_IDS, HostedOpinion
from aegis_ingestion.dual_store import REAL_NAMESPACE, SYNTHETIC_NAMESPACE, DualKnowledgeStore
from aegis_ingestion.evolus import ProviderUnavailable
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt
from langsmith.run_helpers import tracing_context
from pydantic import ConfigDict
from pymongo.errors import DuplicateKeyError

from aegis_agents.graph import diagnose
from aegis_agents.history import observed_window, summarize
from aegis_agents.optimizer import optimize, verify_artifact
from aegis_agents.service import InvestigationService


class State(TypedDict):
    report_json: str


class WorkingReport(CommissionedReport):
    """Mutable local builder; every checkpoint/read uses the frozen public contract."""

    model_config = ConfigDict(frozen=False)


def config(identifier: str) -> RunnableConfig:
    return {
        "configurable": {"thread_id": "commissioned:" + str(UUID(identifier))},
        "recursion_limit": 16,
    }


def read(service: InvestigationService, identifier: str) -> CommissionedReport | None:
    saved = service.saver.get_tuple(config(identifier))
    if saved is None:
        return None
    return CommissionedReport.model_validate_json(saved.checkpoint["channel_values"]["report_json"])


def verify_report(report: CommissionedReport, record: IncidentRecord) -> None:
    if (
        report.status != "awaiting_approval"
        or report.blockers
        or report.plant_id != PLANT
        or report.incident_id != record.incident_id
        or report.rules_sha256 != RULES_SHA256
        or not report.meaningful_diagnosis
        or not report.grounded_planning
        or not report.unsafe_challenger_rejected
        or report.certificate is None
        or sha(canonical(report.model_dump(exclude={"report_sha256"}))) != report.report_sha256
    ):
        raise ValueError("Commissioned investigation admission refused")
    # Re-evaluate opinion grounding; stored booleans alone never grant admission.
    local = {h.cause for h in diagnose(record.event.observed, record.event.evidence)}
    if (
        report.diagnosis is None
        or report.diagnosis.assessment != "investigate"
        or not set(report.diagnosis.hypotheses).intersection(local)
        or not {"observed", "residuals"}.intersection(report.diagnosis.evidence_ids)
        or report.planning is None
        or report.planning.recommendation == "abstain"
        or set(report.planning.evidence_ids) != {"candidate_evaluations", "retrieved_sources"}
        or {a.role for a in report.model_attributions} != {"diagnosis", "planning"}
        or {c.namespace for c in report.source_citations} != {REAL_NAMESPACE, SYNTHETIC_NAMESPACE}
        or report.assessment is None
        or report.assessment.incident_id != record.incident_id
        or report.assessment.status != "checked_non_executable"
        or report.candidate_round != 2
        or report.proposed_controls != SafetyShield.emergency_controls()
        or any(
            a.served_model not in RESPONSE_IDS.get(a.requested_model, set())
            for a in report.model_attributions
        )
    ):
        raise ValueError("Meaningful hosted evidence or native assessment absent")
    verify_artifact(report.assessment)
    if (
        record.event.snapshot is None
        or report.assessment.source_snapshot_sha256 != record.event.snapshot.sha256
        or report.certificate.snapshot_sha256 != record.event.snapshot.sha256
        or report.assessment.native_binary_sha256 != report.certificate.native_binary_sha256
        or len(report.assessment.cases) != 37
    ):
        raise ValueError("Native adversary source/binary/case binding refused")
    safe = next(
        (
            c
            for c in report.assessment.candidates
            if c.controls == SafetyShield.emergency_controls()
        ),
        None,
    )
    unsafe = next(
        (c for c in report.assessment.candidates if c.candidate_id == "planted-unsafe"), None
    )
    if not safe or not safe.feasible or safe.checked_cases != 37 or not unsafe or unsafe.feasible:
        raise ValueError("Native all-cell stop/adversarial evaluation absent")
    feasible = report.planning_evidence.get("candidate_evaluations", {}).get(
        report.planning.recommendation, {}
    )
    if not isinstance(feasible, dict) or feasible.get("feasible") is not True:
        raise ValueError("Hosted planning did not select an evaluated feasible action")


def run(
    service: InvestigationService, resource: dict[str, Any], identifier: str
) -> CommissionedReport:
    record = IncidentRecord.model_validate(resource["incident"])
    existing = read(service, identifier)
    if existing:
        if existing.incident_id != record.incident_id:
            raise ValueError("Investigation identity conflict")
        return existing
    rules()
    report = CommissionedReport(
        investigation_id=str(UUID(identifier)),
        incident_id=record.incident_id,
        rules_sha256=RULES_SHA256,
        report_sha256="0" * 64,
    )
    graph = StateGraph(State)
    references: dict[str, list[dict[str, str]]] = {}
    backend = service.hosted_backend
    knowledge = service.knowledge
    before_calls = backend.calls if backend else 0
    before_catalogs = backend.catalog_calls if backend else 0
    before_tokens = backend.token_reservations if backend else 0
    before_diagnostics = len(backend.diagnostics) if backend else 0
    before_operations = len(knowledge.operations) if knowledge else 0
    before_external = (
        len(knowledge.external.operations) if isinstance(knowledge, DualKnowledgeStore) else 0
    )

    def evidence(data: CommissionedReport, kind: str) -> list[dict[str, str]]:
        if kind in references:
            return references[kind]
        knowledge = service.knowledge
        if not isinstance(knowledge, DualKnowledgeStore):
            data.blockers.append("dual_namespace_hosted_retrieval_required")
            return []
        try:
            hits = asyncio.run(
                knowledge.search(
                    "sensor bias physics residual coolant flow"
                    if kind == "manual"
                    else "safe stop minimax recovery cooling",
                    kind=kind,
                )
            )
        except ProviderUnavailable:
            data.blockers.append("pinecone_unavailable")
            return []
        citations = {c.reference_id: c for c in data.source_citations}
        for h in hits:
            citation = SourceCitation.model_validate(knowledge.citation(h))
            citations[citation.reference_id] = citation
        data.source_citations = list(citations.values())
        references[kind] = [
            {
                "reference_id": h.identifier,
                "untrusted_text": h.text[:300],
                "applicability": "context_only_not_commissioned_plant_rules",
            }
            for h in hits
        ]
        return references[kind]

    def hosted(data: CommissionedReport, payload: dict[str, Any], planning: bool) -> None:
        if planning:
            data.planning_evidence = payload
        else:
            data.diagnosis_evidence = payload
        backend = service.hosted_backend
        if backend is None:
            data.blockers.append("real_amd_hosted_inference_required")
            return
        try:
            result: HostedOpinion = asyncio.run(
                backend.plan_grounded(json.dumps(payload), 256)
                if planning
                else backend.investigate_grounded(json.dumps(payload), 256)
            )
            if planning and isinstance(result.opinion, PlanningOpinion):
                data.planning = result.opinion
            elif not planning and isinstance(result.opinion, ModelOpinion):
                data.diagnosis = result.opinion
            else:
                raise InferenceUnavailable("Unexpected hosted opinion schema")
            data.model_attributions.append(
                ModelAttribution(
                    role="planning" if planning else "diagnosis",
                    requested_model=result.model_id,
                    served_model=result.served_model_id,
                    attempted_models=list(result.attempted_models),
                    latency_ms=result.latency_ms,
                    prompt_tokens=result.prompt_tokens,
                    completion_tokens=result.completion_tokens,
                )
            )
        except InferenceUnavailable:
            data.blockers.append(
                "amd_planning_unavailable" if planning else "amd_diagnosis_unavailable"
            )
        data.provider_diagnostics = list(backend.diagnostics[before_diagnostics:])

    def step(name: str, function: Any) -> Any:
        def invoke(state: State) -> State:
            data = WorkingReport.model_validate_json(state["report_json"])
            function(data)
            data.traces.append(name)
            return {"report_json": data.model_dump_json()}

        return invoke

    def detective(data: CommissionedReport) -> None:
        observed = record.event.observed
        if observed is None:
            raise ValueError("Real observed channels required")
        slopes, correlations = summarize(observed_window(record.event.observed_history), 0)
        hosted(
            data,
            {
                "observed": {
                    "instrument_noise_bound_c": [c.noise_bound_c for c in observed.cells],
                    "cells": [
                        {
                            "cell_id": c.cell_id,
                            "temperature_c": c.temperature_c,
                            "heat_input_w": c.heat_input_w,
                            "flow_kg_s": c.flow_kg_s,
                        }
                        for c in observed.cells
                    ],
                    "coolant_temperature_c": observed.coolant_temperature_c,
                    "loop_pressure_kpa": observed.loop_pressure_kpa,
                },
                "residuals": {
                    "measured_physics_observer_evidence": [
                        e.model_dump() for e in record.event.evidence
                    ],
                    "history_samples": len(record.event.observed_history),
                    "method": (
                        "Energy-balance open-loop observer; residual equals estimate "
                        "minus measured temperature; no injected labels"
                    ),
                },
                "trends": slopes,
                "correlations": correlations,
                "retrieved_sources": evidence(data, "manual"),
            },
            False,
        )
        local = {h.cause for h in diagnose(observed, record.event.evidence)}
        opinion = data.diagnosis
        data.meaningful_diagnosis = bool(
            opinion
            and opinion.assessment == "investigate"
            and set(opinion.hypotheses).intersection(local)
            and {"observed", "residuals"}.intersection(opinion.evidence_ids)
        )
        if not data.meaningful_diagnosis:
            data.blockers.append("missing_or_abstaining_grounded_diagnosis")

    def native(data: CommissionedReport) -> None:
        # Numerical search stays non-executable and retains its original gate labels.
        data.assessment = optimize(record, service.library)
        bad = next(c for c in data.assessment.candidates if c.candidate_id == "planted-unsafe")
        data.unsafe_challenger_rejected = not bad.feasible and not SafetyShield.authorize(
            bad.controls, record.event.state_version, record.event.state_version
        )
        data.certificate = stop_certificate(resource["snapshot"], service.library)
        safe = next(
            c for c in data.assessment.candidates if c.controls == SafetyShield.emergency_controls()
        )
        if not safe.feasible or not data.unsafe_challenger_rejected:
            data.blockers.append("native_adversary_or_shared_stop_refused")

    def planner(data: CommissionedReport) -> None:
        if backend and time.monotonic() < backend.blocked_until:
            data.blockers.append("shared_amd_auth_quota_circuit_open")
            return
        selected = (
            next(
                (
                    c
                    for c in data.assessment.candidates
                    if c.candidate_id == data.assessment.selected_candidate_id
                ),
                None,
            )
            if data.assessment
            else None
        )
        hosted(
            data,
            {
                "candidate_evaluations": {
                    "emergency_stop": {
                        "feasible": data.certificate is not None,
                        "all_six_cells": True,
                        "duration_s": 120,
                        "native_certificate": data.certificate.model_dump()
                        if data.certificate
                        else None,
                    },
                    "minimax_candidate": {
                        "feasible": bool(
                            selected
                            and selected.feasible
                            and selected.controls == SafetyShield.emergency_controls()
                        ),
                        "scope": (
                            "Must also equal the commissioned exact six-cell stop; "
                            "no production restart"
                        ),
                    },
                    "unsafe_challenger_rejected": data.unsafe_challenger_rejected,
                    "productive_restart": "not_authorized_by_commissioned_rule_package",
                },
                "retrieved_sources": evidence(data, "recovery"),
            },
            True,
        )
        data.grounded_planning = bool(
            data.planning
            and data.planning.recommendation != "abstain"
            and set(data.planning.evidence_ids) == {"candidate_evaluations", "retrieved_sources"}
            and data.planning_evidence.get("candidate_evaluations", {})
            .get(data.planning.recommendation, {})
            .get("feasible")
            is True
        )
        if not data.grounded_planning:
            data.blockers.append("missing_or_abstaining_grounded_planning")

    def blue(data: CommissionedReport) -> None:
        data.candidate_round += 1
        if data.candidate_round == 1:
            if data.assessment is None:
                raise ValueError("Native search required")
            data.proposed_controls = next(
                c.controls for c in data.assessment.candidates if c.candidate_id == "planted-unsafe"
            )
        else:
            data.proposed_controls = SafetyShield.emergency_controls()

    def red(data: CommissionedReport) -> None:
        if data.proposed_controls is None or data.assessment is None:
            raise ValueError("Native candidate required")
        checked = next(
            c for c in data.assessment.candidates if c.controls == data.proposed_controls
        )
        accepted = checked.feasible and SafetyShield.authorize(
            data.proposed_controls, record.event.state_version, record.event.state_version
        )
        if data.candidate_round == 1 and accepted:
            raise ValueError("Unsafe candidate was not rejected")
        if data.candidate_round == 2 and not accepted:
            data.blockers.append("corrected_shared_stop_refused")

    def reporter(data: CommissionedReport) -> None:
        if backend:
            data.amd_request_attempts = backend.calls - before_calls
            data.amd_catalog_requests = backend.catalog_calls - before_catalogs
            data.reserved_tokens = backend.token_reservations - before_tokens
        if knowledge:
            data.pinecone_operations = list(knowledge.operations[before_operations:])
        if isinstance(knowledge, DualKnowledgeStore):
            data.pinecone_operations.extend(knowledge.external.operations[before_external:])
        if {c.namespace for c in data.source_citations} != {REAL_NAMESPACE, SYNTHETIC_NAMESPACE}:
            data.blockers.append("both_namespaces_required")
        data.status = "blocked" if data.blockers else "awaiting_approval"
        # Final trace is included before the immutable report digest is computed.

    for name, function in (
        ("evidence_diagnosis", detective),
        ("native_red_blue_referee", native),
        ("blue_candidate", blue),
        ("red_challenge", red),
        ("hosted_planning", planner),
        ("reporter", reporter),
    ):
        graph.add_node(name, step(name, function))

    def seal(state: State) -> State:
        data = WorkingReport.model_validate_json(state["report_json"])
        data.report_sha256 = sha(canonical(data.model_dump(exclude={"report_sha256"})))
        return {"report_json": data.model_dump_json()}

    def approval(state: State) -> State:
        data = CommissionedReport.model_validate_json(state["report_json"])
        interrupt(
            {
                "plant_id": PLANT,
                "incident_id": data.incident_id,
                "report_sha256": data.report_sha256,
                "gate": "incident_specific_WebAuthn_required",
            }
        )
        raise ValueError("Investigation graph cannot execute; separate approval graph required")

    graph.add_node("seal", seal)
    graph.add_node("approval", approval)
    graph.add_edge(START, "evidence_diagnosis")
    graph.add_edge("evidence_diagnosis", "native_red_blue_referee")
    graph.add_edge("native_red_blue_referee", "blue_candidate")
    graph.add_edge("blue_candidate", "red_challenge")
    graph.add_conditional_edges(
        "red_challenge",
        lambda s: (
            "blue_candidate"
            if CommissionedReport.model_validate_json(s["report_json"]).candidate_round == 1
            else "hosted_planning"
        ),
    )
    graph.add_edge("hosted_planning", "reporter")
    graph.add_edge("reporter", "seal")
    graph.add_conditional_edges(
        "seal",
        lambda s: (
            "approval"
            if CommissionedReport.model_validate_json(s["report_json"]).status
            == "awaiting_approval"
            else END
        ),
    )
    compiled = graph.compile(checkpointer=service.saver)
    with tracing_context(enabled=False):
        compiled.invoke({"report_json": report.model_dump_json()}, config(identifier))
    result = read(service, identifier)
    if result is None:
        raise ValueError("Durable commissioned investigation absent")
    try:
        service.client.aegis.commissioned_reports.insert_one(
            {"_id": result.investigation_id, "report": result.model_dump()}
        )
    except DuplicateKeyError:
        saved = service.client.aegis.commissioned_reports.find_one({"_id": result.investigation_id})
        if saved is None or saved["report"] != result.model_dump():
            raise ValueError("Immutable commissioned report conflict") from None
    return result
