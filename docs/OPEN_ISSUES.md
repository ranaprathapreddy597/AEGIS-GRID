# Open issues

| ID | State / phase | Issue and next action |
|---|---|---|
| EXT-01 | Blocked / Phase 6 | No MI300X endpoint, access credentials or device logs. User provisioning needed before live hardware proof. |
| EXT-02 | Blocked / Phase 5 | User supplied api-1.json (Evolus Integration API v1, OpenAPI 3.0.4); schema inspection/adapter remains Phase 5. No provider call verified. |
| EXT-03 | Blocked / later phases | Pinecone/GitHub credential variables not present; no external calls or writes attempted. |
| HW-01 | Unverified | NPU device enumerated OK and amd-smi on PATH; no compatible accelerated inference workload verified. CPU backend tested. |
| TOOL-01 | Resolved for Docker path | Native Windows CMake/compiler absent. Container CMake/CTest is the chosen Phase 1 path; native MSVC remains unverified. |
| MODEL-01 | Resolved / Phase 2 | Coupled coolant/pressure/feeder, bounded actuators, instrument noise, seeded faults and snapshots are implemented; see PHYSICS.md and phase evidence. |
| MODEL-02 | Synthetic model limitation | No plant/OEM calibration, cavitation, boiling, leakage or physical I/O. Sensor intervals cover assumed instrument noise only, not spoof/delay uncertainty. |
| SEC-02 | Simulator inspection only | Authenticated local telemetry includes ground truth/fault labels for developer inspection. Phase 3 SensorFrame excludes truth, scenario and fault labels; injection-invariance tests pass. No production tenant boundary is claimed. |
| SAFE-01 | Deferred / Phases 3/9 | Phase 3 deterministic local emergency shield is tested. Signed capabilities/passkeys/planned recovery are later gates; HTTP operational mutations remain unavailable. |
| DATA-01 | Deferred / Phase 4 | Mongo/Redis are infrastructure only, not used for incident/event persistence; no restart replay guarantee. |
| SEC-01 | Local-only baseline | Shared read tokens and loopback HTTP are not production identity/TLS. Cloud configuration intentionally unavailable. |
| BUILD-01 | Hardening backlog | Direct tool pins and image digests do not freeze all Debian apt transitive packages. Snapshot repository/SBOM validation deferred. |
| TEST-01 | Nonblocking maintenance | Starlette emits an httpx TestClient deprecation warning; all tests pass. Review the maintained httpx2 migration before upgrading the testing transport. |
| CI-01 | Not run remotely | GitHub Actions workflow is present; no remote configured, pushed or hosted CI run claimed. Identical local gate passes. |
| GIT-01 | Local repository | No remote configured and no user Git identity set. Phase commit uses explicit AEGIS GRID Automation identity; no global Git configuration change. |

Initial absence of the phase guide was resolved by the user during discovery.
Any build/test failure discovered during a phase must be repaired or explicitly
recorded as an unmet gate; missing providers alone do not block the local gate.
