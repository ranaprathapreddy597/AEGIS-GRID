# Open issues

| ID | State / phase | Issue and next action |
|---|---|---|
| EXT-01 | Blocked / Phase 6 | No MI300X endpoint, access credentials or device logs. User provisioning needed before live hardware proof. |
| EXT-02 | Blocked / Phase 5 | No verified Evolus provider specification/sandbox supplied. Discover actual provider and schemas before adapter work; invent no routes. |
| EXT-03 | Blocked / later phases | Pinecone/GitHub credential variables not present; no external calls or writes attempted. |
| HW-01 | Unverified | NPU not probed for a supported workload; do not equate CPU branding or AMD-SMI availability with acceleration. |
| TOOL-01 | Resolved for Docker path | Native Windows CMake/compiler absent. Container CMake/CTest is the chosen Phase 1 path; native MSVC remains unverified. |
| MODEL-01 | Deferred / Phase 2 | Independent thermal cells omit shared coolant dynamics, pressure, feeder, uncertainty and faults. |
| SAFE-01 | Deferred / Phases 3/9 | No deterministic controller, signed capabilities, passkeys or operational writes yet. All mutations are unavailable. |
| DATA-01 | Deferred / Phase 4 | Mongo/Redis are infrastructure only, not used for incident/event persistence; no restart replay guarantee. |
| SEC-01 | Local-only baseline | Shared read tokens and loopback HTTP are not production identity/TLS. Cloud configuration intentionally unavailable. |
| BUILD-01 | Hardening backlog | Direct tool pins and image digests do not freeze all Debian apt transitive packages. Snapshot repository/SBOM validation deferred. |
| TEST-01 | Nonblocking maintenance | Starlette emits an httpx TestClient deprecation warning; all tests pass. Review the maintained httpx2 migration before upgrading the testing transport. |
| CI-01 | Not run remotely | GitHub Actions workflow is present; no remote configured, pushed or hosted CI run claimed. Identical local gate passes. |
| GIT-01 | Local repository | No remote configured and no user Git identity set. Phase commit uses explicit AEGIS GRID Automation identity; no global Git configuration change. |

Initial absence of the phase guide was resolved by the user during discovery.
Any build/test failure discovered during Phase 1 must be repaired or explicitly
recorded as an unmet gate; missing providers alone do not block the local Phase 1 gate.
