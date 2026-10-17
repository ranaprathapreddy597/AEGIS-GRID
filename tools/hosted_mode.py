"""Explicit local application mode control; never uploads knowledge or resets provider quota."""

import argparse
import os
import subprocess
from pathlib import Path

from dev import COMPOSE, ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["hosted", "offline"])
    args = parser.parse_args()
    command = [*COMPOSE]
    environment = dict(os.environ)
    if args.mode == "hosted":
        cache = Path.home() / ".cache/huggingface"
        if not cache.is_dir() or not (ROOT / ".run/cloud-knowledge/synthetic.jsonl").is_file():
            raise SystemExit("BLOCKED: frozen model cache and pinned read-only snapshots required")
        environment["AEGIS_MODEL_CACHE"] = cache.as_posix()
        command += ["-f", str(ROOT / "infra/local/compose.hosted.yaml")]
    subprocess.run(
        [*command, "up", "-d", "--wait", "--wait-timeout", "120", "api", "web"],
        cwd=ROOT,
        env=environment,
        check=True,
        timeout=180,
    )
    print("Application mode configured: " + args.mode)


if __name__ == "__main__":
    main()
