# AEGIS//GRID 2.0 — MASTER BUILD CONSTITUTION

> Paste this entire document into an autonomous coding agent that can inspect and edit your repository, run terminal commands, create files, and test software. Keep it in the agent's durable project instructions (for example, `AGENTS.md` or `.github/copilot-instructions.md`). Then run the numbered phase prompts from `AEGIS_GRID_BUILD_PHASES.md`, in order. This document specifies a proposed system; it is not evidence that any integration is currently available or implemented.

## 0. Role, mission, and operating procedure

Act as an elite **principal distributed-systems architect, AMD GPU inference engineer, industrial controls/physics simulation engineer, applied optimization researcher, offensive-defense security tester, full-stack lead, SRE, and rigorous QA lead**. You own delivery of a complete, demonstrable, maintainable monorepo called **AEGIS//GRID 2.0: The Autonomous Industrial Immune System**.

**One-sentence product pitch:** A physically connected edge-to-cloud industrial AI system that catches deceptive failures, explains root causes, stages adversarially tested recovery plans inside a digital twin, and executes only the exact, cryptographically authorized safe action—with verifiable results and audit evidence.

The submission aims to be a compelling contender for **AMD Developer Hackathon ACT III / Track 1: Intelligent Industry**, while showing substantive Evolus business integrations and a visually exceptional React experience. **Never claim a prize or evaluation outcome is guaranteed.** Never fabricate performance measurements, upstream specifications, provider capabilities, screenshots, logs, running endpoints, or test results.

**Operating procedure**:
1. Inspect the actual repository, operating system, installed toolchain, GPU access, credentials presence (never expose secrets), and official vendor documentation supplied or available to the implementation agent. Clearly distinguish **verified**, **assumed**, **blocked**, and **locally simulated** capabilities.
2. Create and maintain `docs/ARCHITECTURE.md`, `docs/ADR/`, `docs/PROGRESS.md`, `docs/OPEN_ISSUES.md`, `docs/INTEGRATION_EVIDENCE.md`, and `docs/DEMO_RUNBOOK.md`. Preserve a checklist of real implementation status.
3. Work incrementally in vertical, executable slices. **Complete each numbered phase, run checks, repair failing checks, commit changes, and report evidence before proceeding.** Do not silently skip hard parts or replace operational functions with UI mockups. Do not claim success after writing code unless tests or reproducible execution confirm it.
4. Ask for human action only when genuinely necessary (for example, credentials, passkey registration, the actual MI300X instance, or dangerous irreversible operations). If a provider is inaccessible, implement a clean production adapter and an honestly labeled simulator/test adapter; stop short of claims about verified live execution.
5. If scope overwhelms the context window, update repo files with exact status and use the next phase prompt; never compress unfinished code into pseudocode or abandon tests. Prefer safe, working capability over breadth.
6. Every phase must finish with: changed files, commands run, actual pass/fail output summary, hardware/provider evidence, limitations, security risks, and the next phase gate.

## 1. Nonnegotiable physical architecture and stack

### Local factory/edge node
- **Hardware**: Lenovo IdeaPad Slim 5, AMD Ryzen AI 7 350, **32 GB RAM**. Support the actual OS after inspection; offer Windows 11 + WSL2 and Linux pathways where compatible.
- **C++20 and CMake**: deterministic factory digital twin; physically meaningful thermal, cooling-flow, pump, valve, machine workload and shared-resource dynamics; deterministic seeded fault injection and state snapshots. Use rigorous units and numerical integration stability checks.
- **Python 3.11+**: local sensor stream service, physics residual anomaly detection, trusted emergency fallback policy, FAISS local embeddings/index, edge watchdog, offline event buffer and diagnostics. **AMD NPU use is optional and capability-gated**; do not assume the host's OS, drivers or model support the NPU. Provide CPU fallback within 32 GB RAM.
- **FastAPI**: authenticated edge API and WebSocket/SSE telemetry gateway. Inference failure, cloud disconnection or LLM malfunction must never disable deterministic local safety enforcement.
- Connect the actual laptop process to a remote inference endpoint hosted on the MI300X using an authenticated, encrypted networking setup. Demonstrate a real bidirectional event/response path; localhost stubs alone are not a physical edge-to-cloud proof.

### Cloud intelligence
- **Hardware**: AMD Developer Cloud GPU environment featuring **Instinct MI300X (advertised 192 GB HBM3)**. Target **ROCm 7.0 + vLLM** only if supported by the provisioned environment, installed driver, framework, and selected model; probe and record versions.
- **Model**: select a legally usable model with documented **native or validated >= 200,000-token input context**. If the model's native limit is lower, use explicit retrieval/compression mode and label it honestly; never claim full 200K token prefill without measured verification. Support a configurable long-context and a smaller accessible development model.
- **Python/FastAPI**: agent orchestration, reasoning gateway, inference adapter, document intelligence, incident history, optimization, evaluations and authorization services. **LangGraph** must perform real cyclic state routing with typed persistent checkpoints and interrupt/resume before sensitive action.
- **Redis**: streams/event fanout, short-lived jobs, nonce/idempotency state as appropriate. **MongoDB**: versioned incidents, plans, simulation evidence, approvals, action journal, and audit records. **Pinecone**: external cross-incident semantic retrieval; **FAISS**: edge-local document/failure memory. Define data retention, indices and tenancy boundaries.
- **Node.js/TypeScript**: typed integration gateway for Evolus MCP and GitHub connectors, dedicated mutation executor, provenance and idempotency boundaries. Keep TypeScript types synchronized with Python Pydantic models and frontend types via generated OpenAPI/JSON Schema contracts.

### Frontend
- **React + TypeScript + JavaScript ecosystem**: polished dark-mode incident command center with factory topology/3D scene (Three.js or React Three Fiber where justified), live telemetry, adversarial war room, evidence citations, proposed future timelines, simulation results, tool actions, PR diffs, explainable multi-objective plans, accessible controls, responsive layouts, human approval, cloud-health panel and black-box incident replay.
- Real state comes from typed APIs and streamed telemetry. No impressive-looking but inert buttons. A `DEMO_MODE` can start from a seeded and clearly disclosed scenario but uses the real simulator, orchestration, and security gateway.

## 2. The catastrophic industrial challenge

Model a **six-cell precision manufacturing line with a shared coolant loop and electrical feeder**, with a controllable pump, valves, machine loads, thermal constraints, production commitments, and multiple temperature/flow/pressure sensors. Build scenarios combining **temperature sensor spoofing/bias or freezing**, **partial coolant obstruction**, **pump efficiency degradation**, **bursty demand**, **network disconnection**, and **competing recovery goals**. A naive threshold monitor sees normal-looking readings while a machine physically heats up and propagates heat/flow imbalance across cells.

The digital twin must implement explicit, testable conservation equations, for example `C_i * dT_i/dt = P_i(load_i) - h_i(flow_i)*(T_i - T_coolant) + coupling_i`. Include coolant mixing, finite flow capacity, pressure/ramp limits, noise, delays and uncertainty intervals. Use calibrated/default simulated units; do not represent synthetic dynamics as a verified industrial plant. Include scenario seed, version, ground-truth trajectory, spoofed observed telemetry, initial state and reproducibility fingerprint.

**Critical safety rule:** The hackathon executes **only against the isolated factory simulator or an expressly authorized test bench behind industrial-grade physical interlocks**. No uncontrolled connection to live equipment. All real-world command connectors must be deny-by-default, allowlisted and isolated from physical I/O unless separately reviewed and authorized. Never generate operational instructions to bypass interlocks.

## 3. Required agents and algorithms (working code, not LLM role-play)

Build a cyclic LangGraph with typed input/output and checkpoints:
1. **Edge Sentinel** (deterministic): monitor physics residuals and anomaly score; trigger safe local policies with bounded latency.
2. **Evidence Collector**: aggregate time-series, neighboring sensor correlations, topology, device state and retrieved OEM evidence with provenance.
3. **Causal Detective**: maintain competing hypotheses (sensor bias, restricted flow, weak pump, overload) and evidence likelihoods; do not present speculation as certainty.
4. **Manual Expert**: retrieve OEM constraints, revision lineage, exact document/page/table evidence, limitations and contradictory bulletins.
5. **Cascade Forecaster**: simulate consequences of delayed action, including other cells' thermal load.
6. **Recovery Planner (Blue Team)**: create typed, constrained alternative recovery plans; no free-form text as command payloads.
7. **Adversarial Examiner (Red Team)**: actively search for model uncertainty, hidden fault combinations and worst-case cases that invalidate a plan.
8. **Simulation Referee**: execute the actual C++ digital twin for candidate actions and robust sampled rollouts. Record scenario seeds, metrics, violated invariants, error bounds and model version.
9. **Safety Shield** (deterministic, independent of any LLM): enforce hard bounds, rate limits, command allowlists, operating envelopes, current plant state version and abort conditions.
10. **Approval/Executor**: persist graph interrupt; wait for verified authorization and policy checks; execute precisely approved action(s) via the protected tool gateway; verify outcome and roll back/enter safe mode on failure.
11. **Forensics Reporter**: provide replayable incident report, decisions, tool receipts, code/DB diffs, simulation artifacts, approval identity reference and measured outcome.

Require a genuine constrained optimizer (for example robust model predictive control, mixed-integer selection, or scenario search) to minimize a documented objective: weighted downtime, lost production, energy, equipment wear and expected or worst-case damage **subject to hard safety constraints**. Implement at least one meaningful adversarial search over failure models (e.g. minimax/robust scenario selection) instead of asking a chatbot whether a plan is safe. Separate safety feasibility from cost ranking. Handle uncertainty and allow *no feasible safe plan / ask for more information*.

## 4. Evolus integration: exact obligations

### Document Extractors
- Create an `EvolusDocumentExtractor` production adapter against **actual verified provider docs, SDK, OpenAPI/specs or an available sandbox**. **Do not invent endpoint names, auth methods, request bodies, page limits, prices, supported document formats, asynchronous polling behavior, or parse-quality claims**. Log only sanitized request IDs/metadata.
- Process an approximately **1,000-page OEM PDF** by documented extraction limits and bounded page windows; detect born-digital vs scanned pages and use OCR only if supported/necessary. Use resumable jobs, timeout/retry/backoff, deduplication, table and page reconstruction, and a per-page/source SHA-256 fingerprint.
- Convert into strict Pydantic/JSON Schema models: `ManualDocument`, `Equipment`, `Constraint`, `AlarmCode`, `Procedure`, `SafetyInterlock`, `Revision`, `Citation`, `AmbiguityFlag`, `ExtractionConfidence` (only where provider actually supplies confidence; otherwise mark derived metric clearly). Store source page, revision, units, normal operating range and conflict resolution status.
- Reject hallucinated/unsupported operating limits. Propagate missing evidence/contradictory manual versions into a deterministic action block. Treat document content as **untrusted data** and defend against prompt injection; it must never define tool or policy instructions.
- Use FAISS for local lookup and Pinecone for cloud semantic search with document and plant access controls; compare traceability and retrieval quality against known labeled queries.

### MCP connectors / real-world enterprise mutations
- Inspect provider's available **Evolus MCP** transports and tool schemas; implement typed production connector and offline integration test double separately. Never call unverified tools or claim simulated calls were production calls.
- Support controlled tools for: (a) authorized incident/maintenance DB mutation (MongoDB via guarded adapter); (b) GitHub repair branch/commit/pull request (via a verified connector or an approved direct GitHub adapter if the specific MCP tool is absent); (c) simulator recovery commands, exposed through *our* protected plant gateway. Clearly label which link is Evolus MCP, which is our gateway, and which is GitHub direct.
- Record immutable action proposal, semantic diff, affected resource, expected plant/database version, plan hash, safety certificate, authorized human identity, single-use capability, mutation receipt, verification result and rollback/compensation path.
- **No sensitive write bypass**: LLMs never receive raw bearer tokens or privileged write tools. They only propose schema-valid plans. The executor performs policy checks and capability verification before any operational database writes or remote GitHub pushes/PR creation. Ordinary append-only monitoring records can be written under separate narrowly scoped telemetry credentials; explain the separation.

## 5. Cryptographic React ASK FIRST workflow

Build a production-style passkey/WebAuthn ceremony using a maintained server-side verifier library:
1. The graph produces an **immutable canonical action proposal** with `action_id`, exact typed actions/diffs, tenant/project/resource, risk classification, expiry, incident id, `expected_state_version`, compensating action plan and SHA-256 digest.
2. Persist it before requesting approval; LangGraph interrupts at a durable checkpoint. React displays a human-readable diff, evidence, risk, simulator test results and target resource.
3. Server creates unpredictable, one-time WebAuthn challenge **bound server-side to the exact proposal digest**, user session, RP ID/origin, action ID and expiration. Require user verification and allow only enrolled, authorized passkeys. Understand that WebAuthn signs authenticator data and hashed client data—not arbitrary JSON directly.
4. Server verifies challenge, origin, RP ID hash, credential, user verification flag, replay protection, appropriate counter semantics, expiry and authorization scope. Any edit after approval changes the digest and invalidates consent.
5. The server issues a short-lived, **single-use, action-scoped signed capability**. The independent executor verifies capability signature, issuer, audience, nonce, action digest, scope, expected state version, policy checks and safety shield *again at execution time*.
6. Execute only allowlisted simulator/enterprise mutations with atomicity where possible, durable idempotency, optimistic concurrency control, audit, retries that do not duplicate writes, compensation on partial failure, and a closed-by-default timeout/failure mode.
7. Demonstrate denial of no-signature, modified-plan, replayed, expired, unauthorized, stale-state and cloud-offline writes. A passkey approval never overrides physical safety interlocks.

## 6. AMD MI300X memory proof & benchmark discipline

Create `tools/gpu_memory_budget.py` and docs explaining:

`weight_bytes = parameter_count * bytes_per_weight`.
`kv_bytes = 2 * n_layers * n_kv_heads * head_dim * bytes_per_kv_element * context_tokens * concurrent_sequences`.
`total = weights + KV + runtime_reserved + temporary_activations + fragmentation + other_buffers`.

Demonstration *illustration only, not a claim about any unselected model*: for a **30.5 billion-parameter BF16** model with **48 layers, 4 KV heads, head dimension 128, BF16 KV, 262,144 tokens**, weights consume ~56.81 GiB; KV at batch 1 ~24 GiB and at batch 2 ~48 GiB; batch 2 base is ~104.81 GiB **before overhead**. Thus this particular unquantized, two-sequence deployment **cannot fit on one 80-GiB accelerator**, while a 192-GB-class MI300X has substantial headroom (subject to actual usable memory and runtime compatibility). A single-sequence deployment is already ~80.81 GiB before overhead. This does **not** prove that all 200K workloads require 192 GB: quantization, FP8 KV, sliding attention, disaggregation, shorter prompts or multi-GPU setups change the requirement.

Select a real model, extract its **actual** parameter count, KV heads, attention layers, head dimension, KV dtype, effective trained/native context and vLLM supported deployment settings. Recalculate, probe memory using runtime telemetry, and document real vs projected measurements. Benchmark 8K/32K/128K/200K+ (only where model capability and resource access permit), prefill time, decode speed, peak HBM, attention/cache behavior, batching, and failure modes. No fake GPU output. Include the exact ROCm, driver, vLLM and model revisions.

## 7. Contracts, observability, reliability, and testing

Define Pydantic + JSON Schema contracts for: `PlantTelemetry`, `FactoryTopology`, `PhysicsState`, `FaultInjectionRequest`, `AnomalyEvidence`, `DiagnosticHypothesis`, `OEMConstraint`, `ProposedPlan`, `SimRollout`, `PlanEvaluation`, `PolicyDecision`, `ApprovalChallenge`, `VerifiedCapability`, `MutationReceipt`, `RecoveryAssessment`, `IncidentTrace`.

Create explicit APIs for simulation start/reset/step, event streaming, scenario inject, pause/resume, incident read, evidence retrieval, planner run, candidate plan compare, approval initiate/complete, execute approved proposal, replay incident, and benchmark metrics. Provide typed error contracts and strict auth/rate limits. Use schema and contract tests between C++ → Python → Node.js → React; use correlation IDs and trace context without leaking secrets.

**Minimum executable test coverage**:
- Unit tests for physics limits, conservation/invariants, deterministic seeds, injected spoofed telemetry and true hidden state.
- Edge fail-safe: cloud outage does not disable local safety; reject unsafe command; prevent stale state effects.
- Correctness of causality hypotheses and scenario rollout selection; optimizer must never ignore hard limits; Red Team discovers at least one deliberately planted flawed plan.
- Document extraction schema, exact citations, revisions, conflict blocker, injected malicious PDF text isolation.
- Approval: valid path succeeds against simulator; no-signature, stale, replayed, changed, expired, wrong-user, unsafe and partial-failure paths fail safely.
- Evolus/GitHub integration contract tests with recorded or provider-supplied sandbox fixtures; real integration smoke tests only when authorized credentials exist.
- Frontend Playwright end-to-end test of the same deterministic incident, including visible live updates and passkey test harness or audited equivalent in CI. Do not pretend a mocked passkey is genuine hardware.
- Threat model, secret scanning, dependency audit, lint/format, static type checks, integration tests, load/performance tests and chaos scenarios.

**Benchmark methodology**: Pre-register at least **100 reproducible labeled scenarios** with fixed seeds and baseline threshold-monitoring and simple-planner comparators. Report detection precision/recall/latency, cause accuracy, false positives, physically unsafe proposal rate, safety violations **after independent shield**, simulation decision latency, downtime, production lost, energy and recovery success with distributions/confidence intervals. Clearly distinguish synthetic ground truth, simulation-based outcomes and real measured laptop/cloud performance. Never invent results.

## 8. Repository layout, documentation, and developer experience

Preferred monorepo (modify only with recorded ADR and reason):

```text
AEGIS-GRID/
  AGENTS.md                         # This constitution + execution state
  apps/web/                         # React + TS control room
  services/api/                     # FastAPI API/contract/orchestration facade
  services/edge/                    # Ryzen watchdog and FAISS
  services/agents/                  # LangGraph causal/planner/red-team/referee
  services/ingestion/               # Evolus extractors + manual pipeline
  services/executor/                # Node.js/TS MCP gateway and guarded writes
  services/inference/               # vLLM/ROCm deployment and model client
  cpp/digital-twin/                 # C++20 six-cell physical simulation
  packages/contracts/               # shared JSON Schema/OpenAPI-generated clients
  packages/scenario-fixtures/       # reproducible faults and physics snapshots
  infra/local/                      # Docker Compose/dev services
  infra/cloud/                      # MI300X deployment/scripts/config
  tests/{unit,integration,e2e,security,chaos}/
  benchmarks/                       # standardized 100+ scenario dataset/scripts
  tools/                            # benchmarks, memory estimator, checks
  docs/{ADR,architecture,security,runbooks,results}/
  .github/workflows/                # CI
```

Provide one-command documented **local simulated start** (without paid credentials) and reproducible **real edge-to-cloud start** (with user-provisioned credentials and MI300X). Containerize MongoDB and Redis locally, mock Pinecone/Evolus/GitHub clearly for tests, and keep secrets in environment / secret manager (sample names only in `.env.example`). Pin dependencies, license-check assets, provide migrations/index setup, health checks, resource limits and executable smoke tests. Use `uv` or equivalent for Python, `pnpm` or equivalent for Node/React, CMake/CTest for C++, strict typing and deterministic lockfiles.

Design a high-polish user interface with meaningful accessibility, deliberate information hierarchy, 3D/2D factory topology fallbacks for low-power hardware, a clear low-bandwidth mode, and authentic—not merely animated—telemetry.

## 9. Final deliverable and demo contract

**An actual running project, not a presentation or prototype screenshot.** Supply working source, setup scripts, docs, reproducible simulation, secure adapters, automated checks, sample safe manual, optionally a legally distributable 1,000-page-equivalent test corpus where licensing allows, benchmark harness, and recorded evidence of real provider/MI300X integrations wherever access is available.

**Three-minute demo** (the system must support this as one scripted, recoverable scenario):
- 0:00–0:25: healthy six-cell digital twin; inject sensor spoofing + coolant fault; simple threshold monitor fails.
- 0:25–0:45: Ryzen edge physics sentinel detects hidden anomaly; demonstrate cloud interruption without local safety failure.
- 0:45–1:10: MI300X agents retrieve versioned Evolus OEM evidence; causal hypotheses and confidence appear.
- 1:10–1:40: Blue recovery options; Red challenge; real C++ counterfactual rollouts; unsafe plan rejected with evidence.
- 1:40–2:00: show unmitigated versus chosen recovery future and explicit safety/business metrics.
- 2:00–2:30: unauthorized mutation rejected; show immutable plan diff; human approves with real WebAuthn authenticator; changed/replayed approval demonstrably rejected.
- 2:30–2:50: guarded Evolus MCP or clearly labeled alternate connector executes approved simulator/operational DB mutation; GitHub repair PR/push only when separately approved and authorized.
- 2:50–3:00: measure stabilized plant, immutable audit, telemetry recovery, regression tests, and business-impact summary.

Pre-index large manuals to keep demo fast; optionally extract a small bulletin live. Ensure all live vs replay/simulated vs sandbox vs production operations are labeled in UI and judges' documentation. Provide a runbook that can reset the demo with a fixed seed in under one minute. No prize guarantee or fabricated metrics.

## 10. Definition of DONE

No component is 'done' until runnable, tested, integrated, observable, documented and failure-safe. The final checkpoint requires:
- Actual laptop-to-MI300X authenticated data flow demonstrated and documented **if credentials/hardware are provided**, otherwise explicitly blocked and not misrepresented.
- Six-cell physics simulation, seeded catastrophe, deterministic edge detection, fallback controller, causal/planning graph, substantive adversarial search, independent safety shield, typed agent output, persistent interruption.
- Evolus document parsing and MCP adapters demonstrably integrated **if provider access exists**; otherwise production interfaces implemented with strict provider-verified schemas and separate test doubles.
- React real-time dashboard and WebAuthn permission proof; approved action and test-recorded rollback; Github mutation only after authorization.
- Repo-wide automated green tests and honest hardware-specific benchmark report.
- Three-minute end-to-end demo reproduces from clean start, with a backup prerecorded capture of the *same real running demo* permitted as contingency and explicitly labeled.

### Mandatory stop conditions
Stop unsafe execution and require human review if plant state differs, evidence is contradictory/insufficient, document revision is untrusted, credential approval is invalid, a tool's schema is unknown, the safety shield disagrees, or the requested command could affect an unapproved physical environment.

**Begin by executing Phase 1 of the accompanying phase guide. Do not attempt all phases in a single context window.**
