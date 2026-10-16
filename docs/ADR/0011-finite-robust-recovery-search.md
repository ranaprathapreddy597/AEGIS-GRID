# ADR 0011: finite minimax search and native counterfactual artifacts

Accepted 2026-10-16. Phase 7 local gate passed at e3251d0. External live gates
remain BLOCKED; the user authorized continued local Phases 8–12.

Use enumerative minimax selection rather than a model's safety opinion. Blue
enumerates ten uniform control vectors: loads 0/.25/.5/.75/1 crossed with pump
.7/1, all valves open. An eleventh deliberately unsafe vector runs full loads,
pump zero and closed valves. Red evaluates each against the actual snapshot and
36 explicit adversarial priors: six branch targets × severity .5/.8/1 × initial
temperature offsets -2/+2 °C, with blockage, weak pump, burst and power faults.
Every prior includes a complete native state, PRNG seed and snapshot hash. The
priors are model-informed assumptions, not diagnosed fault labels or samples
from a learned posterior. Physical truth never enters the diagnostic model input.

The additive C ABI `aegis_rollout` operates on a private Twin copy. It performs
600 one-second frames with twenty 0.05-second physics substeps each, preserving
normal step/observation/PRNG semantics. Bounds are checked at the initial state
and each substep: temperature strictly below 70 °C, pressure at most 180 kPa,
feeder at most 14,500 W. Productive branch flow must be at least .02 kg/s after
ten elapsed seconds of settling; a stopped branch need not have productive flow.
The time interval allows the documented 0.1/s load ramp to complete from load 1.
Pump/load/valve ramps are independently measured against .12/.10/.20 per second;
the kernel implements them at every substep. Violation bits: thermal 1, flow 2,
pressure 4, feeder 8, ramp 16. Invalid input never mutates the source handle.

Feasibility across **all 37 cases** precedes cost ranking. Minimize worst-case
assumed dimensionless cost: 5×lost synthetic production units + .05×downtime
seconds + .25×kWh + .1×actuator travel + 10×normalized thermal risk. Maximum
production reference is horizon/10 units; thermal risk is
`(max(0,peak-40)/30)^2`. These are disclosed experimental weights, not money or
customer economics. Severe full blockage can make stop the only robust feasible
choice; production loss is reported rather than hidden. Ties use candidate ID.

Source cells outside 20–60 °C, coolant outside 20–45 °C, or insufficient remaining
native time horizon cause explicit abstention without made-up trajectories. This
is a narrow domain check and finite coverage, not a proof for arbitrary unknown
faults, parameter/model error, real plants or continuous controls. No calibration
or robust statistical confidence claim. A hot initial state can never be excused
by a later cooling trajectory. Unresolved manual evidence still blocks execution.

Artifacts include every prior's seed/state hash, control vectors, per-candidate
worst metrics/failure count, up to three counterexamples per candidate, objective
weights, policy, model/native binary hash, source snapshot hash, actual rollout
and substep counts, and paired baseline/intervention sampled timelines. Canonical
sorted finite JSON hashes the complete validated report excluding its own hash.
This is an integrity-checked reproducible artifact, **not a cryptographic approval
or industrial safety certification**. Time/RSS measurements live outside this
deterministic payload. Same native binary/state/algorithm yields identical bytes.

Store reports under content hashes in a separate `analysis_artifacts` collection,
30-day retention. Graph identity has find/insert only there, and still cannot
write operational plans/actions/audit. No mutation authority is issued. The API
admits one analysis worker at a time, caps artifacts and returns persisted results;
no ephemeral success fallback. Native handles are confined to that worker thread.
API crashes may lose an uncommitted computation; safe deterministic retries redo
the analysis. This local single-worker admission is not a distributed job system.

LangGraph now uses the actual minimax result: planted unsafe proposal → Red native
counterexamples → optimal checked candidate → independent latched-stop challenge
→ conservative emergency vector. A physically feasible lower-pump optimum still
cannot override the edge's exact maximum-cooling stop policy. The full-corpus
manual contradiction prevents authorization regardless of the numerical result.
The read-only React table and timelines display real persisted calculations.
Phase 9 must independently verify immutable actions, WebAuthn and capabilities
before adding any protected execution path.
