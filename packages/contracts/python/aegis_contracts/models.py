import hashlib
import json
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
    phase: Literal[11] = 11
    mode: Literal["local_simulation"] = "local_simulation"
    mutations_enabled: Literal[False] = False
    guarded_authorization_sandbox: bool = False
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


class ObservedSample(Contract):
    version: Annotated[int, Field(ge=0)]
    time_s: Annotated[FiniteFloat, Field(ge=0)]
    temperatures: Annotated[list[FiniteFloat], Field(min_length=6, max_length=6)]


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
    observed: SensorFrame | None = None
    observed_history: Annotated[list[ObservedSample], Field(max_length=21)] = []
    event_id: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    run_id: Annotated[str, Field(pattern=r"^[0-9a-f-]{36}$")]
    state_version: Annotated[int, Field(ge=1)]
    simulation_time_s: Annotated[FiniteFloat, Field(ge=0)]
    kind: Literal["anomaly", "local_stop"]
    evidence: Annotated[list[AnomalyEvidence], Field(max_length=12)]
    policy_revision: Literal["synthetic-shield-v1"] = "synthetic-shield-v1"
    snapshot: "IncidentSnapshot | None" = None
    origin: Literal["edge_observer", "storage_contract_fixture", "isolated_analysis"] = (
        "edge_observer"
    )

    @model_validator(mode="after")
    def snapshot_version_matches(self) -> "EdgeIncident":
        if self.snapshot is not None and self.snapshot.state_version != self.state_version:
            raise ValueError("Incident and native snapshot versions differ")
        return self


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
    snapshot: "IncidentSnapshot | None" = None

    @model_validator(mode="after")
    def snapshot_version_matches(self) -> "SupervisorFrame":
        if self.snapshot is not None and self.snapshot.state_version != self.frame.state_version:
            raise ValueError("Supervisor frame and native snapshot versions differ")
        return self


class IncidentSnapshot(Contract):
    model_version: Literal["coupled-factory-v3"] = "coupled-factory-v3"
    state_version: Annotated[int, Field(ge=1)]
    point: Literal["before_local_policy"] = "before_local_policy"
    payload_json: Annotated[str, Field(max_length=32768)]
    sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]

    @model_validator(mode="after")
    def consistent(self) -> "IncidentSnapshot":
        if hashlib.sha256(self.payload_json.encode()).hexdigest() != self.sha256:
            raise ValueError("Snapshot integrity mismatch")
        data = json.loads(self.payload_json)
        if (
            not isinstance(data, dict)
            or data.get("format") != "aegis-snapshot-v3"
            or data.get("version") != self.state_version
        ):
            raise ValueError("Snapshot revision/version mismatch")
        return self


class IncidentRecord(Contract):
    tenant_id: Literal["local"] = "local"
    incident_id: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    record_version: Literal[1] = 1
    payload_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    ingested_at: str
    event: EdgeIncident


class IncidentPage(Contract):
    items: Annotated[list[IncidentRecord], Field(max_length=50)]


class IncidentReplay(Contract):
    incident: IncidentRecord
    events: Annotated[list[IncidentRecord], Field(max_length=100)]
    reproducibility_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    snapshot_available: bool
    truncated: bool = False


class StorageStatus(Contract):
    mongo: Literal["disabled", "ready", "unavailable"]
    redis: Literal["disabled", "ready", "unavailable"]
    delivery: Literal["at_least_once_event_id_deduplication"] = (
        "at_least_once_event_id_deduplication"
    )
    retention_days: Literal[30] = 30


PlantTelemetry.model_rebuild()
EdgeIncident.model_rebuild()
SupervisorFrame.model_rebuild()
