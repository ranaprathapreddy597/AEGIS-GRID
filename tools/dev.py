"""Cross-platform local startup. Never connects to a plant or cloud provider."""

import argparse
import os
import secrets
import shutil
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = [
    "docker",
    "compose",
    "--env-file",
    str(ROOT / ".env"),
    "-f",
    str(ROOT / "infra/local/compose.yaml"),
]
SECRET_NAMES = (
    "AEGIS_VIEWER_TOKEN",
    "AEGIS_SERVICE_TOKEN",
    "AEGIS_REDIS_PASSWORD",
    "AEGIS_MONGO_PASSWORD",
    "AEGIS_MONGO_WRITER_PASSWORD",
    "AEGIS_MONGO_READER_PASSWORD",
    "AEGIS_REDIS_WRITER_PASSWORD",
    "AEGIS_INGEST_TOKEN",
)


def read_env() -> dict[str, str]:
    path = ROOT / ".env"
    if not path.exists():
        return {}
    return dict(
        line.split("=", 1)
        for line in path.read_text().splitlines()
        if "=" in line and not line.startswith("#")
    )


def init_env() -> None:
    values = read_env()
    changed = False
    for name in SECRET_NAMES:
        if not values.get(name):
            values[name] = secrets.token_urlsafe(36)
            changed = True
        if len(values[name]) < 32 or not all(
            c.isascii() and (c.isalnum() or c in "-_") for c in values[name]
        ):
            raise SystemExit(f"Invalid local configuration: {name}; use 32+ URL-safe characters")
    if "AEGIS_SEED" not in values:
        values["AEGIS_SEED"] = "42"
        changed = True
    if "AEGIS_WEB_PORT" not in values:
        for candidate in (8080, 8180, 8787, 18080):
            with socket.socket() as listener:
                try:
                    listener.bind(("127.0.0.1", candidate))
                except OSError:
                    continue
            values["AEGIS_WEB_PORT"] = str(candidate)
            changed = True
            break
        else:
            raise SystemExit("No default web port available; set AEGIS_WEB_PORT in .env")
    port = os.environ.get("AEGIS_WEB_PORT", values["AEGIS_WEB_PORT"])
    if not port.isdecimal() or not 1024 <= int(port) <= 65535:
        raise SystemExit("AEGIS_WEB_PORT must be an integer in [1024, 65535]")
    if changed:
        path = ROOT / ".env"
        path.write_text(
            "# Local development only. Never commit.\n"
            + "".join(f"{key}={value}\n" for key, value in values.items())
        )
        if os.name != "nt":
            path.chmod(0o600)


def run(command: list[str], environment: dict[str, str] | None = None) -> None:
    executable = shutil.which(command[0])
    if executable is None:
        raise SystemExit(f"Required command unavailable: {command[0]}")
    subprocess.run([executable, *command[1:]], cwd=ROOT, check=True, env=environment)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", choices=["start", "stop", "status", "token", "init-env", "check"]
    )
    args = parser.parse_args()
    if args.command in {"start", "init-env"}:
        init_env()
    if args.command == "init-env":
        print("Local configuration ready; secret values not displayed.")
    elif args.command == "start":
        run([*COMPOSE, "build"])
        run([*COMPOSE, "up", "--detach", "--wait", "--wait-timeout", "180", "mongo", "redis"])
        bootstrap_names = [
            "AEGIS_MONGO_PASSWORD",
            "AEGIS_REDIS_PASSWORD",
            "AEGIS_MONGO_WRITER_PASSWORD",
            "AEGIS_MONGO_READER_PASSWORD",
            "AEGIS_REDIS_WRITER_PASSWORD",
        ]
        values = read_env()
        flags = [item for name in bootstrap_names for item in ("--env", name)]
        run(
            [
                "docker",
                "run",
                "--rm",
                "--network",
                "aegis-grid_storage",
                *flags,
                "aegis-grid-python:phase5",
                "python",
                "-m",
                "aegis_api.storage",
                "migrate",
            ],
            {**os.environ, **{name: values[name] for name in bootstrap_names}},
        )
        run([*COMPOSE, "up", "--detach", "--wait", "--wait-timeout", "180"])
        port = os.environ.get("AEGIS_WEB_PORT", read_env().get("AEGIS_WEB_PORT", "8080"))
        print(f"Local simulation ready at http://127.0.0.1:{port}")
        print("In your own terminal, run python tools/dev.py token for the viewer token.")
    elif args.command == "stop":
        run([*COMPOSE, "down"])  # Named volumes are deliberately preserved.
    elif args.command == "status":
        run([*COMPOSE, "ps"])
    elif args.command == "token":
        value = read_env().get("AEGIS_VIEWER_TOKEN")
        if not value:
            raise SystemExit("Run python tools/dev.py start first")
        print(value)  # Explicit user-only reveal command. Never run in agent logs.
    elif args.command == "check":
        for command in [
            [sys.executable, "-m", "ruff", "check", "."],
            [sys.executable, "-m", "ruff", "format", "--check", "."],
            [sys.executable, "-m", "mypy"],
            [sys.executable, "tools/export_contracts.py", "--check"],
            [sys.executable, "tools/generate_scenarios.py", "--check"],
            [sys.executable, "tools/generate_manual_corpus.py", "--check"],
            [sys.executable, "tools/check_ts_contracts.py"],
            ["pnpm", "lint"],
            ["pnpm", "typecheck"],
            ["pnpm", "build"],
            ["pnpm", "test"],
            [
                "docker",
                "build",
                "-f",
                "infra/local/python.Dockerfile",
                "--target",
                "qa",
                "-t",
                "aegis-grid-qa:phase5",
                ".",
            ],
            [
                "docker",
                "run",
                "--rm",
                "--network",
                "none",
                "aegis-grid-qa:phase5",
                "ctest",
                "--test-dir",
                "/build",
                "--output-on-failure",
            ],
            ["docker", "run", "--rm", "--network", "none", "aegis-grid-qa:phase5"],
            [sys.executable, "tools/secret_scan.py"],
            [sys.executable, "-m", "pip_audit", "--skip-editable", "--timeout", "60"],
            ["pnpm", "audit", "--audit-level", "high"],
            [sys.executable, "tools/smoke.py"],
            [sys.executable, "tools/cross_language_check.py"],
            [*COMPOSE, "exec", "-T", "api", "python", "-m", "aegis_api.storage_checks"],
            ["pnpm", "exec", "playwright", "test"],
        ]:
            print(f"CHECK: {' '.join(command)}", flush=True)
            run(command)
        print("Phase 5 checks passed.")


if __name__ == "__main__":
    main()
