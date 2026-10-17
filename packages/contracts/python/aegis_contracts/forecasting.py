"""Advisory, observed-only thermal extrapolation contracts."""

from typing import Annotated, Literal

from pydantic import Field

from aegis_contracts.models import CellId, Contract, FiniteFloat, SensorFrame


class ForecastRequest(Contract):
    history: Annotated[list[SensorFrame], Field(min_length=1, max_length=121)]


class CellForecast(Contract):
    cell_id: CellId
    observed_temperature_c: FiniteFloat
    slope_c_per_s: FiniteFloat
    projected_temperature_c: FiniteFloat
    extrapolation_error_c: FiniteFloat
    crossing_in_s: FiniteFloat | None
    warning: bool


class ThermalForecast(Contract):
    method: Literal["observed_linear_trend_v1"] = "observed_linear_trend_v1"
    status: Literal["available", "abstained"]
    reason: str
    horizon_s: Literal[60] = 60
    thermal_limit_c: Literal[70] = 70
    observation_count: int
    cells: list[CellForecast]
    warning: bool
    execution_authority: Literal[False] = False
    limitation: str = (
        "Synthetic simulator advisory only. Linear trend assumes unchanged conditions; "
        "sensor spoofing and abrupt faults can defeat it. Error bands are heuristic, "
        "not calibrated confidence intervals. No approval or control authority."
    )
