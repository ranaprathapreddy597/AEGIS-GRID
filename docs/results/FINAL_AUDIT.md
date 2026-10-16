# Hostile final audit — local scope, 2026-10-16

Assessment by the implementation agent, not an independent external penetration
test or industrial safety assessor. Main and clean-source complete gates pass 268 Python / 3 CTest / 16 Node /
14 browser checks each. Actual 180.02-second demo proof and video are retained.

| Priority | File / line | Finding | Disposition / evidence |
|---|---|---|---|
| P1 fixed | services/edge/aegis_edge/sentinel.py:76 | Trip at the 70 C hard boundary let five blockage cases cross it during bounded load ramp. | Versioned 65 C operating guard; hard 70 C limit unchanged. Original benchmark retained; five native regression cases and separate full 100-case post-fix run show 0 remaining thermal hazards. No universal safety claim. |
| P1 fixed | services/api/aegis_api/app.py:579 | Concurrent authenticated future reads could decompress many large artifacts into memory. | Single expensive reader with 429/Retry-After; actual concurrent HTTP capacity test passes. |
| P1 fixed | tools/dev.py:164 | Migration network was hardcoded to the main project, preventing isolated fresh credentials/volumes and risking cross-project confusion. | Validated COMPOSE_PROJECT_NAME derives its own storage network; clean-source demo uses a distinct project. |
| P2 fixed | apps/web/src/App.tsx:130 | UI hardcoded v1 instead of rendering the actual Sentinel policy revision. | Telemetry policy revision rendered; legacy v1 records remain readable. |
| Release blocker | services/agents/aegis_agents/graph.py:29 | Numerical top-one diagnosis and Sentinel fault detection have limited coverage; original results 31/90 and 46/90. | Published, not patched to fit the benchmark. Post-fix diagnosis 34/90; 44 detector misses remain. No production-readiness claim. |
| Release blocker | services/ingestion/aegis_ingestion/mcp.py:42 | Evolus MCP invocation transport/tool schemas unverified. | invoke refuses before HTTP. Read metadata is not live execution proof. |
| Release blocker | services/ingestion/aegis_ingestion/github.py:134 | No approved remote scope/repository/credentials/hosted CI. | publish refuses; local diff/draft is not a PR. |
| Release blocker | infra/cloud/README.md | MI300X, long-context runtime/HBM/latency/throughput unavailable. | No invented benchmark rows or live GPU claim. |
| Production boundary | docs/security/THREAT_MODEL.md | Local HTTP/shared identity, trusted Python process, physical passkey, OS vulnerability scan, complete administrator rollback/HA/OEM calibration. | Explicitly unverified/not implemented; external trusted audit anchor needed for whole-database rollback. |

No remaining exploitable P0/P1 was identified within the declared local simulator
scope by these checks; this is a bounded result, not a proof of absence. All
external mutation paths deny. No unapproved live edge control route was introduced.
The incident remains blocked by contradictory manual evidence; the approved
stationary local test resource is separate. No deployment or release tag.

## Capability scoreboard

| Capability | Status | Practical limit |
|---|---|---|
| C++ physics, sensor faults, seeded replay | Verified execution / synthetic model | No physical I/O or OEM calibration |
| Sensor-only observer, FAISS and stop policy | Verified local | 46/90 fault recall in registered development cases |
| Persistent cyclic LangGraph, numerical agents | Verified local | Offline language template abstains; no generative LLM result |
| Red/Blue minimax and 10K futures | Verified actual CPU / simulated plant | Finite synthetic priors, no posterior/industrial guarantee |
| Manual corpus, citations, conflict refusal | Verified local synthetic corpus | Evolus/OEM authority unverified |
| WebAuthn, Node signature/policy, Mongo CAS | Verified local with virtual authenticator | Stationary sandbox only; physical key and production identity unverified |
| UI private fault-to-investigation/replay | Verified browser | Explicit recorded analysis, separate from live edge |
| Local repair diff / real before-after proof | Verified local | No remote branch/PR/hosted CI |
| Evolus/Pinecone/MI300X/GitHub live acceptance | BLOCKED | Required access/evidence absent |
| Production TLS/IAM/process isolation/audit anchor/HA | Not implemented or unverified | Release blockers |

Actual inventory is in phase12-dependency-inventory.json. Frozen pip/pnpm audits
and the repository baseline secret scan are part of the full gate; this is not
a signed SBOM, OS CVE scan, formal verification or external assessment.
