from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

FiniteFloat = Annotated[float, Field(allow_inf_nan=False)]
CellId = Literal["CELL-01", "CELL-02", "CELL-03", "CELL-04", "CELL-05", "CELL-06"]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class CellMeasurement(Contract):
    cell_id: CellId
    temperature_c: Annotated[FiniteFloat, Field(ge=-273.15, le=1000)]
    load_fraction: Annotated[FiniteFloat, Field(ge=0, le=1)]
    heat_input_w: Annotated[FiniteFloat, Field(ge=0, le=10000)]
    noise_bound_c: Annotated[FiniteFloat, Field(ge=0, le=1)]
    flow_kg_s: Annotated[FiniteFloat, Field(ge=0, le=0.5)]


class TruthCell(Contract):
    cell_id: CellId
    temperature_c: Annotated[FiniteFloat, Field(ge=0, le=1000)]
    flow_kg_s: Annotated[FiniteFloat, Field(ge=0, le=0.5)]
    valve_fraction: Annotated[FiniteFloat, Field(ge=0, le=1)]


class PhysicsState(Contract):
    cells: Annotated[list[TruthCell], Field(min_length=6, max_length=6)]
    pressure_kpa: Annotated[FiniteFloat, Field(ge=0, le=180)]
    total_flow_kg_s: Annotated[FiniteFloat, Field(ge=0, le=3)]
    pump_fraction: Annotated[FiniteFloat, Field(ge=0, le=1)]
    feeder_power_w: Annotated[FiniteFloat, Field(ge=0, le=14500.000001)]
    energy_j: Annotated[FiniteFloat, Field(ge=0)]
    production_units: Annotated[FiniteFloat, Field(ge=0)]
    energy_residual_j: FiniteFloat


class MeasurementQuality(Contract):
    sampled_version: Annotated[int, Field(ge=0)]
    sampled_time_s: Annotated[FiniteFloat, Field(ge=0)]
    age_s: Annotated[FiniteFloat, Field(ge=0, le=20.000001)]
    packet_available: bool
    dropped_packets: Annotated[int, Field(ge=0)]


class Scenario(Contract):
    scenario_id: Annotated[str, Field(pattern=r"^scenario-\d{3}$")]
    seed: Annotated[int, Field(ge=0, le=4294967295)]
    fault_mask: Annotated[int, Field(ge=0, le=255)]
    severity: Annotated[FiniteFloat, Field(ge=0, le=1)]
    start_s: Annotated[FiniteFloat, Field(ge=0, le=3600)]
    noise_c: Annotated[FiniteFloat, Field(ge=0, le=1)]
    target: Annotated[int, Field(ge=0, le=5)]
    delay_steps: Annotated[int, Field(ge=0, le=20)]
    drop_every: Annotated[int, Field(ge=2, le=100)]


class SimulatorControls(Contract):
    pump: Annotated[FiniteFloat, Field(ge=0, le=1)]
    loads: Annotated[
        list[Annotated[FiniteFloat, Field(ge=0, le=1)]], Field(min_length=6, max_length=6)
    ]
    valves: Annotated[
        list[Annotated[FiniteFloat, Field(ge=0, le=1)]], Field(min_length=6, max_length=6)
    ]


class TwinMeasurement(Contract):
    schema_version: Literal["3.0.0"] = "3.0.0"
    model_version: Literal["coupled-factory-v3"] = "coupled-factory-v3"
    scenario_id: Annotated[str, Field(pattern=r"^scenario-\d{3}$")]
    seed: Annotated[int, Field(ge=0, le=4294967295)]
    state_version: Annotated[int, Field(ge=1)]
    simulation_time_s: Annotated[FiniteFloat, Field(ge=0)]
    coolant_temperature_c: Annotated[FiniteFloat, Field(ge=-273.15, le=1000)]
    loop_pressure_kpa: Annotated[FiniteFloat, Field(ge=0, le=180)]
    cells: Annotated[list[CellMeasurement], Field(min_length=6, max_length=6)]
    ground_truth: PhysicsState
    measurement: MeasurementQuality
    injected_fault_mask: Annotated[int, Field(ge=0, le=255)]

    @model_validator(mode="after")
    def unique_cells(self) -> "TwinMeasurement":
        if len({cell.cell_id for cell in self.cells}) != 6:
            raise ValueError("exactly six distinct cells are required")
        if [cell.cell_id for cell in self.cells] != [f"CELL-0{i}" for i in range(1, 7)]:
            raise ValueError("cells must be in canonical order")
        if [cell.cell_id for cell in self.ground_truth.cells] != [
            cell.cell_id for cell in self.cells
        ]:
            raise ValueError("ground truth must match cell ordering")
        if (
            self.measurement.sampled_version > self.state_version
            or abs(
                self.simulation_time_s - self.measurement.sampled_time_s - self.measurement.age_s
            )
            > 1e-6
        ):
            raise ValueError("inconsistent measurement age")
        if self.measurement.dropped_packets > self.state_version:
            raise ValueError("inconsistent packet count")
        if (
            abs(
                sum(c.flow_kg_s for c in self.ground_truth.cells)
                - self.ground_truth.total_flow_kg_s
            )
            > 1e-6
        ):
            raise ValueError("flow does not balance")
        return self


class PlantTelemetry(TwinMeasurement):
    source: Literal["local_cpp_simulator"] = "local_cpp_simulator"
    run_id: Annotated[str, Field(pattern=r"^[0-9a-f-]{36}$")]
    simulator_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    scenario_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    observed_at: Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}T.+\+00:00$")]
    sentinel: "SentinelStatus"


class Health(Contract):
    status: Literal["ok", "degraded"]
    service: str
    mode: Literal["local_simulation"] = "local_simulation"
    detail: str


class ErrorResponse(Contract):
    code: str
    message: str
    correlation_id: str


class Capability(Contract):
    name: str
    status: Literal["verified_local", "simulated", "blocked", "not_implemented"]
    detail: str


class Capabilities(Contract):
    phase: Literal[3] = 3
    mode: Literal["local_simulation"] = "local_simulation"
    mutations_enabled: Literal[False] = False
    capabilities: list[Capability]


class SensorFrame(Contract):
    """Detector input allowlist. Hidden truth, labels and scenario ID are absent."""

    state_version: Annotated[int, Field(ge=1)]
    simulation_time_s: Annotated[FiniteFloat, Field(ge=0)]
    coolant_temperature_c: Annotated[FiniteFloat, Field(ge=-273.15, le=1000)]
    loop_pressure_kpa: Annotated[FiniteFloat, Field(ge=0, le=180)]
    cells: Annotated[list[CellMeasurement], Field(min_length=6, max_length=6)]
    measurement: MeasurementQuality

    @model_validator(mode="after")
    def ordered_cells(self) -> "SensorFrame":
        if [cell.cell_id for cell in self.cells] != [f"CELL-0{i}" for i in range(1, 7)]:
            raise ValueError("Sensor cells must be in canonical order")
        return self

    @classmethod
    def from_twin(cls, frame: TwinMeasurement) -> "SensorFrame":
        return cls.model_validate({name: getattr(frame, name) for name in cls.model_fields})


class AnomalyEvidence(Contract):
    cell_id: CellId
    residual_c: FiniteFloat
    estimated_temperature_c: FiniteFloat
    observed_temperature_c: FiniteFloat
    reason: Literal["physics_disagreement", "thermal_limit", "stale_measurement", "missing_packets"]


class MemoryMatch(Contract):
    state_version: Annotated[int, Field(ge=1)]
    distance_squared: Annotated[FiniteFloat, Field(ge=0)]
    label: Literal["nominal", "sensor_anomaly"]


class SentinelStatus(Contract):
    state: Literal["warming", "nominal", "anomaly", "latched_stop"]
    evidence: Annotated[list[AnomalyEvidence], Field(max_length=12)]
    latched: bool
    first_detection_time_s: FiniteFloat | None
    applied_policy: Literal["observe_only", "none", "local_emergency_stop"]
    policy_revision: Literal["synthetic-shield-v1"] = "synthetic-shield-v1"
    latency_ms: Annotated[FiniteFloat, Field(ge=0)]
    max_estimated_temperature_c: FiniteFloat
    memory_entries: Annotated[int, Field(ge=0, le=4096)]
    memory_matches: Annotated[list[MemoryMatch], Field(max_length=3)]
    cpu_fallback: Literal[True] = True
    npu_verified: Literal[False] = False


class EdgeIncident(Contract):
    event_id: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    run_id: Annotated[str, Field(pattern=r"^[0-9a-f-]{36}$")]
    state_version: Annotated[int, Field(ge=1)]
    simulation_time_s: Annotated[FiniteFloat, Field(ge=0)]
    kind: Literal["anomaly", "local_stop"]
    evidence: Annotated[list[AnomalyEvidence], Field(max_length=12)]
    policy_revision: Literal["synthetic-shield-v1"] = "synthetic-shield-v1"


class EdgeStatus(Contract):
    cloud: Literal["disabled", "offline", "online"]
    queued_events: Annotated[int, Field(ge=0, le=256)]
    dropped_events: Annotated[int, Field(ge=0)]
    recent_events: Annotated[list[EdgeIncident], Field(max_length=128)]
    detector: Literal["sensor-only-thermal-observer-v1"] = "sensor-only-thermal-observer-v1"
    execution: Literal["isolated_simulator_cpu"] = "isolated_simulator_cpu"


class EdgeBatch(Contract):
    protocol_version: Literal["aegis-edge-v1"] = "aegis-edge-v1"
    events: Annotated[list[EdgeIncident], Field(min_length=1, max_length=32)]


class EdgeBatchAck(Contract):
    accepted_event_ids: Annotated[list[str], Field(max_length=32)]


class SupervisorFrame(Contract):
    frame: TwinMeasurement
    sentinel: SentinelStatus


PlantTelemetry.model_rebuild()
