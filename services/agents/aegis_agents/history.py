"""Project observed temperature history; hidden state is not diagnostic evidence."""

import math

from aegis_contracts.models import ObservedSample


def observed_window(delivered: list[ObservedSample]) -> list[ObservedSample]:
    if len(delivered) > 21:
        raise ValueError("Invalid observed history bound")
    samples: list[ObservedSample] = []
    for item in delivered:
        # Delay changes can repeat/regress sampled time. Retain only increasing observations.
        if not samples or (item.version > samples[-1].version and item.time_s > samples[-1].time_s):
            samples.append(item)
    return samples


def summarize(samples: list[ObservedSample], target: int) -> tuple[list[float], list[float | None]]:
    if len(samples) < 2 or not 0 <= target < 6:
        return [], []
    duration = samples[-1].time_s - samples[0].time_s
    slopes = [
        (samples[-1].temperatures[i] - samples[0].temperatures[i]) / duration for i in range(6)
    ]
    columns = [[sample.temperatures[i] for sample in samples] for i in range(6)]
    centered = [[value - sum(column) / len(column) for value in column] for column in columns]
    correlations = []
    for column in centered:
        denominator = math.sqrt(sum(v * v for v in column) * sum(v * v for v in centered[target]))
        correlations.append(
            max(
                -1.0,
                min(
                    1.0,
                    sum(a * b for a, b in zip(column, centered[target], strict=True)) / denominator,
                ),
            )
            if denominator > 1e-12
            else None
        )
    return slopes, correlations
