"""Install frozen host dependencies and run the full gate in clean_demo's source export."""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-prefix", default="phase12")
    prefix = parser.parse_args().evidence_prefix
    if not re.fullmatch(r"[a-z0-9-]{1,64}", prefix):
        raise ValueError("Invalid evidence prefix")
    proof = json.loads(
        (ROOT / f"docs/results/{prefix}-clean-bootstrap.json").read_text(encoding="utf-8")
    )
    project = proof["project"]
    if not re.fullmatch(r"aegis-proof-[0-9a-f]{8}", project):
        raise ValueError("Expected the explicitly created local proof project")
    directory = (ROOT / ".run" / project).resolve(strict=True)
    source = (directory / "source").resolve(strict=True)
    if not source.is_relative_to((ROOT / ".run").resolve()):
        raise ValueError("Proof path outside ignored workspace")
    environment = {**os.environ, "COMPOSE_PROJECT_NAME": project}
    compose = [
        "docker",
        "compose",
        "--project-name",
        project,
        "--env-file",
        str(source / ".env"),
        "-f",
        str(source / "infra/local/compose.yaml"),
    ]
    result = dict(
        source_tree=proof["source_tree"],
        project=project,
        scope="Actual source export, new host venv/node_modules, isolated proof DB; "
        "same OS/download/browser caches.",
    )
    uv = shutil.which("uv") or str(
        Path(sys.executable).with_name("uv.exe" if os.name == "nt" else "uv")
    )
    pnpm = shutil.which("pnpm") or "pnpm"
    log_path = ROOT / f"docs/results/{prefix}-clean-checks.txt"
    try:
        with log_path.open("w", encoding="utf-8") as log:

            def run(command: list[str], timeout: int = 900) -> None:
                subprocess.run(
                    command,
                    cwd=source,
                    env=environment,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    check=True,
                    timeout=timeout,
                )

            # Explicit exported-path manifest only; never stage generated credentials.
            manifest = directory / "source-paths"
            manifest.write_bytes(
                subprocess.check_output(
                    ["git", "ls-tree", "-rz", "--name-only", proof["source_tree"]], cwd=ROOT
                )
            )
            run(["git", "init", "--quiet"])
            run(
                [
                    "git",
                    "-c",
                    "core.autocrlf=false",
                    "add",
                    "--pathspec-from-file=" + str(manifest),
                    "--pathspec-file-nul",
                ]
            )
            run([uv, "sync", "--locked", "--python", sys.executable])
            run([pnpm, "install", "--frozen-lockfile"])
            python = str(
                source / (".venv/Scripts/python.exe" if os.name == "nt" else ".venv/bin/python")
            )
            run([python, "tools/dev.py", "start"])
            run([python, "tools/dev.py", "check"], timeout=1200)
        result.update(
            result="PASS",
            separate_venv=(source / ".venv").is_dir(),
            separate_node_modules=(source / "node_modules").is_dir(),
        )
    except (OSError, subprocess.SubprocessError) as error:
        result.update(result="FAIL", error_class=type(error).__name__)
        raise
    finally:
        subprocess.run(
            [*compose, "down"],
            cwd=source,
            env=environment,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=60,
        )
        result["cleanup"] = (
            "Only proof containers/networks stopped; all volumes and main stack retained."
        )
        (ROOT / f"docs/results/{prefix}-clean-check-proof.json").write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    main()
