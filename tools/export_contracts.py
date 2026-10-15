"""Generate deterministic OpenAPI/JSON Schema; never load deployment secrets."""

import argparse
import json
from pathlib import Path

from aegis_api.app import create_app
from aegis_contracts.config import Settings
from aegis_contracts.models import PlantTelemetry, TwinMeasurement
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
