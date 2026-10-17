"""Read-only incident eligibility. Never creates proposals, challenges or capabilities."""

from aegis_contracts.investigation import Investigation, RecoveryBlocker, RecoveryEligibility
from aegis_ingestion.dual_store import REAL_NAMESPACE, SYNTHETIC_NAMESPACE
from aegis_ingestion.library import fixture_library


def recovery_eligibility(report: Investigation) -> RecoveryEligibility:
    library = fixture_library()
    diagnosis = report.hosted_diagnosis
    meaningful = bool(
        diagnosis
        and report.backend == "amd_token_factory"
        and any(a.role == "diagnosis" for a in report.model_attributions)
        and diagnosis.assessment == "investigate"
        and diagnosis.hypotheses
        and diagnosis.evidence_ids
        and {"observed", "residuals"}.intersection(diagnosis.evidence_ids)
        and set(diagnosis.hypotheses).intersection(h.cause for h in report.hypotheses)
    )
    planning = report.hosted_planning
    grounded = bool(
        planning
        and report.backend == "amd_token_factory"
        and any(a.role == "planning" for a in report.model_attributions)
        and planning.recommendation != "abstain"
        and set(planning.evidence_ids) == {"candidate_evaluations", "retrieved_sources"}
        and {c.namespace for c in report.source_citations} == {SYNTHETIC_NAMESPACE, REAL_NAMESPACE}
    )
    last = report.candidates[-1] if report.candidates else None
    native_checked = bool(
        last
        and last.red_accepted
        and last.simulation_checked
        and last.maximum_temperature_c is not None
        and last.maximum_temperature_c < 70
        and report.recovery_assessment
        and report.native_binary_sha256
    )
    blockers: list[RecoveryBlocker] = ["incident_gateway_scope_unavailable"]
    if library.decision.status == "no_action" or report.manual_decision == "no_action":
        blockers.append("unresolved_manual_evidence")
    if not meaningful:
        blockers.append("missing_or_abstaining_diagnosis")
    if not grounded:
        blockers.append("missing_or_ungrounded_planning")
    if not native_checked:
        blockers.append("native_candidate_not_verified")
    return RecoveryEligibility(
        investigation_id=report.investigation_id,
        incident_id=report.incident_id,
        blockers=blockers,
        manual_corpus_sha256=library.digest,
        manual_decision=library.decision,
        meaningful_hosted_diagnosis=meaningful,
        grounded_hosted_planning=grounded,
        native_candidate_checked=native_checked,
    )
