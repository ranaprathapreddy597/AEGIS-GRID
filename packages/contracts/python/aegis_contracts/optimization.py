"""Checked synthetic futures are evidence, never capabilities to execute."""

from typing import Annotated, Literal

from pydantic import Field

from aegis_contracts.models import Contract, FiniteFloat, SimulatorControls

Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class FutureSample(Contract):
    elapsed_s: Annotated[FiniteFloat, Field(ge=0, le=1200)]
    maximum_temperature_c: FiniteFloat
    production_units: FiniteFloat
    energy_kwh: FiniteFloat


class SimRollout(Contract):
    horizon_s: Annotated[int, Field(ge=1, le=1200)]
    steps: Annotated[int, Field(ge=1, le=1200)]
    maximum_temperature_c: FiniteFloat
    maximum_pressure_kpa: FiniteFloat
    maximum_feeder_power_w: FiniteFloat
    minimum_flow_kg_s: FiniteFloat
    energy_kwh: Annotated[FiniteFloat, Field(ge=0)]
    production_units: Annotated[FiniteFloat, Field(ge=0)]
    downtime_s: Annotated[FiniteFloat, Field(ge=0)]
    actuator_travel: Annotated[FiniteFloat, Field(ge=0)]
    maximum_ramp_excess: Annotated[FiniteFloat, Field(ge=0)]
    violation_mask: Annotated[int, Field(ge=0, le=31)]
    samples: Annotated[list[FutureSample], Field(max_length=122)]


class UncertaintyCase(Contract):
    case_id: str
    seed: Annotated[int, Field(ge=0, le=4294967295)]
    snapshot_sha256: Digest
    fault_mask: Annotated[int, Field(ge=0, le=255)]
    target: Annotated[int, Field(ge=0, le=5)]
    severity: Annotated[FiniteFloat, Field(ge=0, le=1)]
    temperature_offset_c: FiniteFloat


class Counterexample(Contract):
    case_id: str
    violation_mask: Annotated[int, Field(ge=1, le=31)]
    maximum_temperature_c: FiniteFloat


class PlanEvaluation(Contract):
    candidate_id: str
    controls: SimulatorControls
    feasible: bool
    checked_cases: int
    failed_cases: int
    worst_temperature_c: FiniteFloat
    worst_objective: FiniteFloat
    mean_energy_kwh: FiniteFloat
    minimum_production_units: FiniteFloat
    maximum_downtime_s: FiniteFloat
    maximum_actuator_travel: FiniteFloat
    counterexamples: Annotated[list[Counterexample], Field(max_length=3)]


class RecoveryAssessment(Contract):
    artifact_sha256: Digest
    incident_id: Digest
    source_snapshot_sha256: Digest
    native_binary_sha256: Digest
    model_version: Literal["coupled-factory-v3"] = "coupled-factory-v3"
    algorithm: Literal["enumerative-minimax-v1"] = "enumerative-minimax-v1"
    status: Literal["checked_non_executable", "abstained"]
    reason: str
    policy: dict[str, FiniteFloat]
    objective_weights: dict[str, FiniteFloat]
    assumptions: list[str]
    cases: Annotated[list[UncertaintyCase], Field(max_length=37)]
    candidates: Annotated[list[PlanEvaluation], Field(max_length=11)]
    selected_candidate_id: str | None
    total_rollouts: Annotated[int, Field(ge=0, le=500)]
    native_substeps: Annotated[int, Field(ge=0)]
    horizon_s: Literal[600] = 600
    baseline: SimRollout | None
    intervention: SimRollout | None
    executable: Literal[False] = False
    manual_action_gate: Literal["BLOCKED"] = "BLOCKED"
    live_gates: Literal["MI300X/Evolus/Pinecone BLOCKED"] = "MI300X/Evolus/Pinecone BLOCKED"
