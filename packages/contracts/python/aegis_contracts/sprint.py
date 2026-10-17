"""Read-only summaries of checked-in reproducible experiments."""

from typing import Annotated, Literal

from pydantic import Field

from aegis_contracts.models import Contract, FiniteFloat


class ExperimentMetric(Contract):
    name: str
    value: FiniteFloat | None
    unit: str = "fraction"


class ExperimentSummary(Contract):
    name: str
    state: Literal["PASS", "PARTIAL", "BLOCKED"]
    scope: str
    metrics: list[ExperimentMetric]
    limitations: list[str]
    artifact: str
    artifact_sha256: Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]


class AttackCheck(Contract):
    name: str
    state: Literal["PASS", "FAIL"]
    passed: int
    reason: str
    selector: str


class SprintEvidence(Contract):
    mode: Literal["recorded_offline_experiments"] = "recorded_offline_experiments"
    execution_authority: Literal[False] = False
    experiments: list[ExperimentSummary]
    attacks: list[AttackCheck]
    limitations: list[str]
