# AEGIS//GRID repository instructions

Read and follow `AEGIS_GRID_MASTER_PROMPT.md` as the build constitution and
`AEGIS_GRID_BUILD_PHASES.md` as the ordered work orders. Both supplied files are
authoritative project instructions. Preserve them unchanged.

## Current execution state

- Final recovery follow-up 2026-10-17: Scenario A BLOCKED; Scenario B PARTIAL.
  Two real native faults and hosted AMD/dual-Pinecone investigations persist;
  vectors remain 1,235 + 103, zero reingestion. Whole shared plant corpus conflicts
  (70/95 C); existing signed executor only permits a fault-free stationary sandbox.
  No incident challenge/capability/protected write was issued. A diagnosis abstained;
  B diagnosis route failed and planning abstained. Do not exclude the bulletin or
  substitute sandbox CTAP2 approval for incident recovery. Read
  docs/results/RECOVERY_DEMONSTRATION.md for actual calls, failures and gates.
  Main and separate frozen-source gates each pass 332 Python / 3 CTest / 16 Node /
  14 browser checks; 180.0182-second clean demo passes its stationary sandbox only.

- Unified cloud follow-up authorized on 2026-10-17: both existing Pinecone
  namespaces now feed the persistent application LangGraph through an explicit
  hosted Compose override; default mode stays offline. Guarded live UI/API/SSE,
  AMD diagnosis/planning, eight cited sources and native adversarial evaluation
  reach the approval interrupt. No dataset was regenerated/reuploaded and no
  Pinecone record was modified/deleted. Diagnosis reliability remains PARTIAL;
  contradictory manuals prohibit incident authorization. Actual WebAuthn remains
  independently tested in the stationary sandbox. Read docs/CLOUD_WORKFLOW.md
  and docs/results/CLOUD_INTEGRATION.md for measured results, final gates and
  source-freeze limitations. MI300X/Evolus/production/physical acceptance remain
  BLOCKED. Never reset application sessions to evade provider quotas.

- Public acquisition follow-up authorized on 2026-10-17: `real-world-v1` now has
  103 verified licensed references from five OEM/NIST/UCI/Zenodo sources. The first
  pilot correctly blocked on 2/10 dense-query failures; query-only repair passed
  the same pilot before 83 further inserts. No records were overwritten/deleted.
  NASA PCoE acquisition remains BLOCKED on license/provenance verification.
  External references never authorize commands or change independent safety/HITL.
  Read docs/results/REAL_WORLD_ACQUISITION.md for actual evidence and constraints.

- Assigned work: **remaining phases in order**, authorized on 2026-10-15.
  Phase 1 passed at `f024ab5`; Phase 2 at `57010e1`; Phase 3 at `b9985f6`.
  Phase 4 passed at `12c2d86` on 2026-10-16. Phase 5 local gate passed at `5513a27`; Evolus/Pinecone live gates remain blocked.
  Phase 6 local gate accepted on 2026-10-16 at `7dfe7e4`.
  Phase 7 local gate passed; see docs/results/PHASE7.md.
  Phase 8 local gate passed; see docs/results/PHASE8.md.
  Phase 9 local gate passed; see docs/results/PHASE9.md.
  Phase 10 local gate passed; see docs/results/PHASE10.md.
  Phase 11 local gate passed; see docs/results/PHASE11.md.
  Phase 12 local gate and clean-source demo/full gate passed; see docs/results/PHASE12.md.
  Local phases 1–12 are validated. Required live and production gates remain BLOCKED.
  No release tag, external write or production completion is authorized by the local gate.
  MI300X/Evolus and production acceptance gates remain BLOCKED until verified.
  Live follow-up authorized on 2026-10-16: scoped synthetic Pinecone upserts,
  retrieval/count/filter/cleanup tests and AMD inference diagnostics. Pinecone now
  retains 1,235 verified native 256-D semantic vectors; actual LangGraph hosted
  diagnosis/planning and retrieved sources reach the native recovery/HITL boundary.
  Hosted reasoning reliability remains PARTIAL (GLM timeout; graph abstentions).
  See docs/results/LIVE_INTEGRATION.md and docs/LIVE_KNOWLEDGE.md. This specific
  provider authorization does not authorize enterprise writes or deployments.
  Complete/test/commit/report each phase before proceeding. Record unavailable
  external gates explicitly; never waive them to mark a release complete.
- Read `docs/PROGRESS.md`, `docs/OPEN_ISSUES.md`, and
  `docs/INTEGRATION_EVIDENCE.md` before continuing.
- Never call incomplete or simulated integration a verified production capability.
- All plant execution is confined to the isolated simulator. Physical I/O is absent.
- No external writes, deployments, credentials, or fabricated provider schemas.
- Check `.env.example` for configuration names; never print or commit secret values.
- Commit each passing phase and record actual test evidence and remaining gates.
- Keep contracts generated from Pydantic and OpenAPI; do not hand-edit generated files.

## Development

- Windows host with Docker Desktop Linux engine; native Python and Node also supported.
- `python tools/dev.py start` builds and starts the local stack.
- `python tools/dev.py check` runs the current automated gate.
- Safety control is confined to isolated simulator instances. Approval and enterprise
  writes remain closed until their numbered gates pass. No incomplete mutation routes.
