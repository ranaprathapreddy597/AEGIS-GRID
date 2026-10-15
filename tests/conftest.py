from pathlib import Path

import pytest
from aegis_contracts.config import Settings
from pydantic import SecretStr


@pytest.fixture
def settings() -> Settings:
    return Settings(
        viewer_token=SecretStr("test-viewer-only-" * 3),
        service_token=SecretStr("test-service-only-" * 3),
        twin_binary=Path("/build/aegis-twin"),
    )


@pytest.fixture
def telemetry() -> dict:
    return {
        "schema_version": "1.0.0",
        "model_version": "thermal-bootstrap-v1",
        "seed": 42,
        "state_version": 1,
        "simulation_time_s": 0.5,
        "coolant_temperature_c": 22.0,
        "cells": [
            {
                "cell_id": f"CELL-0{i + 1}",
                "temperature_c": 25.5,
                "load_fraction": 0.5,
                "heat_input_w": 600.0,
            }
            for i in range(6)
        ],
        "source": "local_cpp_simulator",
        "run_id": "00000000-0000-0000-0000-000000000001",
        "simulator_sha256": "a" * 64,
        "observed_at": "2026-10-14T17:30:00+00:00",
    }
