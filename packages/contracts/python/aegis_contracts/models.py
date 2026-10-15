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


class TwinMeasurement(Contract):
    schema_version: Literal["1.0.0"] = "1.0.0"
    model_version: Literal["thermal-bootstrap-v1"] = "thermal-bootstrap-v1"
    seed: Annotated[int, Field(ge=0, le=4294967295)]
    state_version: Annotated[int, Field(ge=1)]
    simulation_time_s: Annotated[FiniteFloat, Field(ge=0)]
    coolant_temperature_c: Annotated[FiniteFloat, Field(ge=-273.15, le=1000)]
    cells: Annotated[list[CellMeasurement], Field(min_length=6, max_length=6)]

    @model_validator(mode="after")
    def unique_cells(self) -> "TwinMeasurement":
        if len({cell.cell_id for cell in self.cells}) != 6:
            raise ValueError("exactly six distinct cells are required")
        return self


class PlantTelemetry(TwinMeasurement):
    source: Literal["local_cpp_simulator"] = "local_cpp_simulator"
    run_id: Annotated[str, Field(pattern=r"^[0-9a-f-]{36}$")]
    simulator_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    observed_at: Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}T.+\+00:00$")]


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
    phase: Literal[1] = 1
    mode: Literal["local_simulation"] = "local_simulation"
    mutations_enabled: Literal[False] = False
    capabilities: list[Capability]
