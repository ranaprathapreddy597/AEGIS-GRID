# AEGIS//GRID 2.0 — 12 PHASE-BY-PHASE BUILD PROMPTS

**Workflow**: Paste `AEGIS_GRID_MASTER_PROMPT.md` first as a persistent coding-agent instruction. Then paste **only the next phase prompt** into the same agent/repository session, in order. If the agent stops, use the *continuation prompt* below, not 'start over'. Demand real source changes, commands and evidence every phase. Commit after each passing phase. Timeframes are not promises. Never share secrets in the chat or commit them.

## Phase 1 — Repo discovery, technical design, skeleton and golden path

> Follow the AEGIS//GRID master constitution. Inspect the current repo/OS/toolchains/hardware and report verified vs unavailable external integrations. Create the proposed monorepo, pinned dependency managers, CMake/CTest, FastAPI, Node/TypeScript, React/TypeScript, Compose for Redis/Mongo, configuration schemas, contract generation, test runners, GitHub Actions CI, security baseline and architecture ADRs. Implement the FIRST live vertical slice: deterministic simulator emits one telemetry measurement through the edge service, the API streams it, and React renders the actual value. Include one-command local startup, health endpoints and contract/unit/integration smoke tests. Run checks and fix them. Do not pretend AMD Cloud or Evolus is connected without evidence. Finish with a precise status table and commit.

**Gate:** A new clone can start the minimal stack and see real changing simulator data, with tests green.

## Phase 2 — C++ industrial digital twin and fault universe

> Build a real deterministic C++20 six-cell factory model with documented differential/step equations, pressure/temperature/load/coolant physics, invariants and bounded actuators. Expose a narrow API to Python through a C ABI, pybind11 or local RPC; justify the choice. Add scenario descriptors and fault injection: spoofed/stuck sensors, blockage, pump degradation, cascading heat, power spikes, delayed measurements and dropped packets. Implement snapshots, seeded reset, time scaling, hidden physical ground truth and observed readings. Create 100 labeled deterministic scenario fixtures, physics unit and property tests, performance profiling on 32GB-class hardware, and a visible live integration in React. Run all checks and commit.

**Gate:** Same seed => same physical and observed traces; fault can deceive naive thresholds; invariants are tested.

## Phase 3 — Ryzen sentinel, FAISS memory and cloud-outage survival

> Implement a Python FastAPI edge process, typed telemetry and incident events, lightweight anomaly detection using thermal-flow physics residuals and sensor cross-validation, configurable edge FAISS lookup, bounded ring/event buffer, and independent deterministic safety shield/controller. Provide secure cloud communication client with authentication/TLS and reconnect/queue semantics. Verify it fits 32GB host RAM; optional AMD NPU integration ONLY after capability probing, with functional CPU fallback. Add cloud-disconnection test, sensor-spoof challenge, safety refusal tests and measured edge detection latency. Integrate into golden path, run checks and commit.

**Gate:** Edge detects a planted deceptive anomaly while cloud is unreachable and never executes forbidden commands.

## Phase 4 — Event-sourced state and enterprise backend

> Implement the platform FastAPI APIs and canonical Pydantic/JSON Schema contracts; generate TypeScript clients. Set up Redis event streams and MongoDB incidents, plan/action/audit collections, indexes and migrations; include retention/redaction policy, versioned snapshots, idempotency and typed errors. Add WebSockets/SSE for live telemetry; reliable incident tracing and reproducibility fingerprints. Separate restricted append-only telemetry records from approval-gated operational writes. Build cross-language C++/Python/Node/React contract tests, authenticated API boundaries and load tests. Run and commit.

**Gate:** An incident persists and replays through a process restart; contracts remain synchronized.

## Phase 5 — Real Evolus extractor adapter and manual reasoning corpus

> Investigate the actual Evolus Document Extractors provider docs/SDK or supplied sandbox. Record only verified routes/schema/auth limits; do NOT invent an API. Implement an adapter and separate honest test fake; resumable batch extraction from a ~1,000-page-equivalent PDF/corpus with page fingerprints, citations, units, revision consistency, table mapping and strict JSON/Pydantic validation. Implement OEM safety-constraint, procedure, interlock and contradiction schemas, FAISS local and Pinecone cloud indexing, prompt-injection isolation and evidence retrieval scores. Run an integration test with the real provider only if credentials are available, otherwise mark blocked and show contract tests. Prove an intentionally contradictory bulletin causes a no-action decision. Run checks and commit.

**Gate:** Every actionable OEM constraint has a verifiable page/revision citation; contradictions block unsupported writes.

## Phase 6 — MI300X ROCm/vLLM deployment and long-context proof

> Build tested cloud deployment manifests/scripts for MI300X ROCm 7.0 and vLLM, respecting observed compatibility. Select a legitimately available long-context model; record actual architecture/context metadata. Implement a Python model-serving client and real authenticated laptop-to-cloud request/response pathway. Produce a memory budget calculator for weights, BF16/FP8 KV, batching, context and runtime reserve; show 80 GiB failure for a precisely defined unquantized configuration and feasible 192GB deployment only if actual model/runtime behavior supports it. Collect real device telemetry, version numbers, prefill/decode throughput and peak HBM at 8K/32K/128K/200K+ as supported. Provide local development backend with clearly labeled simulation. Never fabricate GPU timings, driver versions, or true 200K success. Run and commit.

**Gate:** Live MI300X connection and logs when access exists, otherwise reproducible deployment scripts and an explicit blocked gate, not a false pass.

## Phase 7 — Cyclic LangGraph forensic AI and evidence memory

> Build a persistent typed LangGraph graph with Sentinel trigger, Evidence Collector, Causal Detective, OEM Manual Expert, Cascade Forecaster, Blue Planner, Red Examiner, Simulation Referee, deterministic Safety Shield, Approval interrupt, Executor and Verifier/Reporter. Make transitions genuinely cyclic according to new evidence, adversarial failures and simulation feedback; cap loops and token budgets. Model input/output is structured validated data; unsafe/untrusted sources cannot inject policies. Wire Mongo persistence, FAISS/Pinecone retrieval and actual MI300X inference adapter (with labeled offline dev backend). Add fixtures proving diagnoses distinguish sensor spoofing from real thermal faults. Instrument traces, cost, latency and errors. Run checks and commit.

**Gate:** One seeded incident completes investigation through candidate plans without touching a protected mutation endpoint.

## Phase 8 — Red-vs-Blue search, robust optimization and future timelines

> Implement genuine constrained recovery search (robust MPC, enumerative scenario selection or similarly justified algorithm) and adversarial counterexample generation; NEVER substitute an LLM opinion for simulation. Enumerate candidate controls, enforce thermal/flow/pressure/ramp constraints, simulate uncertain hidden states, and rank feasible plans by risk, downtime, lost production, energy and equipment wear. Reject a deliberately planted unsafe plan; produce certified/checked C++ rollout artifacts and paired unmitigated/intervention timelines with seeds and quantitative metrics. Test optimizer consistency, search coverage and out-of-distribution abstention. Integrate artifacts into API. Run and commit.

**Gate:** Real physics rollouts demonstrably beat baseline on some cases; hard constraints always take precedence.

## Phase 9 — WebAuthn HITL and independent action authorization

> Implement full React Ask First UI + FastAPI backend WebAuthn enrollment/verification with verified origin/RP ID/challenge and user verification. Canonicalize and hash immutable proposed actions; bind the random challenge to the digest server-side and use expiring one-time approval; persist LangGraph interrupt/resume. Build separate Node/TS executor verifying scoped signed capability, expected plant-state/database version, independent safety policies, replays, tamper evidence, idempotency and compensating actions. Test real browser/passkey interaction where available, plus CI test harness clearly labeled. Include forced failures: no approval, modified plan, nonce reuse, expired challenge, wrong user, stale plant, safety override and interrupted transaction. Run security checks, commit.

**Gate:** No unapproved operational database/remote GitHub action or simulated plant mutation is reachable through any public endpoint.

## Phase 10 — Evolus MCP execution, GitHub repair engineer and receipts

> Discover and implement verified Evolus MCP connector interfaces; do not assume non-existent tools. Create a deny-by-default allowlisted integration gateway that applies signed authorized commands only after Phase 9 passes. Integrate a true guarded operational Mongo mutation and simulator command, plus an approved GitHub repair branch/commit/PR workflow (through Evolus MCP only if actually supported; otherwise transparently use a direct verified connector). AI may generate a local patch/test suite before approval, but remote writes occur only after approval; code changes must be reviewed/diffed and CI must be required. Provide idempotent receipts, compensations, audit and tests for partial failure. Distinguish provider live sandbox from simulator fake. Run checks and commit.

**Gate:** At least one real scoped enterprise write path is proven if authorized credentials exist; all unapproved paths deny.

## Phase 11 — Exceptional polished React command center

> Build the complete accessible React + TypeScript command center: immersive factory digital twin with performant 2D fallback; topology, thermal/flow overlays and spoof-vs-truth view; realtime fault injection panel; edge/cloud connectivity badge and NPU status if detected; causal evidence graph with OEM citations; Red/Blue plan tournament; 10K-futures histogram/failure cases; side-by-side timelines; economics, plan action diff and live passkey approval; MCP/GitHub tool receipts; reproducible incident replay; offline mode and mobile layout. Use the actual APIs, not static sample data outside a labeled demo tutorial. Make every clickable element meaningful and handle loading, errors, auth, rate limit and reconnection. Add Playwright E2E and UI accessibility tests, use production-quality visual design, run all checks and commit.

**Gate:** The full seeded incident can be operated through the UI without using a developer console.

## Phase 12 — Red-team hardening, benchmarks, actual demo and submission

> Perform end-to-end threat modeling, dangerous instruction injection tests in PDF and model output, supply-chain/dependency scans, credential auditing, approval bypass fuzzing, chaos testing (cloud outage, stale state, corrupted sensor, tool timeout, DB rollback, connector outage), and benchmark 100+ labeled scenarios against naive threshold detection and a simple AI baseline. Measure detection precision/recall, diagnosis correctness, unsafe action blocks, recovery success, downtime, costs, latency, memory, throughput and uncertainty; report **actual** numbers with reproducible commands and confidence intervals. Build a 3-minute demo runner with exact event cues and seed reset, screenshots/capture from real running software, README installation paths (local simulated and true MI300X), architecture/security diagrams, results report, 1-minute pitch, 3-minute narration, judge FAQ and product/economic story. Validate honest AMD and Evolus usage evidence, fix P0 bugs, run the entire CI suite, and provide a release checklist. Commit and tag a release only when gates pass.

**Gate:** A fresh environment reproduces the three-minute live demo and tests; any missing cloud/provider access is called out as a release blocker rather than concealed.

---

## Reusable continuation prompt (when an agent runs out of context)

> Read `AGENTS.md`, the AEGIS master constitution, `docs/PROGRESS.md`, `docs/OPEN_ISSUES.md`, `docs/INTEGRATION_EVIDENCE.md`, and the latest commit; inspect test results. Identify the currently assigned numbered phase and remaining acceptance gates. Continue from the last verified working commit, without rewriting completed modules or declaring blocked integration successful. Implement the next smallest real vertical slice; run the appropriate unit/integration/security tests; fix failures; update docs and commit. Report changed files, commands, actual results, blockers and next step. Never output pseudocode in place of required source code.

## Final audit prompt (only after Phase 12)

> Act as an independent hostile hackathon judge and external red-team assessor. Attempt to disprove every claim in README, demo, architecture, hardware memory justification and Evolus integration. Find dead controls, fake telemetry, unverified vendor endpoints, unmeasured GPU statements, security bypasses, nondeterminism, data leakage, unclear hardware usage, unrealistic benchmark claims and polished-but-nonfunctional UI. Produce a severity-ranked, file/line-specific defect report; repair all P0/P1 issues that are fixable with available access; rerun all tests. Reevaluate the actual end-to-end 3-minute demo from a clean install. Present an honest scoreboard of Verified, Simulated, Blocked and Not Implemented capabilities. Do not assert victory, guarantee prizes, or invent evidence.

## Recommended collaboration protocol

Use **one persistent repository** with version control, not 12 new disconnected agent chats. Use master prompt as the policy and phases as work orders. At every phase, insist on: (1) exact files changed, (2) executed commands, (3) test summaries, (4) proof/evidence, (5) one Git commit, (6) unresolved blocker log. You can run separate isolated specialists in branches but merge only after contract tests. Prefer working vertical slices and clean architecture over a giant untested first response.
