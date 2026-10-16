# Open issues

| ID | State / phase | Issue and next action |
|---|---|---|
| EXT-01 | Blocked / Phase 6 | Pinned model/image, memory projections, read client and deployment/collection scripts implemented. No endpoint/device logs or actual long-context/HBM measurements. User will provision access later; live gate remains blocked. |
| EXT-02 | Blocked / Phase 5 | Verified supplied OpenAPI read adapter and exact-match pipeline implemented. Application scope supplied; rotated local key, existing document IDs/personal read auth and live extraction proof pending. No provider call verified. |
| EXT-03 | Blocked / later phases | Pinecone/GitHub credential variables not present; no external calls or writes attempted. |
| HW-01 | Unverified | NPU device enumerated OK and amd-smi on PATH; no compatible accelerated inference workload verified. CPU backend tested. |
| TOOL-01 | Resolved for Docker path | Native Windows CMake/compiler absent. Container CMake/CTest is the chosen Phase 1 path; native MSVC remains unverified. |
| MODEL-01 | Resolved / Phase 2 | Coupled coolant/pressure/feeder, bounded actuators, instrument noise, seeded faults and snapshots are implemented; see PHYSICS.md and phase evidence. |
| MODEL-02 | Synthetic model limitation | No plant/OEM calibration, cavitation, boiling, leakage or physical I/O. Sensor intervals cover assumed instrument noise only, not spoof/delay uncertainty. |
| SEC-02 | Simulator inspection only | Authenticated local telemetry includes ground truth/fault labels for developer inspection. Phase 3 SensorFrame excludes truth, scenario and fault labels; injection-invariance tests pass. No production tenant boundary is claimed. |
| SAFE-01 | Deferred / Phases 3/9 | Phase 3 deterministic local emergency shield is tested. Signed capabilities/passkeys/planned recovery are later gates; HTTP operational mutations remain unavailable. |
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
