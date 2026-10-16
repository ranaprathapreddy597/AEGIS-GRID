"""Render only. Does not pull an image, provision a GPU or deploy a service."""

import json
import os
import subprocess

from dev import ROOT


def main() -> None:
    result = subprocess.run(
        [
            "docker",
            "compose",
            "-f",
            "infra/cloud/mi300x.compose.yaml",
            "config",
            "--format",
            "json",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
        env={
            **os.environ,
            "INFERENCE_API_KEY": "manifest-render-fixture-only-" * 3,
            "AEGIS_CONTEXT_TOKENS": "8192",
            "AEGIS_CONCURRENT_SEQUENCES": "1",
        },
    )
    service = json.loads(result.stdout)["services"]["inference"]
    if (
        "@sha256:" not in service["image"]
        or service.get("privileged")
        or service["ports"][0]["host_ip"] != "127.0.0.1"
        or any("docker.sock" in mount.get("source", "") for mount in service["volumes"])
        or service["entrypoint"] != ["python3", "/opt/aegis/serve.py"]
    ):
        raise SystemExit("Cloud manifest safety/immutability checks failed")
    print(
        json.dumps(
            {
                "result": "PASS",
                "scope": "Compose render and policy only",
                "image_pulled": False,
                "device_verified": False,
                "deployed": False,
            }
        )
    )


if __name__ == "__main__":
    main()
