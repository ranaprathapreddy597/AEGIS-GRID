"""Six small synthetic live checks. No secrets, chain-of-thought or plant actions recorded."""

import asyncio
import json
from dataclasses import asdict
from pathlib import Path

from aegis_inference.client import InferenceUnavailable
from aegis_inference.token_factory import BASE_URL, EFFORT, MODEL_ORDER, TokenFactoryClient
from dev import read_env
from pydantic import SecretStr


async def main() -> None:
    key = read_env().get("INFERENCE_API_KEY")
    if not key:
        raise SystemExit("AMD key absent in ignored .env")
    rows = []
    cases = [
        ("abstention", "No incident evidence is available. Abstain.", set()),
        (
            "synthetic_sensor_disagreement",
            json.dumps(
                {
                    "observed": {"temperature_c": 38.0, "flow_kg_s": 0.005},
                    "residuals": [{"estimated_minus_sensor_c": 16.0}],
                }
            ),
            {"sensor_bias"},
        ),
    ]
    shared_failure = False
    for model in MODEL_ORDER:
        client = TokenFactoryClient(SecretStr(key), models=(model,))
        try:
            for name, evidence, expected in cases:
                try:
                    value = await client.investigate(evidence)
                    result = asdict(value)
                    result["opinion"] = value.opinion.model_dump()
                    result.update(
                        case=name,
                        status="VALIDATED",
                        expected_smoke_behavior=(
                            not value.opinion.hypotheses
                            and value.opinion.assessment == "insufficient_evidence"
                        )
                        if not expected
                        else bool(expected & set(value.opinion.hypotheses)),
                    )
                except InferenceUnavailable:
                    result = dict(
                        model_id=model,
                        case=name,
                        status="REFUSED_OR_UNAVAILABLE",
                        expected_smoke_behavior=False,
                        diagnostic=client.last_diagnostic,
                    )
                rows.append(result)
                print(json.dumps(result), flush=True)
                if client.last_diagnostic.get("http_status") in {401, 403, 429}:
                    shared_failure = True
                    break
                await asyncio.sleep(1)
        finally:
            await client.close()
        if shared_failure:
            break
    output = dict(
        base_url=BASE_URL.rstrip("/"),
        model_order=MODEL_ORDER,
        reasoning_effort=EFFORT,
        scope="At most six small sequential synthetic opinion checks; "
        "not a quality/long-context/GPU benchmark or live LangGraph acceptance",
        hardware_verified=False,
        mi300x_acceptance="BLOCKED",
        rows=rows,
    )
    Path("docs/results/amd-token-factory-smoke.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    asyncio.run(main())
