"""Small deterministic thermal forecaster. Never reads simulator truth or fault labels."""

import math
from statistics import mean, median

from aegis_contracts.forecasting import CellForecast, ThermalForecast
from aegis_contracts.models import SensorFrame

HORIZON_S = 60
WINDOW_S = 30.0
LIMIT_C = 70


def forecast(history: list[SensorFrame]) -> ThermalForecast:
    """Fit trailing observations only; no trained parameters or future samples."""
    if not 1 <= len(history) <= 121:
        raise ValueError("Forecast requires 1..121 ordered observations")
    for before, after in zip(history, history[1:], strict=False):
        if (
            after.state_version <= before.state_version
            or after.simulation_time_s <= before.simulation_time_s
        ):
            raise ValueError("Forecast history must be strictly ordered")
    latest = history[-1]
    usable = [
        frame
        for frame in history
        if frame.measurement.packet_available
        and frame.measurement.age_s <= 5.0
        and latest.simulation_time_s - frame.measurement.sampled_time_s <= WINDOW_S
    ]
    # Delayed or frozen samples are not independent observations.
    unique = {frame.measurement.sampled_time_s: frame for frame in usable}
    samples = sorted(unique.values(), key=lambda item: item.measurement.sampled_time_s)

    def abstain(reason: str) -> ThermalForecast:
        return ThermalForecast(
            status="abstained",
            reason=reason,
            observation_count=len(samples),
            cells=[],
            warning=False,
        )

    if not latest.measurement.packet_available or latest.measurement.age_s > 5.0:
        return abstain("Latest observation unavailable or stale")
    if len(samples) < 6:
        return abstain("Need six fresh independent samples spanning at least ten seconds")
    times = [sample.measurement.sampled_time_s for sample in samples]
    if times[-1] - times[0] < 10.0:
        return abstain("Observation window too short")
    if any(b - a > 10 for a, b in zip(times, times[1:], strict=False)):
        return abstain("Observation gap exceeds ten seconds")
    center = mean(times)
    variance = sum((time - center) ** 2 for time in times)
    median_flow = median(c.flow_kg_s for c in latest.cells)
    cells = []
    for index, cell in enumerate(latest.cells):
        values = [sample.cells[index].temperature_c for sample in samples]
        average = mean(values)
        slope = sum((t - center) * (v - average) for t, v in zip(times, values, strict=True))
        slope /= variance
        residual = math.sqrt(
            mean(
                [
                    (v - average - slope * (t - center)) ** 2
                    for t, v in zip(times, values, strict=True)
                ]
            )
        )
        # Extrapolation to the present includes measurement delay; never hide it as a new reading.
        projected = cell.temperature_c + slope * (HORIZON_S + latest.measurement.age_s)
        error = 2 * (residual + cell.noise_bound_c) * (1 + HORIZON_S / (times[-1] - times[0]))
        crossing = (LIMIT_C - cell.temperature_c) / slope if slope > 0 else None
        if cell.temperature_c >= LIMIT_C:
            crossing = 0.0
        warning = cell.temperature_c >= LIMIT_C or (slope > 0 and projected >= LIMIT_C)

        # Physics-based energy balance check for choked/uncooled branches
        # with corrupted or spoofed sensors.
        if not warning and median_flow > 0.05 and cell.flow_kg_s < 0.25 * median_flow:
            q = cell.flow_kg_s
            c_flow = q * 4180
            ua = 120 * (q / 0.3) ** 0.8 if q > 0 else 0.0
            h = -c_flow * math.expm1(-ua / c_flow) if q > 0 else 0.0
            q_loss_limit = h * (LIMIT_C - latest.coolant_temperature_c) + 6.0 * (LIMIT_C - 22.0)
            net_heat_at_limit = cell.heat_input_w - q_loss_limit
            if net_heat_at_limit > 200.0:
                dt_net = (net_heat_at_limit - 150.0) / 10000.0
                peer_temps = [
                    c.temperature_c
                    for idx, c in enumerate(latest.cells)
                    if idx != index and c.flow_kg_s >= 0.5 * median_flow
                ]
                baseline_temp = max(peer_temps) if peer_temps else 28.0
                choked_sec = sum(
                    1
                    for f in history
                    if f.cells[index].flow_kg_s < 0.05 and f.cells[index].heat_input_w > 500
                )
                est_temp = baseline_temp + (choked_sec * dt_net)
                est_crossing = (LIMIT_C - est_temp) / dt_net if dt_net > 0 else 999.0
                if (
                    (est_temp - cell.temperature_c > 5.0)
                    and est_temp >= 64.5
                    and 0.0 <= est_crossing <= HORIZON_S
                ):
                    warning = True
                    projected = max(projected, est_temp + dt_net * HORIZON_S)
                    crossing = min(crossing, est_crossing) if crossing is not None else est_crossing

        cells.append(
            CellForecast(
                cell_id=cell.cell_id,
                observed_temperature_c=cell.temperature_c,
                slope_c_per_s=slope,
                projected_temperature_c=projected,
                extrapolation_error_c=error,
                crossing_in_s=max(0.0, crossing - latest.measurement.age_s)
                if crossing is not None
                else None,
                warning=warning,
            )
        )
    return ThermalForecast(
        status="available",
        reason="Trailing observed temperature trend; fixed 60 second horizon",
        observation_count=len(samples),
        cells=cells,
        warning=any(cell.warning for cell in cells),
    )
