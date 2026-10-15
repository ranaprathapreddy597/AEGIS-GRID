# Open issues

| ID | State / phase | Issue and next action |
|---|---|---|
| EXT-01 | Blocked / Phase 6 | No MI300X endpoint, access credentials or device logs. User provisioning needed before live hardware proof. |
| EXT-02 | Blocked / Phase 5 | No verified Evolus provider specification/sandbox supplied. Discover actual provider and schemas before adapter work; invent no routes. |
| EXT-03 | Blocked / later phases | Pinecone/GitHub credential variables not present; no external calls or writes attempted. |
| HW-01 | Unverified | NPU not probed for a supported workload; do not equate CPU branding or AMD-SMI availability with acceleration. |
| TOOL-01 | Resolved for Docker path | Native Windows CMake/compiler absent. Container CMake/CTest is the chosen Phase 1 path; native MSVC remains unverified. |
| MODEL-01 | Resolved / Phase 2 | Coupled coolant/pressure/feeder, bounded actuators, instrument noise, seeded faults and snapshots are implemented; see PHYSICS.md and phase evidence. |
| MODEL-02 | Synthetic model limitation | No plant/OEM calibration, cavitation, boiling, leakage or physical I/O. Sensor intervals cover assumed instrument noise only, not spoof/delay uncertainty. |
| SEC-02 | Simulator inspection only | Authenticated local telemetry includes ground truth/fault labels for developer inspection. Future anomaly detection must exclude these fields; no production tenant or sensor-only separation is claimed. |
| SAFE-01 | Deferred / Phases 3/9 | No deterministic controller, signed capabilities, passkeys or operational writes yet. HTTP operational mutations are unavailable; local C ABI controls only isolated offline simulator instances. |
| DATA-01 | Deferred / Phase 4 | Mongo/Redis are infrastructure only, not used for incident/event persistence; no restart replay guarantee. |
| SEC-01 | Local-only baseline | Shared read tokens and loopback HTTP are not production identity/TLS. Cloud configuration intentionally unavailable. |
| BUILD-01 | Hardening backlog | Direct tool pins and image digests do not freeze all Debian apt transitive packages. Snapshot repository/SBOM validation deferred. |
| TEST-01 | Nonblocking maintenance | Starlette emits an httpx TestClient deprecation warning; all tests pass. Review the maintained httpx2 migration before upgrading the testing transport. |
| CI-01 | Not run remotely | GitHub Actions workflow is present; no remote configured, pushed or hosted CI run claimed. Identical local gate passes. |
| GIT-01 | Local repository | No remote configured and no user Git identity set. Phase commit uses explicit AEGIS GRID Automation identity; no global Git configuration change. |

Initial absence of the phase guide was resolved by the user during discovery.
Any build/test failure discovered during a phase must be repaired or explicitly
recorded as an unmet gate; missing providers alone do not block the local gate.
