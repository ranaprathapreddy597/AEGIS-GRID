"""Explicit authenticated read/generation smoke, not a hardware attestation."""

import asyncio
import json
import os
from dataclasses import asdict

from aegis_inference.client import InferenceUnavailable, VLLMClient
from aegis_inference.token_factory import BASE_URL, TokenFactoryClient
from dev import read_env
from pydantic import SecretStr


async def main() -> None:
    values = read_env()
    values.update(
        {
            name: os.environ[name]
            for name in ["INFERENCE_BASE_URL", "INFERENCE_API_KEY"]
            if name in os.environ
        }
    )
    endpoint, key = values.get("INFERENCE_BASE_URL"), values.get("INFERENCE_API_KEY")
    if not endpoint or not key:
        print(
            json.dumps(
                {
                    "status": "BLOCKED",
                    "reason": "MI300X endpoint/access pending",
                    "live_path_verified": False,
                    "hardware_verified": False,
                }
            )
        )
        return
    if endpoint.rstrip("/") == BASE_URL.rstrip("/"):
        hosted = TokenFactoryClient(SecretStr(key))
        try:
            opinion = await hosted.investigate("No incident evidence. Abstain.")
            value = asdict(opinion)
            value["opinion"] = opinion.opinion.model_dump()
            print(
                json.dumps(
                    {
                        "status": "AMD_HOSTED_OPINION_VERIFIED",
                        "hardware_verified": False,
                        "mi300x_acceptance": "BLOCKED",
                        "result": value,
                    }
                )
            )
        except InferenceUnavailable:
            print(
                json.dumps(
                    {
                        "status": "BLOCKED",
                        "reason": "Hosted opinion unavailable or refused",
                        "hardware_verified": False,
                        "mi300x_acceptance": "BLOCKED",
                    }
                )
            )
        finally:
            await hosted.close()
        return
    client = VLLMClient(endpoint, SecretStr(key))
    try:
        result = await client.investigate("No incident evidence. Abstain.")
        print(
            json.dumps(
                {
                    "status": "SERVING_PATH_VERIFIED",
                    "hardware_verified": False,
                    "result": result.model_dump(),
                }
            )
        )
    except InferenceUnavailable:
        print(
            json.dumps(
                {
                    "status": "BLOCKED",
                    "live_path_verified": False,
                    "reason": "Inference transport/output not verified",
                }
            )
        )
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
