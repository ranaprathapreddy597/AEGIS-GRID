"""Small explicit live schema checks; retain only validation fields, usage and model identity."""

import asyncio
import json
from dataclasses import asdict
from pathlib import Path

from aegis_inference.client import InferenceUnavailable
from aegis_inference.token_factory import MODEL_ORDER, TokenFactoryClient
from dev import read_env
from pydantic import SecretStr


async def main() -> None:
    values = read_env()
    rows = []
    for model in MODEL_ORDER:
        client = TokenFactoryClient(SecretStr(values["INFERENCE_API_KEY"]), models=(model,))
        try:
            result = await client.investigate(
                json.dumps(
                    {
                        "observed": {"temperature_c": 38.0, "flow_kg_s": 0.03},
                        "residuals": {"estimated_temperature_c": 80.0, "residual_c": 42.0},
                        "trends": "sensor stays flat while independent physics estimate rises",
                        "correlations": "neighbor observations rise",
                    }
                ),
                512,
            )
            row = asdict(result)
            row["opinion"] = result.opinion.model_dump()
            rows.append({"status": "VALIDATED", **row, "diagnostics": client.diagnostics})
        except InferenceUnavailable:
            rows.append(
                {
                    "status": "REFUSED_OR_UNAVAILABLE",
                    "model_id": model,
                    "diagnostics": client.diagnostics,
                    "last": client.last_diagnostic,
                }
            )
            if client.blocked_until:
                break
        finally:
            await client.close()
    Path("docs/results/live-amd-diagnostics.json").write_text(
        json.dumps(
            {
                "scope": "One synthetic sensor case per model; not representative accuracy",
                "routing_order": list(MODEL_ORDER),
                "rows": rows,
                "historical_failures": "Earlier text not retained; retrospective cause unproven",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {"checks": len(rows), "validated": sum(r["status"] == "VALIDATED" for r in rows)}
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
