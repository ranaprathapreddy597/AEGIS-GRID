# ADR 0005: Coupled twin with a narrow C ABI

Status: accepted, 2026-10-15. See `docs/results/PHASE2.md` for execution evidence.

Retain the edge-owned C++ subprocess for live process isolation. Add a versioned C
ABI over the same Twin class for Python offline stepping, snapshots, reset, actuator
validation and measured scenario evaluation. ctypes needs no new compiler-specific
Python extension package. Exceptions cannot cross the C boundary; errors are copied
through an explicit last-error function. Each handle is single-thread owned.

All physics/fault/PRNG/delay state lives in C++, including snapshot state. Python
validates scenario descriptors and fingerprints their canonical content. No HTTP
mutation API is added. Local process configuration selects a preregistered scenario;
the C ABI is a simulator-only library, not a physical I/O adapter or authorization
mechanism. Production command execution remains unavailable until its later gate.

Use conservative simultaneous thermal updates with bounded internal substeps,
an algebraic pump/system curve with pressure slew, branch conductance, finite
coolant heat capacity, radiator heat removal, symmetric ring thermal coupling,
and a shared feeder power budget. Defaults are synthetic and all units explicit.
Conservation, step refinement and physical/ramp bounds must be tested. Fault labels
describe injected causes; they are not a trained diagnostic model's predictions.
