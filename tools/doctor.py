"""Sanitized local capability probe; no network provider calls or secret values."""

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

PROVIDERS = [
    "EVOLUS_API_KEY",
    "EVOLUS_BASE_URL",
    "EVOLUS_MCP_URL",
    "PINECONE_API_KEY",
    "GITHUB_TOKEN",
    "GH_TOKEN",
    "MI300X_HOST",
    "INFERENCE_BASE_URL",
    "INFERENCE_API_KEY",
    "MONGODB_URI",
    "REDIS_URL",
]


def probe(command: list[str]) -> dict:
    executable = shutil.which(command[0])
    if not executable:
        return {"available": False}
    try:
        result = subprocess.run(
            [executable, *command[1:]], capture_output=True, timeout=15, check=False
        )
        output = result.stdout.decode("utf-8", errors="replace").replace("\x00", "").strip()
        return {"available": True, "exit_code": result.returncode, "output": output[:3000]}
    except subprocess.TimeoutExpired:
        return {"available": True, "timeout": True}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = {
        "captured_at_utc": datetime.now(UTC).isoformat(),
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "provider_environment_present": {name: bool(os.getenv(name)) for name in PROVIDERS},
        "tools": {
            name: probe(command)
            for name, command in {
                "git": ["git", "--version"],
                "node": ["node", "--version"],
                "pnpm": ["pnpm", "--version"],
                "uv": ["uv", "--version"],
                "cmake": ["cmake", "--version"],
                "g++": ["g++", "--version"],
                "docker": [
                    "docker",
                    "version",
                    "--format",
                    "client={{.Client.Version}} server={{if .Server}}"
                    "{{.Server.Version}} {{.Server.Os}}{{end}}",
                ],
                "compose": ["docker", "compose", "version"],
            }.items()
        },
    }
    if os.name == "nt":
        report["hardware"] = probe(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "$osInfo=Get-CimInstance Win32_OperatingSystem; "
                "$cpuInfo=Get-CimInstance Win32_Processor; "
                "$gpuInfo=Get-CimInstance Win32_VideoController; "
                "[pscustomobject]@{OS=$osInfo.Caption; Build=$osInfo.BuildNumber; "
                "RAMGiB=[math]::Round($osInfo.TotalVisibleMemorySize/1MB,2); "
                "CPU=$cpuInfo.Name; LogicalProcessors=$cpuInfo.NumberOfLogicalProcessors; "
                "GPU=$gpuInfo.Name; Driver=$gpuInfo.DriverVersion} | ConvertTo-Json",
            ]
        )
    text = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8", newline="\n")
        print("Sanitized capability report written")
    else:
        print(text)


if __name__ == "__main__":
    main()
