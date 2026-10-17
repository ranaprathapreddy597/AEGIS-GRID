"""Policy tests, never live provider or incident-authorization success claims."""

from pathlib import Path

import pytest
from aegis_agents.recovery_gate import recovery_eligibility
from aegis_contracts.inference import ModelOpinion, PlanningOpinion
from aegis_contracts.investigation import Investigation, RecoveryEligibility
from aegis_ingestion.corpus import decide
from aegis_ingestion.library import fixture_library
from pydantic import ValidationError


def report():
    return Investigation(
        investigation_id="00000000-0000-0000-0000-000000000008", incident_id="a" * 64
    )


def test_all_shared_plant_cells_retain_existing_contradiction():
    library = fixture_library()
    for i in range(1, 7):
        decision = decide(library.pages, f"CELL-0{i}")
        assert decision.status == "no_action"
        assert any(f.reason == "contradiction" for f in decision.flags)


def test_model_action_cannot_issue_capability_or_ignore_full_corpus():
    r = Investigation.model_validate(
        {
            **report().model_dump(),
            "hosted_diagnosis": ModelOpinion(
                assessment="investigate",
                hypotheses=["sensor_bias"],
                evidence_ids=["observed", "residuals"],
            ),
            "hosted_planning": PlanningOpinion(
                recommendation="minimax_candidate",
                evidence_ids=["candidate_evaluations", "retrieved_sources"],
            ),
            "manual_decision": "simulator_evidence_only",  # forged/stale claim
        }
    )
    result = recovery_eligibility(r)
    assert result.status == "BLOCKED" and not result.eligible
    assert not result.challenge_issued and not result.capability_issued
    assert "unresolved_manual_evidence" in result.blockers
    assert "incident_gateway_scope_unavailable" in result.blockers
    # Merely assigning a schema-valid opinion does not establish hosted evidence.
    assert not result.meaningful_hosted_diagnosis and not result.grounded_hosted_planning
    assert any(f.citations for f in result.manual_decision.flags)


def test_abstention_and_unchecked_forecast_cannot_be_called_safe_recovery():
    result = recovery_eligibility(report())
    assert not result.meaningful_hosted_diagnosis
    assert not result.grounded_hosted_planning and not result.native_candidate_checked
    with pytest.raises(ValidationError):
        RecoveryEligibility.model_validate({**result.model_dump(), "eligible": True})
    with pytest.raises(ValidationError):
        RecoveryEligibility.model_validate({**result.model_dump(), "capability_issued": True})


def test_eligibility_http_is_authenticated_read_only_and_durable(settings):
    from aegis_api.app import create_app
    from fastapi.testclient import TestClient

    with TestClient(create_app(settings)) as client:
        path = "/api/v1/investigations/00000000-0000-0000-0000-000000000008/recovery-eligibility"
        assert client.get(path).status_code == 401
        headers = {"Authorization": "Bearer " + settings.viewer_token.get_secret_value()}
        assert client.get(path, headers=headers).status_code == 503
        assert client.post(path, headers=headers, json={"eligible": True}).status_code == 405


@pytest.mark.skipif(not Path("/build/libaegis_twin.so").exists(), reason="Native QA image required")
@pytest.mark.parametrize("identifier", ["scenario-010", "scenario-090"])
def test_real_supervised_incident_has_typed_observed_history(identifier, monkeypatch):
    monkeypatch.syspath_prepend(str(Path("tools").resolve()))
    from aegis_agents.history import observed_window
    from recovery_scenarios import native_event

    event = native_event(identifier, Path("/build/libaegis_twin.so"))
    assert event.snapshot is not None and event.evidence
    assert event.snapshot.state_version == event.state_version
    assert len(observed_window(event.observed_history)) >= 2
    assert all(len(s.temperatures) == 6 for s in event.observed_history)
    assert event.simulation_time_s <= 600
