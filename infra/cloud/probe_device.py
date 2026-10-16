"""Read-only observed runtime/device collector; emits failures as failures."""

import json
import platform
import subprocess
from importlib.metadata import PackageNotFoundError, version


def main() -> None:
    report: dict[str, object] = {"platform": platform.platform(), "hardware_verified": False}
    for package in ["torch", "vllm", "transformers"]:
        try:
            report[package] = version(package)
        except PackageNotFoundError:
            report[package] = None
    for name, command in [
        ("rocm_smi", ["rocm-smi", "--showproductname", "--showmeminfo", "vram", "--json"]),
        ("rocminfo", ["rocminfo"]),
    ]:
        try:
            result = subprocess.run(  # noqa: S603 - fixed read-only GPU command allowlist
                command, capture_output=True, text=True, timeout=20, check=False
            )
            report[name] = {"exit_code": result.returncode, "stdout": result.stdout[:65536]}
        except (OSError, subprocess.TimeoutExpired):
            report[name] = {"unavailable": True}
    try:
        import torch

        devices = [
            {
                "name": torch.cuda.get_device_name(i),
                "total_memory_bytes": torch.cuda.get_device_properties(i).total_memory,
                "allocated_bytes": torch.cuda.memory_allocated(i),
                "reserved_bytes": torch.cuda.memory_reserved(i),
            }
            for i in range(torch.cuda.device_count())
        ]
        report["devices"] = devices
        report["hip_version"] = torch.version.hip
        report["hardware_verified"] = bool(
            devices and torch.version.hip and all("MI300X" in device["name"] for device in devices)
        )
    except (ImportError, RuntimeError):
        report["devices"] = []
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
