# Architecture and current boundary

Phase 2 implements the read-only local path below. The master constitution
remains the target architecture for later phases.

```mermaid
flowchart LR
  C[C++20 thermal kernel] -->|bounded NDJSON stdout| E[Python edge]
  E -->|service bearer token / validated JSON| A[FastAPI]
  A -->|viewer bearer token / SSE| N[loopback nginx]
  N --> R[React]
  X[Node executor: deny all mutations]
  M[(Mongo: isolated infrastructure)]
  D[(Redis: isolated infrastructure)]
```

## Process and trust boundaries

- Edge is the sole owner of one simulator child process. It starts from a fixed
  seed, validates every frame, requires increasing versions with exactly accounted packet drops and the selected seed,
  keeps only the latest frame, and gives each process run a UUID plus binary and effective-scenario SHA-256.
- The bootstrap integration uses a narrow subprocess/NDJSON interface. It cannot
  send commands to the twin. Child timeout/exit or invalid output disables readiness.
- API polls the authenticated latest-frame endpoint at 2 Hz per viewer and emits
  SSE. There are at most eight streams. Live state is not durable; offline snapshots are explicit local artifacts.
- API has a global 60-token read bucket with one token/second refill. Browser
  status becomes stale after 3.5 seconds without a frame; edge freshness expires
  after three seconds. Invalid/cloud data cannot create substitute measurements.
- The browser talks only to nginx on the selected loopback port (saved in `.env`).
  Nginx joins an ingress bridge plus the internal app network; API/edge/executor have no
  published host ports. Backend tokens are absent from the JavaScript bundle.
- Redis/Mongo are on a separate internal network, without app connections or host
  ports. Their admin bootstrap credentials are never passed to API/edge/executor.
- The executor is a typed Node process with a health endpoint and explicit denials.
  It has no database, GitHub, physical-device or cloud clients.

## Coupled physics and offline rollouts

The same C++ Twin class powers the live subprocess and a versioned C ABI used
through Python ctypes for local experiments. Six cells share coolant, pump and
feeder dynamics, with bounded actuators, seeded sensor/process/transport faults,
reset and complete state snapshots. See [equations and limits](PHYSICS.md).
No HTTP mutation endpoint exposes the ABI. Ground truth is a simulator inspection
field, not an input for future production detectors.

## Contracts

Pydantic is the source for strict JSON schemas and API OpenAPI. Unknown fields,
duplicate/missing cells, coerced integer strings, nonfinite floats, invalid source
labels, and out-of-range values fail validation. TypeScript declarations are
generated with openapi-typescript and consumed by React and the Node service.
The read-only Phase 2 contracts are not final command/approval schemas.

## Later architecture

Phase 3 adds deterministic safety and FAISS.
Phase 4 adds Redis streams, Mongo events, replay, retention and tenant boundaries.
Phases 5–10 add evidence, MI300X inference, LangGraph, robust planning, WebAuthn and
independent capability-checked execution. Phase 11 extends this dashboard; Phase 12
audits the entire product and measured demo. These are planned, not implemented.
