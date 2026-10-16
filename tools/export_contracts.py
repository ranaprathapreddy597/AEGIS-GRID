"""Generate deterministic OpenAPI/JSON Schema; never load deployment secrets."""

import argparse
import json
from pathlib import Path

from aegis_api.app import create_app
from aegis_contracts.config import Settings
from aegis_contracts.inference import InferenceResult, MemoryBudget
from aegis_contracts.investigation import Investigation
from aegis_contracts.manuals import ManualDocument, ManualEvidence, ManualRecords, OEMConstraint
from aegis_contracts.models import PlantTelemetry, Scenario, SimulatorControls, TwinMeasurement
from aegis_contracts.optimization import RecoveryAssessment, SimRollout
from pydantic import SecretStr

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    # Non-runtime schema fixture, never a working deployment credential.
    settings = Settings(
        viewer_token=SecretStr("schema-export-only" * 3),
        service_token=SecretStr("schema-service-only" * 3),
    )
    outputs = {
        "openapi.json": create_app(settings).openapi(),
        "plant-telemetry.schema.json": PlantTelemetry.model_json_schema(),
        "twin-measurement.schema.json": TwinMeasurement.model_json_schema(),
        "settings.schema.json": Settings.model_json_schema(),
        "scenario.schema.json": Scenario.model_json_schema(),
        "simulator-controls.schema.json": SimulatorControls.model_json_schema(),
        "manual-document.schema.json": ManualDocument.model_json_schema(),
        "oem-constraint.schema.json": OEMConstraint.model_json_schema(),
        "manual-evidence.schema.json": ManualEvidence.model_json_schema(),
        "manual-records.schema.json": ManualRecords.model_json_schema(),
        "memory-budget.schema.json": MemoryBudget.model_json_schema(),
        "inference-result.schema.json": InferenceResult.model_json_schema(),
        "investigation.schema.json": Investigation.model_json_schema(),
        "recovery-assessment.schema.json": RecoveryAssessment.model_json_schema(),
        "sim-rollout.schema.json": SimRollout.model_json_schema(),
    }
    for name, schema in outputs.items():
        target = ROOT / "packages/contracts/generated" / name
        text = json.dumps(schema, indent=2, sort_keys=True) + "\n"
        if args.check:
            if not target.exists() or target.read_text(encoding="utf-8") != text:
                raise SystemExit(f"Contract drift: regenerate {target.name}")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8", newline="\n")
    print("Contract schemas match" if args.check else "Contract schemas generated")


if __name__ == "__main__":
    main()
