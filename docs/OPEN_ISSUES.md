# Open issues

2026-10-17 sprint completion: main full gate and separate clean-source gate both
PASS 398 Python / 3 CTest / 35 Node / 17 Chromium, and the final 180.0162159s isolated
demo passes with video and proof recorded. Diagnosis optimization improved held-out
recall to 73% (precision 100%, accuracy 80%, z = 3.74, p < 0.001) over 100 fresh native cases;
targeted healthy operating confounder false assertions remain zero (100% correct abstention).
Forecasting optimization improved hazard window recall to 70% (14/20 detected, precision 66.7%,
F1 0.683, Fisher p = 0.00022, 25s median lead time, FPR 0.48% across 1,455 negative windows).
Physical limits remain: Family 1 sensor clamp produces <= 0.07 C residual under nominal load
(unmanifested), and neither model claims real-world plant calibration or hosted-model accuracy.
Dedicated MI300X, Evolus, physical passkeys, OEM reviews and production acceptance remain
BLOCKED. Completed commissioned resource, signed safety artifacts and vectors are preserved.

2026-10-17 commissioned fixture: a separate signed simulator-only rule package,
incident-bound approval and independent exact-stop executor completed the real
hosted/CTAP2/native cooldown path. This does not resolve the original plant's
manual contradictions or widen its stationary sandbox policy. Diagnosis was
non-abstaining and included independently supported sensor_bias, but also three
unconfirmed alternatives; specificity remains PARTIAL and representative diagnosis
quality is unverified. Only safe-stop containment is allowed; fault repair,
production restart, physical I/O, human industrial/OEM review and production
security acceptance remain blocked. See results/COMMISSIONED_RECOVERY.md.

2026-10-17 final recovery: Scenario A BLOCKED on simultaneous 70/95 C shared
plant limits without verified supersession, unavailable incident-bound gateway
scope and hosted diagnosis abstention. Existing sandbox rejects active faults;
its CTAP2/signature/receipt proof cannot authorize these incidents. Scenario B
PARTIAL: unsafe challenger rejected and zero new capabilities/writes, but fresh
AMD planning abstained, so its action-recommendation condition is unproved.
Do not remove manuals or widen capability scopes to force this demonstration.
Full source/audit details: results/RECOVERY_DEMONSTRATION.md. Dedicated
hardware/external/production gates remain blocked.

2026-10-17 unified application: the explicit hosted API/React path now verifies
dual Pinecone retrieval and real AMD opinions through persistent LangGraph/SSE.
Automatic service egress is replaced by an explicit hosted override; default
Compose remains offline. Only local simulator tenancy is supported. Initial
diagnosis routing failed; final diagnosis returned a schema-valid abstention,
so useful hosted diagnosis reliability remains PARTIAL. No acquired OEM document
has a verified equipment mapping to the fictional plant; external manuals remain
context only. Contradictory local manuals block incident authorization before any
passkey ceremony. Actual WebAuthn acceptance remains a separate stationary sandbox.
See results/CLOUD_INTEGRATION.md; earlier pending application-wiring statements
below are historical. No dedicated MI300X/Evolus/production gate is waived.

2026-10-17: `real-world-v1` now has 103 verified licensed external references from
five approved OEM/NIST/UCI/Zenodo sources. NASA PCoE dataset acquisition is BLOCKED
until its dataset-specific redistribution/license chain is verified. CIRA data
contains 271 empty cells and a provider-description/CSV field suffix mismatch;
missingness is disclosed, no imputation/conversion is performed. Dense-only
retrieval missed two pilot queries; bounded source routing/semantic reranking
repairs the same test set. Final 9/10 top-1 and 10/10 top-5 is development source
relevance, not held-out fault diagnosis or real-plant safety validation. References
remain untrusted context and cannot change policies. See results/REAL_WORLD_ACQUISITION.md.

2026-10-16 live follow-up supersedes historical Pinecone credential/absence
statements: the dedicated synthetic namespace has 1,235 verified persisted
semantic vectors and live filtered retrieval/cleanup proof. AMD hosted LangGraph
connectivity/strict validation is verified via the explicit runner; useful hosted
reasoning reliability remains PARTIAL because GLM times out and graph opinions
abstain. Earlier opaque validation failures cannot be reconstructed from retained
metadata. Automatic hosted service egress, hosted Mongo acceptance, production
tenancy/identity and representative semantic/diagnosis evaluation remain pending.
MI300X, Evolus and all other unverified external gates remain BLOCKED. See
results/LIVE_INTEGRATION.md for the current evidence; entries below are historical.

| ID | State / phase | Issue and next action |
|---|---|---|
| EXT-01 | Blocked / Phase 6 | Pinned model/image, memory projections, read client and deployment/collection scripts implemented. No endpoint/device logs or actual long-context/HBM measurements. User will provision access later; live gate remains blocked. |
| EXT-02 | Blocked / Phase 5 | Verified supplied OpenAPI read adapter and exact-match pipeline implemented. Application scope supplied; rotated local key, existing document IDs/personal read auth and live extraction proof pending. No provider call verified. |
| EXT-03 | Partial / live follow-up | Pinecone synthetic ingestion and filtered retrieval verified (1,235 vectors); production/OEM retrieval and GitHub live acceptance remain unverified/blocked. Historical credential absence no longer describes Pinecone. |
| HW-01 | Unverified | NPU device enumerated OK and amd-smi on PATH; no compatible accelerated inference workload verified. CPU backend tested. |
| TOOL-01 | Resolved for Docker path | Native Windows CMake/compiler absent. Container CMake/CTest is the chosen Phase 1 path; native MSVC remains unverified. |
| MODEL-01 | Resolved / Phase 2 | Coupled coolant/pressure/feeder, bounded actuators, instrument noise, seeded faults and snapshots are implemented; see PHYSICS.md and phase evidence. |
| MODEL-02 | Synthetic model limitation | No plant/OEM calibration, cavitation, boiling, leakage or physical I/O. Sensor intervals cover assumed instrument noise only, not spoof/delay uncertainty. |
| SEC-02 | Simulator inspection only | Authenticated local telemetry includes ground truth/fault labels for developer inspection. Phase 3 SensorFrame excludes truth, scenario and fault labels; injection-invariance tests pass. No production tenant boundary is claimed. |
| SAFE-01 | Verified local / Phase 9 | Actual WebAuthn, Ed25519, Node policy and native sandbox CAS pass. Only the stationary test sandbox is enabled; incident manual conflict and external writes remain closed. |
| DATA-01 | Resolved / Phase 4 | Journal-acknowledged append-only Mongo events and snapshots, bounded Redis fanout, scoped ACLs and actual API-restart replay are implemented and tested; see PHASE4.md. |
| SEC-01 | Local-only baseline | Shared read tokens and loopback HTTP are not production identity/TLS. Cloud configuration intentionally unavailable. |
| BUILD-01 | Hardening backlog | Direct tool pins and image digests do not freeze all Debian apt transitive packages. Snapshot repository/SBOM validation deferred. |
| TEST-01 | Nonblocking maintenance | Starlette emits an httpx TestClient deprecation warning; all tests pass. Review the maintained httpx2 migration before upgrading the testing transport. |
| CI-01 | Not run remotely | GitHub Actions workflow is present; no remote configured, pushed or hosted CI run claimed. Identical local gate passes. |
| DATA-02 | Local deployment limit | Single Mongo instance, shared local tenant, 30-day TTL and bounded replay; no high availability or exactly-once cross-system transaction claim. |
| CERT-01 | Deferred / Phase 8 | Snapshot model revision and payload hash are checked; rollout certificates must additionally bind the native binary hash before use for authorization. |
| GIT-01 | Local repository | No remote configured and no user Git identity set. Phase commit uses explicit AEGIS GRID Automation identity; no global Git configuration change. |

Initial absence of the phase guide was resolved by the user during discovery.
Any build/test failure discovered during a phase must be repaired or explicitly
recorded as an unmet gate; missing providers alone do not block the local gate.

Phase 5: FAISS lexical top-1 relevance is 20/24 on exact-term development queries;
this is not semantic/OEM accuracy. Cloud indexing/comparison remains blocked.
Arbitrary hostile PDF parsing requires separate process resource enforcement before
public ingestion; only fixed read-only fixtures are exposed by the API. Free-form
OEM constraint extraction and trusted revision lineage require verified source data.

Phase 7 local gate passed. Actual persisted graph and delivered sensor trends are
verified; full-corpus contradiction still refuses action. The local inference
backend is a deterministic abstention template, not a generative model. Phase 8
must replace the limited two-candidate forecasts with actual robust search.

Phase 8: native binary/state/policy/seed-bound, reproducible rollout artifacts now
exist. They are evidence only, not signed execution capabilities or industrial
certification. Fixed-grid worst-case selection is deliberately conservative;
severe priors require stopping and lose production. Finite coverage excludes
unknown model error/real plants. Phase 9 must verify artifacts/current state again
and add independent authorization before any protected mutation is enabled.

Phase 9 local gate passes; see PHASE9.md and ADR 0012. Physical passkey/hardware
attestation, production TLS/IAM, credential lifecycle/revocation and external audit
anchoring remain unverified. The API process holds trusted authorizer/gateway
configuration; production process isolation is not claimed. A full administrator
rollback of all Mongo state needs an external trusted anchor to detect.

TEST-02: one owner-login transport failure and one restart readiness timeout were
observed and retained. Two-second bounded API shutdown and sanitized diagnostics
were added; final focused/full suites pass. The intermittent failure's complete
cause is not established; no production SLA or stability guarantee is claimed.
UX-01 resolved / Phase 10: browser reload restores the owner session and paused
proposal from authenticated APIs; actual before/after Chromium proof retained.
External MCP invocation/GitHub publication remains BLOCKED: metadata/configured
tool names are not verified invocation schemas or hosted CI/publication proof.


Phase 12 findings: original 100-case benchmark exposed five late thermal trips;
policy v2 adds a 65 C operating guard, with unchanged 70 C hard bound. All five
native regressions pass and the separate post-fix run has 0/100 thermal hazards.
Fault recall remains 46/90 (44 misses); numerical diagnosis is 34/90 after the
fix. These development limitations block production claims. See BENCHMARKS.md.
Concurrent expensive futures reads are now bounded with 429. Local Compose
migration networking now respects a separate project for fresh-source proof.
Container OS CVE scanning/signed provenance, production IAM/TLS/process isolation,
physical-key acceptance and external audit anchoring remain outstanding.
