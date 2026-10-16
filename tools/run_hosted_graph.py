"""Run live acceptance in the built native simulator image, passing secrets by environment."""

import os
import subprocess
import sys
from pathlib import Path

from dev import ROOT, read_env


def main() -> None:
    values = read_env()
    names = ["INFERENCE_API_KEY", "PINECONE_API_KEY", "PINECONE_INDEX_HOST"]
    environment = {**os.environ, **{name: values[name] for name in names}}
    model_cache = Path.home() / ".cache/huggingface/hub/models--minishlab--potion-base-8M"
    command = ["docker", "run", "--rm", "--network", "bridge", "--memory", "768m", "--cpus", "2"]
    for name in names:
        command += ["--env", name]
    command += [
        "--env",
        "HF_HUB_CACHE=/models",
        "--env",
        "HF_HUB_OFFLINE=1",
        "--volume",
        str(model_cache) + ":/models/models--minishlab--potion-base-8M:ro",
        "--volume",
        str(ROOT / "tools") + ":/app/tools:ro",
        "--volume",
        str(ROOT / "docs/results") + ":/app/docs/results",
        "aegis-grid-python:phase12",
        "python",
        "tools/live_knowledge.py",
        "graph",
    ]
    result = subprocess.run(command, cwd=ROOT, env=environment, check=False, timeout=240)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
