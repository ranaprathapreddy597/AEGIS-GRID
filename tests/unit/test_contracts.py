import copy

import pytest
from aegis_contracts.models import PlantTelemetry
from pydantic import ValidationError


def test_valid_frame_round_trip(telemetry):
    frame = PlantTelemetry.model_validate(telemetry)
    assert PlantTelemetry.model_validate_json(frame.model_dump_json()) == frame


@pytest.mark.parametrize(
    "field,value",
    [
        ("seed", "42"),
        ("state_version", 0),
        ("simulation_time_s", float("nan")),
        ("extra", True),
        ("source", "real_plant"),
    ],
)
def test_rejects_bad_envelope(telemetry, field, value):
    telemetry[field] = value
    with pytest.raises(ValidationError):
        PlantTelemetry.model_validate(telemetry)


@pytest.mark.parametrize(
    "field,value",
    [
        ("temperature_c", float("inf")),
        ("temperature_c", -274.0),
        ("load_fraction", 1.1),
        ("heat_input_w", -1.0),
        ("cell_id", "CELL-07"),
    ],
)
def test_rejects_invalid_cell(telemetry, field, value):
    telemetry["cells"][0][field] = value
    with pytest.raises(ValidationError):
        PlantTelemetry.model_validate(telemetry)


def test_duplicate_and_missing_cells_rejected(telemetry):
    duplicate = copy.deepcopy(telemetry)
    duplicate["cells"][1] = duplicate["cells"][0]
    with pytest.raises(ValidationError):
        PlantTelemetry.model_validate(duplicate)
    telemetry["cells"].pop()
    with pytest.raises(ValidationError):
        PlantTelemetry.model_validate(telemetry)
