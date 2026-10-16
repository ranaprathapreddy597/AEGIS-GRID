"""Isolated CPU process: C++ library + sensor-only sentinel + independent local shield."""

import argparse
import json
import sys
import time
from pathlib import Path

from aegis_contracts.models import (
    IncidentSnapshot,
    Scenario,
    SensorFrame,
    SentinelStatus,
    SupervisorFrame,
    TwinMeasurement,
)

from aegis_edge.sentinel import SafetyShield, Sentinel
from aegis_edge.twin import NativeTwin


class SupervisedTwin:
    def __init__(
        self,
        scenario: Scenario,
        library: Path,
        observe_only: bool = False,
        memory_capacity: int = 256,
    ) -> None:
        self.twin = NativeTwin(scenario, library)
        self.sentinel = Sentinel(memory_capacity, observe_only)
        self.last_status: SentinelStatus | None = None
        self.incident_snapshot: IncidentSnapshot | None = None

    def step(self, dt: float = 0.5) -> tuple[TwinMeasurement, SentinelStatus | None]:
        frame = self.twin.step(dt)
        if not frame.measurement.packet_available:
            return frame, self.last_status
        sensors = SensorFrame.from_twin(frame)
        status = self.sentinel.update(sensors)
        if status.latched and self.incident_snapshot is None:
            envelope = json.loads(self.twin.snapshot())
            self.incident_snapshot = IncidentSnapshot(
                state_version=sensors.state_version,
                payload_json=envelope["payload"],
                sha256=envelope["sha256"],
            )
        if status.latched and not self.sentinel.observe_only:
            controls = SafetyShield.emergency_controls()
            if not SafetyShield.authorize(
                controls, sensors.state_version, self.twin.current_version()
            ):
                raise RuntimeError("Independent safety shield refused local command")
            self.twin.controls(sensors.state_version, controls)
        self.last_status = status
        return frame, status

    def close(self) -> None:
        self.twin.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--library", required=True, type=Path)
    parser.add_argument("--speed", type=float, default=1)
    parser.add_argument("--memory-capacity", type=int, default=256)
    parser.add_argument("--observe-only", action="store_true")
    args = parser.parse_args()
    if not 0.5 <= args.speed <= 20:
        raise ValueError("Invalid time scale")
    supervisor = SupervisedTwin(
        Scenario.model_validate_json(args.scenario),
        args.library,
        args.observe_only,
        args.memory_capacity,
    )
    try:
        emitted_snapshot = False
        while True:
            frame, status = supervisor.step()
            if frame.measurement.packet_available and status is not None:
                snapshot = supervisor.incident_snapshot if not emitted_snapshot else None
                print(
                    SupervisorFrame(
                        frame=frame, sentinel=status, snapshot=snapshot
                    ).model_dump_json(),
                    flush=True,
                )
                emitted_snapshot = emitted_snapshot or snapshot is not None
            time.sleep(0.5 / args.speed)
    finally:
        supervisor.close()


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, OSError):
        print("Isolated supervisor stopped: invalid input or failed dependency", file=sys.stderr)
        raise SystemExit(2) from None
