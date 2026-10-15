# ADR 0003: Read-only NDJSON subprocess and SSE

Status: accepted, 2026-10-14.

The first slice needs a small, inspectable C++→Python boundary without introducing
ABI or wheel compatibility issues. The edge owns a child simulator whose stdout
is one bounded JSON frame per line. It cannot issue actuator commands.

Strict schema validation, sequence checking, timeout, process ownership and binary
fingerprinting make this boundary executable and traceable. The API streams SSE to
a fetch-based React consumer so bearer tokens stay out of URLs and browser storage.
Use generated TypeScript types, not manually mirrored payload definitions.

At most 120 browser frames and one edge frame are retained. API per-viewer polling
is intentionally small-scale; Redis fanout/backpressure and durable replay belong
to Phase 4. Phase 2 may retain local RPC or replace it with a justified C ABI.
