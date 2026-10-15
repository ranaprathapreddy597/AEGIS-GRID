"""Sensor-only observer and an independent, closed emergency policy for synthetic twins."""

import math
import time
from collections import deque
from typing import Literal

import faiss
import numpy as np
from aegis_contracts.models import (
    AnomalyEvidence,
    MemoryMatch,
    SensorFrame,
    SentinelStatus,
    SimulatorControls,
)
from numpy.typing import NDArray


class PhysicsObserver:
    def __init__(self) -> None:
        self.previous: SensorFrame | None = None
        self.estimated: list[float] = []
        self.bad_count = [0] * 6
        self.first_detection: float | None = None

    def update(self, frame: SensorFrame) -> list[AnomalyEvidence]:
        previous = self.previous
        if previous is None:
            self.estimated = [c.temperature_c for c in frame.cells]
        else:
            dt = frame.simulation_time_s - previous.simulation_time_s
            if frame.state_version <= previous.state_version or not 0 < dt <= 5:
                raise ValueError("Nonmonotonic or excessively gapped sensor stream")
            # Open-loop energy observer driven only by allowlisted sensor channels.
            # Do not feed corrected observations back in: a spoof must not reset the residual.
            steps = max(1, math.ceil(dt / 0.05))
            step = dt / steps
            for _ in range(steps):
                updated = []
                for i, cell in enumerate(previous.cells):
                    q = cell.flow_kg_s
                    flow_capacity = q * 4180
                    ua = 120 * (q / 0.3) ** 0.8
                    h = -flow_capacity * math.expm1(-ua / flow_capacity) if q else 0.0
                    estimate = self.estimated[i]
                    coupling = 8 * (
                        previous.cells[(i + 5) % 6].temperature_c
                        + previous.cells[(i + 1) % 6].temperature_c
                        - 2 * estimate
                    )
                    heat = cell.heat_input_w - h * (estimate - previous.coolant_temperature_c)
                    heat += coupling - 6 * (estimate - 22)
                    updated.append(estimate + step * heat / 10000)
                self.estimated = updated
        self.previous = frame
        evidence = []
        for i, cell in enumerate(frame.cells):
            residual = self.estimated[i] - cell.temperature_c
            self.bad_count[i] = self.bad_count[i] + 1 if abs(residual) > 2.0 else 0
            reason: (
                Literal[
                    "physics_disagreement", "thermal_limit", "stale_measurement", "missing_packets"
                ]
                | None
            ) = None
            if frame.measurement.age_s > 2:
                reason = "stale_measurement"
            elif self.bad_count[i] >= 3:
                reason = "physics_disagreement"
            elif max(cell.temperature_c, self.estimated[i]) >= 70:
                reason = "thermal_limit"
            if reason is not None:
                evidence.append(
                    AnomalyEvidence(
                        cell_id=cell.cell_id,
                        residual_c=residual,
                        estimated_temperature_c=self.estimated[i],
                        observed_temperature_c=cell.temperature_c,
                        reason=reason,
                    )
                )
        if evidence and self.first_detection is None:
            self.first_detection = frame.simulation_time_s
        return evidence


class LocalMemory:
    """Bounded FAISS flat index of standardized engineering features, not text embeddings."""

    def __init__(self, capacity: int = 256) -> None:
        if not 32 <= capacity <= 4096:
            raise ValueError("Memory capacity outside [32,4096]")
        faiss.omp_set_num_threads(1)
        self.rows: deque[tuple[int, Literal["nominal", "sensor_anomaly"], NDArray[np.float32]]] = (
            deque(maxlen=capacity)
        )
        self.index = faiss.IndexFlatL2(18)

    @staticmethod
    def features(frame: SensorFrame, estimates: list[float]) -> NDArray[np.float32]:
        return np.asarray(
            [c.temperature_c / 100 for c in frame.cells]
            + [c.flow_kg_s / 0.5 for c in frame.cells]
            + [(e - c.temperature_c) / 10 for e, c in zip(estimates, frame.cells, strict=True)],
            dtype=np.float32,
        ).reshape(1, 18)

    def lookup(self, vector: NDArray[np.float32]) -> list[MemoryMatch]:
        if not self.rows:
            return []
        distances, indexes = self.index.search(vector, min(3, len(self.rows)))
        rows = list(self.rows)
        return [
            MemoryMatch(
                state_version=rows[int(index)][0],
                label=rows[int(index)][1],
                distance_squared=max(0.0, float(distance)),
            )
            for distance, index in zip(distances[0], indexes[0], strict=True)
        ]

    def add(self, frame: SensorFrame, vector: NDArray[np.float32], anomaly: bool) -> None:
        self.rows.append(
            (frame.state_version, "sensor_anomaly" if anomaly else "nominal", vector.copy())
        )
        # At most 4096 x 18 floats; rebuilding avoids unbounded tombstones or ID reuse.
        self.index.reset()
        self.index.add(np.concatenate([row[2] for row in self.rows], axis=0))


class SafetyShield:
    """Independent allowlist. This phase can only stop loads and maximize cooling."""

    @staticmethod
    def emergency_controls() -> SimulatorControls:
        return SimulatorControls(pump=1.0, loads=[0.0] * 6, valves=[1.0] * 6)

    @staticmethod
    def authorize(proposed: SimulatorControls, expected_version: int, actual_version: int) -> bool:
        return (
            type(expected_version) is int
            and expected_version >= 1
            and expected_version == actual_version
            and proposed == SafetyShield.emergency_controls()
        )


class Sentinel:
    def __init__(self, memory_capacity: int = 256, observe_only: bool = False) -> None:
        self.observer = PhysicsObserver()
        self.memory = LocalMemory(memory_capacity)
        self.observe_only = observe_only
        self.latched = False
        self.last_memory_time = -10.0
        self.max_estimate = 0.0

    def update(self, sensors: SensorFrame) -> SentinelStatus:
        started = time.perf_counter_ns()
        evidence = self.observer.update(sensors)
        self.latched = self.latched or bool(evidence)
        self.max_estimate = max(self.max_estimate, *self.observer.estimated)
        vector = self.memory.features(sensors, self.observer.estimated)
        matches = self.memory.lookup(vector)
        if sensors.simulation_time_s - self.last_memory_time >= 10:
            self.memory.add(sensors, vector, bool(evidence))
            self.last_memory_time = sensors.simulation_time_s
        state: Literal["warming", "nominal", "anomaly", "latched_stop"] = (
            "latched_stop"
            if self.latched and not self.observe_only
            else "anomaly"
            if evidence
            else "nominal"
        )
        if sensors.simulation_time_s < 5 and not evidence:
            state = "warming"
        return SentinelStatus(
            state=state,
            evidence=evidence,
            latched=self.latched,
            first_detection_time_s=self.observer.first_detection,
            applied_policy="observe_only"
            if self.observe_only
            else "local_emergency_stop"
            if self.latched
            else "none",
            latency_ms=(time.perf_counter_ns() - started) / 1e6,
            max_estimated_temperature_c=self.max_estimate,
            memory_entries=len(self.memory.rows),
            memory_matches=matches,
        )
