"""Export the staged source and run the actual demo in a new local Compose project."""

import json
import os
import shutil
import socket
import subprocess
import sys
import tarfile
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    identifier = "aegis-proof-" + uuid4().hex[:8]
    directory = ROOT / ".run" / identifier
    source = directory / "source"
    source.mkdir(parents=True)
    tree = subprocess.check_output(["git", "write-tree"], cwd=ROOT, text=True).strip()
    archive = directory / "source.tar"
    subprocess.run(["git", "archive", tree, "-o", str(archive)], cwd=ROOT, check=True)
    with tarfile.open(archive) as bundle:
        bundle.extractall(source, filter="data")
    assert not (source / ".env").exists()  # noqa: S101 - executable proof assertion.
    assert not (source / "node_modules").exists()  # noqa: S101
    assert not (source / ".venv").exists()  # noqa: S101
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    (source / ".env").write_text(f"AEGIS_WEB_PORT={port}\n", encoding="utf-8")
    environment = {**os.environ, "COMPOSE_PROJECT_NAME": identifier}
    compose = [
        "docker",
        "compose",
        "--project-name",
        identifier,
        "--env-file",
        str(source / ".env"),
        "-f",
        str(source / "infra/local/compose.yaml"),
    ]
    started = time.perf_counter()
    report = dict(
        source_tree=tree,
        project=identifier,
        port=port,
        source_copy_initially_has_credentials=False,
        source_copy_has_venv=False,
        source_copy_has_node_modules=False,
        limitation="Same host Docker/layer/download caches and host Playwright tooling reused; "
        "not a cold machine or GPU/provider proof.",
    )
    try:
        with (directory / "startup.txt").open("w", encoding="utf-8") as log:
            subprocess.run(
                [sys.executable, "tools/dev.py", "start"],
                cwd=source,
                env=environment,
                stdout=log,
                stderr=subprocess.STDOUT,
                check=True,
                timeout=900,
            )
        report["startup_wall_s"] = time.perf_counter() - started
        with urlopen(f"http://localhost:{port}/healthz", timeout=5) as response:  # noqa: S310 - fixed loopback.
            report["frontend_http"] = response.status
        try:
            urlopen(f"http://localhost:{port}/api/v1/telemetry/latest", timeout=5)  # noqa: S310
            raise RuntimeError("Anonymous read unexpectedly succeeded")
        except HTTPError as error:
            if error.code != 401:
                raise
            report["anonymous_read_http"] = error.code
        with (directory / "demo.txt").open("w", encoding="utf-8") as log:
            subprocess.run(
                [
                    shutil.which("pnpm") or "pnpm",
                    "exec",
                    "node",
                    "tools/run_demo.mjs",
                    "--workspace",
                    str(source),
                    "--output",
                    str(ROOT / "docs/results/phase12-demo"),
                ],
                cwd=ROOT,
                stdout=log,
                stderr=subprocess.STDOUT,
                check=True,
                timeout=240,
            )
        proof = json.loads(
            (ROOT / "docs/results/phase12-demo/proof.json").read_text(encoding="utf-8")
        )
        if proof["result"] != "PASS" or proof["duration_s"] < 180:
            raise RuntimeError("Actual complete demo proof required")
        report.update(
            result="PASS",
            demo_duration_s=proof["duration_s"],
            actual_demo_receipt_sha256=proof["receipt"]["receipt_sha256"],
        )
    except (subprocess.SubprocessError, OSError, ValueError, RuntimeError) as error:
        report.update(
            result="FAIL",
            error_class=type(error).__name__,
            detail="See ignored local startup/demo logs; secrets intentionally omitted.",
        )
        raise
    finally:
        subprocess.run(
            [*compose, "down"],
            cwd=source,
            env=environment,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=60,
        )
        report["cleanup"] = (
            "Only new proof project's containers/networks stopped; volumes and main stack retained."
        )
        (ROOT / "docs/results/phase12-clean-bootstrap.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    main()
