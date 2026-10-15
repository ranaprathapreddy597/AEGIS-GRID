# ADR 0006: Sensor-only edge detection and isolated local emergency control

Accepted 2026-10-15. Phase 3 extends the existing C++ Twin rather than adding a
second scripted plant. The edge now owns a Python supervisor child process. That
process owns one C ABI handle, the observer, bounded FAISS feature memory and the
independent emergency shield. A native crash or invalid stream ends readiness.
Cloud delivery runs separately in the parent async service and cannot submit
controls to the child. Physical I/O is absent.

`SensorFrame` allowlists time/version, temperature, noise bounds, measured ideal
flow, heat/load, coolant, pressure and measurement quality. It excludes hidden
truth, scenario identity, seed and injected fault labels. The detector accepts
only that type. Cross-boundary tests change hidden truth and labels without
changing detector input. Current flow/pressure channels are ideal simulated
instruments; this is not validated sensor calibration.

The energy observer integrates the documented cell equation with <=0.05 s steps
using measured flow/heat/coolant/neighbors. It does not continually assimilate
temperature observations, so a deceptive temperature clamp cannot erase an
accumulating residual. Three consecutive absolute residuals >2 °C, a measured or
estimated temperature >=70 °C, or temperature age >2 s trigger a latched stop.
These are synthetic development limits, not cited OEM constraints. Large gaps or
nonmonotonic input fail the isolated process closed. Observer uncertainty and
model mismatch need wider evaluation; no production detection guarantee exists.

The independent shield permits only the exact local emergency vector: pump=1,
six valves=1, six load targets=0, with matching current state version. C++ checks
the version/ranges again and enforces ramp/feeder/pressure limits. Zero targets
take priority over injected demand bursts (a real rollout test caught the missing
priority rule). The native model/snapshot revision is now v3; the function-level
C ABI stays at version 2 because its signatures did not change. Idle electrical
and heat demand remains modeled when machine load is zero.

The latch does not automatically restart loads. Restarting this isolated demo
reinitializes plant and detector together. Public operational writes remain
unavailable. This trusted emergency behavior is independent from later arbitrary
recovery proposals, which require the Phase 9 authorization pipeline. Local
`observe_only` configuration exists for disclosed regression comparisons and is
visible in telemetry; no HTTP or model output can toggle it.

FAISS `IndexFlatL2` stores at most 256 standardized 18-dimensional engineering
feature vectors by default (configurable 32–4096), with one CPU thread. The
vectors contain six temperatures, flows and residuals. Similarity is not a
diagnosis, probability or semantic text embedding. Stored labels come only from
the observer's nominal/anomaly decision. There are no unsafe pickle/index loads.
[Official FAISS introduction](https://github.com/facebookresearch/faiss/wiki/getting-started)
documents the actual add/search interface used here.

The parent retains 128 recent incident events and a separate 256-item outbox.
Overflow evicts the oldest queued item and increments a visible loss counter.
Delivery is the application-owned `aegis-edge-v1` HTTPS protocol with a separate
bearer token, validated server certificate, no redirects/environment proxy,
timeouts, bounded response, batch digest/idempotency key and complete typed ack.
An ack cannot carry commands. Failure retains events and backs off to 30 s.
Phase 4 will provide durable receiver/persistence; this phase's queue is volatile.
Default Compose has no edge internet egress. An explicit cloud-egress override
and endpoint configuration are required before live remote delivery.

Tests cover actual loopback connection refusal while safety continues; reconnect
acks are explicit HTTP test doubles. No live remote TLS/provider success is
claimed. CPU is functional; a Windows NPU device is enumerated but no accelerated
inference workload is verified. Measured memory/latency and remaining limitations
are in `docs/results/PHASE3.md`.
