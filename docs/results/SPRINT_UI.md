# Sprint live digital twin and counterfactual explorer

Actual React implementation adds six observed-flow/temperature trend cards,
per-cell operating state and synthetic limits, shared-loop pressure, timestamped
incident events and explicit observed/truth/prediction/action boundaries.
Existing live SSE and immutable citations remain the sources.

The native strategy picker uses existing actual recovery assessments. It exposes
candidate controls, sampled feasibility/counterexamples, worst temperature,
maximum downtime, mean energy and minimum modeled production. The paired future
trace remains explicitly bound to the optimizer-selected candidate; choosing a
different card does not fabricate another trajectory. No execution button or new
physical isolation/repair/restart model was introduced.

The observed-only forecast panel consumes the new generated contracts, sends
only the SensorFrame allowlist, pauses on stale/disconnected streams and labels
heuristic error bands. The recorded experiment panel shows all baselines,
limitations, artifact hashes and selected attack families. Errors remain visible.

Focused Chromium result: two new tests passed, with no skipped/unexpected/flaky
tests (19.99 seconds in retained runner result). They check actual long-window
six-cell predictions, strict request fields, WCAG 2A/2AA checks, mobile width,
native infeasible-strategy selection and no execution authority. Final source
also passes ESLint and the production Vite/TypeScript build. Full regression and
clean-source evidence are reported separately.

Screenshots: sprint-live-twin.png, sprint-intelligence.png,
sprint-command-center.png, sprint-command-center-mobile.png,
sprint-native-explorer.png. These are captures of the running software, not design
mockups. Original historical screenshots are preserved.
