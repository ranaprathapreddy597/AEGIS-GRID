# Actual scenario benchmark — 2026-10-16

Protocol frozen in docs/FINAL_VALIDATION_PLAN.md before measurement. All 100
registered development fixtures, 600 s each, dt 1 s; 90 fault-positive, 10 healthy.
Thirty distinct training seeds for the learned NumPy logistic/centroid baseline.
No truth, labels, IDs, seed, version or absolute time enter its inference features.

| Detector | TP / FP / FN / TN | Recall | Descriptive family-bootstrap 95% recall |
|---|---|---|---|
| 70 C threshold | 5 / 0 / 85 / 10 | 0.056 | 0.000–0.167 |
| Unchanged Sentinel v1 | 46 / 0 / 44 / 10 | 0.511 | 0.200–0.825 |
| Learned CPU logistic | 62 / 0 / 28 / 10 | 0.689 | 0.400–1.000 |

All three had zero false positives on only ten correlated healthy fixtures. The
precision bootstrap degenerates to [1,1] in this limited sample; this does not
establish real-world precision. Ten family clusters, only one healthy family and
shared synthetic equations sharply limit all intervals. There were no early
alarms. Diagnosis top-one: numerical 31/90, learned family centroid 52/90.

## Safety failure and explicit post-evaluation repair

The original shield retained five thermal violations out of sixteen baseline
hazard cases (scenario-030/031/032/033/035). Trips occurred at the 70 C hard bound;
bounded load ramps needed time. Raw original rows and timings remain unchanged.

Policy v2 uses a 65 C operating trip guard while the hard limit stays 70 C. The
5 C reserve is conservative synthetic engineering headroom for sampled detection
and the at-most-ten-second load ramp; it is not a proof for arbitrary initial
states, external heating, model error or plants. Maximum model input heating is
.85 * 2200 * 1.65 / 10000 = .30855 C/s before losses/coupling; the margin is not
claimed as a full coupled-system invariant. Old policy records remain readable.

A separate complete post-fix run recovered 16/16 recorded hazardous cases, with
zero remaining thermal hazards across 100 fixtures. This is regression validation
after seeing the original failures, NOT a new held-out benchmark. Sentinel fault
recall remains 46/90: 44 missed fault cases remain visible. Numerical diagnosis
is 34/90 after the guard; learned baseline is unchanged. No winning-metric claim.

Post-fix mean production 45.6791 → 30.7974 synthetic units; mean energy
1.82088 → 1.31497 kWh; mean shield downtime 193.82 s over the 600 s windows.
These figures include healthy/non-hazard cases. Costs are model quantities, not
money or measured industrial savings. The protected approval sandbox is separate.

| Fault family | Cases | Sentinel v2 alarms | Learned alarms |
|---|---|---|---|
| healthy | 10 | 0 | 0 |
| spoof | 10 | 10 | 0 |
| freeze | 10 | 10 | 2 |
| blockage | 10 | 6 | 10 |
| pump_degradation | 10 | 0 | 10 |
| demand_burst | 10 | 0 | 10 |
| measurement_delay | 10 | 10 | 10 |
| packet_loss | 10 | 0 | 0 |
| power_spike | 10 | 0 | 10 |
| deceptive_cascade | 10 | 10 | 10 |

Actual network-none, 2-CPU/512-MiB post-fix run: 34.5107 s total,
139.07 MiB peak process RSS. Sentinel p95 0.2181 ms;
learned feature+inference p95 0.0547 ms; paired native steps/s
3676.5 including evaluation Python overhead. Excludes
Docker/WSL/other processes, model training from evaluation throughput, and all GPU/NPU work.

All 512 finite random non-stop control vectors were refused by the exact-stop
shield. The full gate separately tests all 512 single-bit Ed25519 signature
mutations, real WebAuthn negatives and actual gateway/Mongo privilege denials.

Reproduction: run tools/benchmark_scenarios.py in the QA image with --network none,
--cpus 2 --memory 512m and an output bind mount. Phase 11 image/source e9b0e21
reproduces the original detector; Phase 12 source reproduces the post-fix detector.
Fixed model weights, training seeds, all evaluation rows and hashes are in JSON.
MI300X/Evolus/Pinecone/GitHub live gates remain BLOCKED.
