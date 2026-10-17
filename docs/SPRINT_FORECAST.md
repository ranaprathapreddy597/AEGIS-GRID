# Sprint predictive intelligence — PARTIAL

The working observed-only forecast fits ordinary least squares to the trailing
30 seconds of six cell temperature measurements and extrapolates 60 seconds.
It emits a thermal-limit warning at 70 C, per-cell slopes, projected temperatures,
estimated crossing time and a clearly labeled heuristic extrapolation error.
It has no execution authority. The existing independent shield is unchanged.

`aegis_agents.forecasting.forecast(list[SensorFrame])` returns `ThermalForecast`.
`ForecastRequest` and response models live in `aegis_contracts.forecasting` for
normal OpenAPI generation. Forecasting excludes hidden truth, injected fault
labels, scenario IDs and seeds. It requires six fresh independent samples spanning
ten seconds, bounds history to 121 frames, refuses stale/unavailable latest
measurements and gaps over ten seconds, and rejects unordered histories.

## Frozen evaluation and actual results

No model training or parameter selection was performed. Fixed window, horizon,
target, three new seeds and ten existing fault families were specified in the
evaluation script before the measurement. Only predictions use the sensor-only
projection. Native ground truth labels whether any cell crosses 70 C in the next
60 seconds. Windows already at 70 C are excluded: existing hazards are detection,
not a future forecasting success. All private instances run without control or
cloud access. None of the application plants, approvals or retained receipts
are reset or changed.

Actual native run: 30 episodes, 600 seconds each, ten-second evaluation stride,
1,566 eligible windows, 20 future thermal crossing positives. Raw rows, trajectory
hashes, native binary and forecast source hashes are retained in
[results/SPRINT_FORECAST.json](results/SPRINT_FORECAST.json).

| Fixed method | TP | FP | FN | TN | Coverage | Precision | Recall of all positives | Covered accuracy | Median warning lead |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Linear trend | 2 | 2 | 18 | 1,460 | 94.64% | 50.00% | 10.00% | 98.65% | 60 s |
| Current 70 C persistence | 0 | 0 | 20 | 1,492 | 96.55% | undefined | 0.00% | 98.68% | undefined |
| Current 65 C guard | 2 | 16 | 18 | 1,476 | 96.55% | 11.11% | 10.00% | 97.75% | 60 s |

The trend has fewer false-positive windows than the simple 65 C guard on this
sample, but misses 18/20 future hazards. Its false-positive rate among covered
negative windows is 0.137%; abstention is 5.36%. Accuracy is dominated by negative
windows and is not an adequate success claim. Lead time summarizes only two
true-positive windows and is not an independent incident detection result.
Overlapping windows are correlated; no confidence interval treating them as
independent observations is reported. Coverage differs by method and is included
explicitly. No parameters were changed after viewing these results.

Sensor spoofing, frozen sensors, abrupt transitions and nonlinear thermal dynamics
can defeat a short linear trend. Held-out seeds use known fault families; this
does not establish unseen-fault generalization, fault identity prediction,
pre-onset prediction or calibration on industrial telemetry. Strong forecasting
acceptance remains BLOCKED on representative external data and materially better
sensitivity. Error bands are descriptive heuristics, never safety certificates.

## Reproduction and focused verification

From the repository root, in the existing Linux runtime image with repository
mounted at `/workspace`, working directory `/workspace`, network disabled and
`PYTHONPATH=/workspace/services/agents:/workspace/services/edge:/workspace/packages/contracts/python`:

```text
python tools/evaluate_forecasting.py --library /usr/local/lib/libaegis_twin.so --output docs/results/SPRINT_FORECAST.json
```

Host focused tests: `.venv/Scripts/python.exe -m pytest tests/unit/test_forecasting.py -q`.
Five tests passed, including linear known-slope behavior, cooling, stale/short/
duplicate/out-of-order input, frozen sample deduplication and hidden-truth/input
bounds. Ruff and strict mypy are run on the new production modules. Full regression,
API/browser integration and clean-source results are recorded by the sprint gate.
