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
        "schema_version": "2.0.0",
        "model_version": "coupled-factory-v2",
        "seed": 42,
        "scenario_id": "scenario-000",
        "scenario_sha256": "b" * 64,
        "injected_fault_mask": 0,
        "measurement": {
            "sampled_version": 1,
            "sampled_time_s": 0.5,
            "age_s": 0.0,
            "packet_available": True,
            "dropped_packets": 0,
        },
        "ground_truth": {
            "cells": [
                {
                    "cell_id": f"CELL-0{i + 1}",
                    "temperature_c": 25.5,
                    "flow_kg_s": 0.1,
                    "valve_fraction": 1.0,
                }
                for i in range(6)
            ],
            "pressure_kpa": 10.0,
            "total_flow_kg_s": 0.6,
            "pump_fraction": 0.85,
            "feeder_power_w": 10000.0,
            "energy_j": 5000.0,
            "production_units": 0.01,
            "energy_residual_j": 0.0,
        },
        "state_version": 1,
        "simulation_time_s": 0.5,
        "coolant_temperature_c": 22.0,
        "cells": [
            {
                "cell_id": f"CELL-0{i + 1}",
                "temperature_c": 25.5,
                "load_fraction": 0.5,
                "heat_input_w": 600.0,
                "noise_bound_c": 0.1,
            }
            for i in range(6)
        ],
        "source": "local_cpp_simulator",
        "run_id": "00000000-0000-0000-0000-000000000001",
        "simulator_sha256": "a" * 64,
        "observed_at": "2026-10-14T17:30:00+00:00",
    }
