# Phase 7 report — 2026-10-16, Asia/Calcutta

Status: local gate PASS. MI300X, Evolus and Pinecone live gates BLOCKED.
Phase 6 accepted at `7dfe7e4`; preceding documentation commit `f120696`.

Implemented real typed LangGraph cycles, Mongo checkpoints with separate scoped
identity, safe JSON checkpoint codec, sensor-only diagnosis/model inputs, FAISS
manual evidence, actual C++ baseline/candidate forecasts, independent shield,
durable approval interrupt, authenticated analysis/replay API and React inspector.
No public resume or execution operation is enabled. The local inference backend
is explicitly an offline abstention template; physics reasoners are actual code.
No generative LLM/GPU accuracy or live provider capability is claimed.

Changed groups: `services/agents`, canonical `investigation.py` contracts/generated
schemas, edge incident observation capture, API routes/storage migration,
configuration/Compose/startup, React investigation panel and tests. ADR 0010
documents trust boundaries, TTL/serializer choices and exact limits.

Executed:

```powershell
.venv/Scripts/python tools/dev.py start
.venv/Scripts/python tools/dev.py check
.venv/Scripts/python -m pytest -q tests/unit/test_graph_security.py
```

The first full run passed 206 checks and exposed alphabetical hypothesis ranking;
support-score ordering was repaired. An earlier TS build caught possibly empty
array indexing; the UI now displays the actual maximum proposed load. Both are
real resolved findings; final gate results are recorded in `phase7-checks.txt`.

An actual authenticated HTTP request already completed a persisted investigation
(`phase7-live-investigation.json`): two cycles, first candidate rejected, second
retained for review, real 120-second baseline peak 55.688 degC versus zero-load
candidate peak 40.952 degC. It pauses because the manual bulletin is contradictory.
These are one seeded model-informed simulator case, not robust recovery proof or
physical outcomes. Actual traces record local node timings; tokens used zero,
cost null, provider live gates blocked, operational_write_allowed false.

Final gate: **208 Python / 3 CTest / 9 Chromium / 2 Node tests passed**.
Types/lints, generated contract drift, fixture drift, cloud manifest rendering,
secret/dependency audits, actual HTTP/SSE and cross-language checks passed.
Actual scoped storage tests denied six monitoring operations and three graph
writes to protected collections. Browser proof includes delivered-history samples,
two real cycles, durable interrupt, identical idempotent retry and report equality
after an actual API restart. The earlier overheat browser timeout is retained in
phase7-browser-timeout.txt; focused rerun passed unchanged and this final full
suite passed the same test in 31.7 seconds. No threshold or timeout was weakened.

Next ordered phase is 8 after this local phase commit. No release tag, external
write or deployment; all three provider live gates remain BLOCKED.
