"""Read-only analysis copies. These records never authorize operational mutation."""

from typing import Annotated, Literal

from pydantic import Field

from aegis_contracts.models import Contract, FiniteFloat, SentinelStatus, TwinMeasurement
from aegis_contracts.optimization import Digest


class PreviewRequest(Contract):
    scenario_id: Annotated[str, Field(pattern=r"^scenario-0[0-9]{2}$")]
    seed: Annotated[int, Field(ge=0, le=4294967295)] = 42


class PreviewSample(Contract):
    baseline: TwinMeasurement
    shielded: TwinMeasurement
    sentinel: SentinelStatus | None


class ScenarioPreview(Contract):
    artifact_sha256: Digest
    request: PreviewRequest
    native_binary_sha256: Digest
    baseline_final_snapshot_sha256: Digest
    shielded_final_snapshot_sha256: Digest
    mode: Literal["isolated_analysis_replay"] = "isolated_analysis_replay"
    operational_mutation: Literal[False] = False
    duration_s: Literal[600] = 600
    detection_s: FiniteFloat | None
    baseline_peak_c: FiniteFloat
    shielded_peak_c: FiniteFloat
    samples: Annotated[list[PreviewSample], Field(min_length=60, max_length=61)]


class HistogramBin(Contract):
    lower_c: FiniteFloat
    upper_c: FiniteFloat
    baseline: Annotated[int, Field(ge=0, le=5000)]
    intervention: Annotated[int, Field(ge=0, le=5000)]


class FutureFailure(Contract):
    case: int
    seed: int
    target: int
    severity: FiniteFloat
    baseline_peak_c: FiniteFloat
    intervention_peak_c: FiniteFloat
    baseline_violations: int
    intervention_violations: int


class FuturesEnsemble(Contract):
    artifact_sha256: Digest
    rows_sha256: Digest
    source_snapshot_sha256: Digest
    native_binary_sha256: Digest
    mode: Literal["precomputed_actual_cpp_cpu"] = "precomputed_actual_cpp_cpu"
    pairs: Literal[5000] = 5000
    total_rollouts: Literal[10000] = 10000
    native_substeps: Literal[120000000] = 120000000
    horizon_s: Literal[600] = 600
    baseline_failed: int
    intervention_failed: int
    histogram: Annotated[list[HistogramBin], Field(min_length=10, max_length=10)]
    counterexamples: Annotated[list[FutureFailure], Field(max_length=6)]
    baseline_mean_energy_kwh: FiniteFloat
    intervention_mean_energy_kwh: FiniteFloat
    baseline_mean_production: FiniteFloat
    intervention_mean_production: FiniteFloat
    intervention_mean_downtime_s: FiniteFloat
    assumptions: list[str]
