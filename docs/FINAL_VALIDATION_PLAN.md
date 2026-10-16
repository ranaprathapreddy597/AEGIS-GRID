# Frozen final validation plan — recorded before Phase 12 measurement

Evaluate all 100 preregistered synthetic scenario fixtures for 600 simulated
seconds, dt=1 s. A positive case has a nonzero injected fault mask; ten healthy
cases are negatives. This is fault presence over the window, not necessarily a
hazard or a held-out industrial sample. Also publish alarms before fault onset.

Compare the unchanged observed-temperature >=70 C baseline, the unchanged
sensor-only Sentinel on the SAME unmitigated trajectory, and a simple learned
NumPy logistic classifier. Train the latter on three distinct seeds per family
(30 new trajectories), using observed temperatures, flow, load, heat, coolant,
pressure and measurement quality only. No truth, scenario ID, fault label, seed,
version or absolute time enters the learned feature vector. Labels are permitted
only for supervised training/evaluation. Freeze threshold .5 and three consecutive
positive delivered frames before evaluation. Record coefficients/training seeds.

Report case confusion matrices, precision/recall, detection delay, actual detector
latency/RSS/throughput. Use 2,000 fixed-seed family-cluster bootstrap replicates
for descriptive 95% intervals; only ten synthetic families and one healthy family
limit interpretation. Do not treat correlated fixtures as independent plants.

Record numerical diagnose() top-one coarse cause accuracy on all 90 fault cases,
including no-detection/unsupported causes as incorrect. Acceptable labels fixed:
bias/freeze/cascade -> sensor_bias; blockage -> restricted_flow; weak pump ->
weak_pump; burst/spike -> overload; delay -> stale_measurement; packet loss ->
missing_packets. The current reasoner has no stale/missing diagnostic class;
those misses must remain visible. Learned nearest-centroid family diagnosis is
an additional explicitly simple CPU baseline, not a generative model result.

Run paired independent shield trajectories, report thermal recovery on baseline
hazardous cases, production/downtime/energy costs and failures. The protected
stationary authorization resource is separate; no hazardous incident is approved.
Finite CPU rollouts and observed sensor logic are not industrial certification.

Add bounded mutation fuzzing, malformed/hostile model outputs, source injection,
corrupted state/receipt, timeout and connector outage checks. Retain the full
existing real browser/Mongo/Redis/native/crypto gate. An administrator rolling back
the entire database remains outside local tamper detection without an anchor.

Finally export a clean source tree, start a separate local Compose project with
fresh credentials/volumes, and capture an actual 180-second browser demo. Its
passkey harness must be labeled virtual; physical/GPU/Evolus/Pinecone acceptance
and hosted CI remain blocked. Never tag a release while required gates are blocked.
