"""Local, single-threaded C ABI for isolated offline rollouts; never an HTTP control API."""

import ctypes
import hashlib
import json
import os
from pathlib import Path
from typing import Self

from aegis_contracts.models import Scenario, SimulatorControls, TwinMeasurement


def scenario_from_file(directory: Path, scenario_id: str, seed: int | None = None) -> Scenario:
    # Validate before constructing a path; only the 100 packaged descriptors are selectable.
    if len(scenario_id) != 12 or not scenario_id.startswith("scenario-"):
        raise ValueError("Invalid scenario id")
    suffix = scenario_id[9:]
    if not suffix.isascii() or not suffix.isdecimal() or int(suffix) >= 100:
        raise ValueError("Unknown scenario")
    data = json.loads((directory / f"{scenario_id}.json").read_text())
    scenario = Scenario.model_validate(data["config"])
    if scenario.scenario_id != scenario_id:
        raise ValueError("Scenario identity mismatch")
    if seed is not None:
        scenario = Scenario.model_validate({**scenario.model_dump(), "seed": seed})
    return scenario


def fingerprint(scenario: Scenario) -> str:
    return hashlib.sha256(scenario.model_dump_json().encode()).hexdigest()


class NativeTwin:
    def __init__(self, scenario: Scenario, library: Path | None = None) -> None:
        path = library or Path(os.environ.get("AEGIS_TWIN_LIBRARY", "/build/libaegis_twin.so"))
        self.lib = ctypes.CDLL(str(path.resolve(strict=True)))
        self.lib.aegis_abi_version.argtypes = []
        self.lib.aegis_abi_version.restype = ctypes.c_uint
        if self.lib.aegis_abi_version() != 2:
            raise ValueError("Unsupported twin ABI")
        signatures = {
            "create": ([ctypes.c_char_p], ctypes.c_void_p),
            "destroy": ([ctypes.c_void_p], None),
            "step": ([ctypes.c_void_p, ctypes.c_double], ctypes.c_int),
            "reset": ([ctypes.c_void_p], ctypes.c_int),
            "controls": ([ctypes.c_void_p, ctypes.c_uint64, ctypes.c_char_p], ctypes.c_int),
            "restore": ([ctypes.c_void_p, ctypes.c_char_p], ctypes.c_int),
            "json": ([ctypes.c_void_p], ctypes.c_char_p),
            "snapshot": ([ctypes.c_void_p], ctypes.c_char_p),
            "error": ([ctypes.c_void_p], ctypes.c_char_p),
        }
        for name, (arguments, result) in signatures.items():
            function = getattr(self.lib, f"aegis_{name}")
            function.argtypes, function.restype = arguments, result
        self.handle = self.lib.aegis_create(scenario.model_dump_json().encode())
        if not self.handle:
            raise ValueError("Scenario rejected by native twin")

    def _check(self, result: int) -> None:
        if result != 0:
            raise ValueError("Simulator operation rejected")

    def step(self, dt: float = 0.5) -> TwinMeasurement:
        self._check(self.lib.aegis_step(self.handle, dt))
        return TwinMeasurement.model_validate_json(self.raw())

    def raw(self) -> bytes:
        data = self.lib.aegis_json(self.handle)
        if not isinstance(data, bytes):
            raise ValueError("Closed or invalid twin handle")
        return data

    def reset(self) -> None:
        self._check(self.lib.aegis_reset(self.handle))

    def controls(self, expected_version: int, controls: SimulatorControls) -> None:
        if type(expected_version) is not int or not 0 <= expected_version <= 1000000000:
            raise ValueError("Invalid version")
        self._check(
            self.lib.aegis_controls(
                self.handle, expected_version, controls.model_dump_json().encode()
            )
        )

    def snapshot(self) -> bytes:
        payload = self.lib.aegis_snapshot(self.handle)
        if not isinstance(payload, bytes):
            raise ValueError("Closed or invalid twin handle")
        return json.dumps(
            {"sha256": hashlib.sha256(payload).hexdigest(), "payload": payload.decode()}
        ).encode()

    def restore(self, snapshot: bytes) -> None:
        if len(snapshot) > 65536:
            raise ValueError("Snapshot too large")
        envelope = json.loads(snapshot)
        if (
            not isinstance(envelope, dict)
            or set(envelope) != {"sha256", "payload"}
            or not isinstance(envelope["sha256"], str)
            or not isinstance(envelope["payload"], str)
        ):
            raise ValueError("Invalid snapshot envelope")
        payload = envelope["payload"].encode()
        if b"\0" in payload or hashlib.sha256(payload).hexdigest() != envelope["sha256"]:
            raise ValueError("Snapshot integrity mismatch")
        self._check(self.lib.aegis_restore(self.handle, payload))

    def close(self) -> None:
        self.lib.aegis_destroy(self.handle)
        self.handle = None

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
