import copy

import pytest
from aegis_agents.forecasting import forecast
from aegis_contracts.forecasting import ForecastRequest
from aegis_contracts.models import SensorFrame
from pydantic import ValidationError


def history(telemetry, slope=0.2, start=58.0):
    result = []
    for index in range(16):
        payload = copy.deepcopy(telemetry)
        payload["state_version"] = index + 1
        payload["simulation_time_s"] = float(index * 2)
        payload["measurement"].update(
            sampled_version=index + 1,
            sampled_time_s=float(index * 2),
            age_s=0.0,
            packet_available=True,
        )
        payload["cells"][0]["temperature_c"] = start + slope * index * 2
        result.append(
            SensorFrame.model_validate({name: payload[name] for name in SensorFrame.model_fields})
        )
    return result


def test_linear_forecast_is_observed_only_and_advisory(telemetry):
    result = forecast(history(telemetry))
    assert result.status == "available" and result.warning
    assert result.cells[0].slope_c_per_s == pytest.approx(0.2)
    assert result.cells[0].projected_temperature_c == pytest.approx(76.0)
    assert result.cells[0].crossing_in_s == pytest.approx(30.0)
    assert not result.execution_authority
    assert (
        "ground_truth"
        not in ForecastRequest.model_json_schema()["$defs"]["SensorFrame"]["properties"]
    )


def test_cooling_and_stationary_are_not_future_crossings(telemetry):
    for slope in (-0.1, 0.0):
        result = forecast(history(telemetry, slope=slope))
        assert not result.cells[0].warning
        assert result.cells[0].crossing_in_s is None


def test_refuses_short_stale_duplicate_and_out_of_order_history(telemetry):
    rows = history(telemetry)
    assert forecast(rows[:3]).status == "abstained"
    stale = rows[-1].model_copy(
        update={"measurement": rows[-1].measurement.model_copy(update={"age_s": 6.0})}
    )
    assert forecast([*rows[:-1], stale]).status == "abstained"
    for values in ([rows[1], rows[0]], [rows[0], rows[0]], []):
        with pytest.raises(ValueError):
            forecast(values)


def test_repeated_sensor_samples_do_not_create_history(telemetry):
    rows = history(telemetry)
    frozen = [
        row.model_copy(
            update={"measurement": row.measurement.model_copy(update={"sampled_time_s": 30.0})}
        )
        for row in rows
    ]
    assert forecast(frozen).status == "abstained"


def test_input_bound_and_no_hidden_truth(telemetry):
    rows = history(telemetry)
    with pytest.raises(ValidationError):
        ForecastRequest(history=rows * 8)
    with pytest.raises(ValidationError):
        SensorFrame.model_validate({**rows[0].model_dump(), "ground_truth": {}})
