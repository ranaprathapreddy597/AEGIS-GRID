# Coupled factory model v2

This is a synthetic six-cell factory for software experiments. Constants below
are design assumptions, not OEM limits or a calibrated plant. No physical I/O,
boiling, cavitation, coolant leakage, hydraulic inertia, motor transients or
temperature-dependent material properties are modeled. Thermal values can exceed
normal operating temperatures without the model asserting safe operation.

The energy-balance and convection approach follows the principles described in
[DOE heat-transfer training](https://www.energy.gov/ehss/articles/doe-hdbk-10122-92).
The pump/system intersection follows the pressure/flow relationship explained by
[Grundfos](https://www.grundfos.com/ie/learn/research-and-insights/pump-curves).
Neither source supplies or validates this model's numerical constants.

## State, units and equations

For cell i: temperature T_i (°C), load l_i and valve v_i (fractions). The reservoir
temperature is T_c; ambient T_a=22 °C. Each cell has C_i=10,000 J/K; reservoir
C_c=20 kg × 4,180 J/(kg K)=83,600 J/K. Six cells form a thermal ring. Initial
temperatures are 25+U(seed) °C; coolant 25 °C; load 0.65+0.04i; valves 1; pump 0.85;
pressure 0 kPa. The initial-state snapshot for each fixture is in the profile JSON.

Hydraulic equations (mass flow q in kg/s, differential pressure p in kPa):

```
k_i = v_i (1 - blockage_i) / sqrt(800)
S = sum(k_i)
p_target = 180 (pump * efficiency)^2 / (1 + 12 S^2)
q_i = k_i sqrt(p)
Q = sum(q_i)
```

The algebraic intersection uses `p = 180 (pump*efficiency)^2 - 12 Q^2`.
Pressure slews toward that intersection at at most 20 kPa/s. Thus during slew,
pressure is a bounded lag approximation, not the instantaneous pump-curve solution.
All branch outflow returns to the mixed reservoir: total mass is constant.
`p<=180` and `S<=6/sqrt(800)` imply `Q<=2.847 kg/s` (contract bound 3 kg/s).

```
P_pump = 350 pump^3 / efficiency
P_request_i = (200 + 2000 l_i) * spike_multiplier
served = min(1, (14500 - P_pump) / sum(P_request_i))
P_heat_i = 0.85 * served * P_request_i
P_feeder = P_pump + sum(served * P_request_i)
UA_i = 120 (q_i / 0.3)^0.8
h_i = q_i cp * (1 - exp(-UA_i / (q_i cp)))  [zero when q_i=0]
H_i = h_i (T_i - T_c)
C_i dT_i/dt = P_heat_i - H_i - 6(T_i-T_a)
              + 8(T_previous + T_next - 2T_i)
C_c dT_c/dt = sum(H_i) + P_pump - 700(T_c-T_a)
```

The heat-exchanger form ensures an inferred branch return temperature
`T_c + H_i/(q_i cp)` lies between inlet coolant and cell temperature. Mixing is
represented by the summed heat flux into the finite reservoir. Pump electrical
power is assumed to end as coolant heat. The remaining 15% of machine power is
unmodeled work/loss outside the tracked thermal system. Production integrates
`sum(served*l_i)/60` synthetic units/s; energy integrates feeder W over seconds.

The thermal-energy check uses `E=C_c*T_c+sum(C_i*T_i)`. Internal coolant exchange
and symmetric ring exchange cancel exactly algebraically. The accumulated
residual is the numerical difference between ΔE and the integral of machine heat
+ pump heat − radiator heat − cell ambient losses, measured in joules.

## Integration and controls

`step(dt)` accepts finite `0<dt<=1` s and divides it into equal simultaneous
forward-Euler substeps no larger than 0.05 s. Maximum nominal cell heat-transfer
time constants are tens of seconds, so this is conservative for these coefficients.
CTest compares 0.05 s internal steps with 0.025 s, requiring <0.01 °C difference
after 100 s. This is a tested numerical envelope, not general solver certification.
Simulation horizon is limited to 1,000,000 s / 1 billion frames.

Local C ABI controls atomically validate six loads, six valves, pump in [0,1]
and expected state version before changing targets. Pump/load/valve ramp limits
are 0.12/0.10/0.20 fraction/s. The feeder clips delivered machine demand to keep
total power <=14,500 W. These are model constraints, not the Phase 3 safety shield.
There is no HTTP route to reset, restore, inject faults or change controls.

CLI `--speed` scales wall-clock sleep only, not simulated dt or equations.
The edge exposes configuration `AEGIS_TIME_SCALE` in [0.5,20]. Actual wall speed
also includes scheduling/serialization overhead and is not a real-time guarantee.

## Fault and measurement semantics

Fault onset is evaluated at each internal substep's start; boundary quantization
is <=0.05 s. Measurement faults are evaluated at the completed step. Bit masks:

| Bit | Injected effect |
|---|---|
| 1 | Target temperature sensor clamps its underlying signal to at most 38 °C |
| 2 | Target temperature freezes at first fault-active sample, before instrument noise |
| 4 | Target branch conductance falls by `0.98*severity` |
| 8 | Hydraulic efficiency becomes `1-0.55*severity`; raises pump input heat |
| 16 | Load request adds `0.25*severity` for 30 of every 60 seconds, capped at 1 |
| 32 | Temperature vector delivered from up to 20 previous output steps |
| 64 | Every Nth fault-active frame is omitted by the actual CLI transport |
| 128 | Machine electrical requests multiply by `1+0.65*severity` for 10 of 30 seconds |

Mask 157 combines spoofing, blockage, weak pump, burst load and power spikes.
Heat propagation emerges through ring coupling and the common coolant reservoir;
there is no scripted neighbor-temperature animation. Ten families × ten seeds
form 100 labeled fixtures. Severity and target also vary. Labels are injected
causes, not diagnosis outcomes. They are development fixtures, not independent
held-out clinical/industrial or detector benchmark data.

Temperature observations add deterministic uniform noise in ±noise_bound_c.
The implied interval `[reading-noise_bound_c, reading+noise_bound_c]` covers only
instrument noise around the assumed signal; spoofing, freezing and delay can put
current truth outside it. No statistical confidence or full state uncertainty
claim is made. Load and heat input are current ideal simulator channels, even
when temperatures are delayed. `measurement` labels temperature age and source
version. Flow/pressure/coolant are ideal simulator state, labeled accordingly.

`ground_truth` and `injected_fault_mask` are privileged *simulation inspection*
fields shown only as such in the UI; future detectors must not consume them as
sensor evidence. The separate observation vector can deceive a naive threshold.
The current authenticated dashboard permits local developer truth inspection;
this is not a production data-separation or tenant boundary.

## Determinism and snapshots

Unsigned xorshift64, initialized to seed+1, produces bounded uniform doubles.
Physics is deterministic given seed, scenario, exact dt sequence and controls.
Noise consumes the same sequence on every output step, including dropped packets.
Same-build replay is byte-identical; cross-platform/libm bit identity is not claimed.

The narrow C ABI (version 2) shares the CLI's Twin implementation. Python ctypes
copies handle-owned strings. Each context-managed handle is single-thread owned;
no callbacks or network/physical operations exist. nlohmann/json 3.11.2 serializes
round-trip double values and parses snapshots. Snapshots contain all physical,
actuator, PRNG, freeze, delay-history, packet-counter, version/time and integral
state. Restore validates into a temporary instance and replaces the live instance
only after validation. Invalid ranges/shape/order and oversized input fail.

Python snapshot envelopes include SHA-256 for accidental corruption detection.
This is not authentication: a local caller can recompute the hash. The ABI is
trusted in-process code, not a hostile pointer sandbox or approval gateway.
Scenario fingerprints cover Pydantic-ordered compact JSON; binary/library hashes
identify the executing build. Live `AEGIS_SEED` overrides the selected descriptor
seed explicitly and is included in the fingerprint. Offline fixture evaluation
uses each descriptor's registered seed. Live run UUID/time are intentionally not
part of deterministic physical trajectories.

`tools/profile_twin.py` executes and replays all 100 scenarios for 1,200 seconds,
stores whole-trajectory SHA-256, initial snapshots and every tenth-second raw
observed/truth frame in `phase2-trajectories.ndjson.gz`. This archive includes
offline frames whose packet_available is false; live CLI correctly omits them.
The report specifies timing scope, process RSS and host limitations.
