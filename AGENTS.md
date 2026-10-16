# AEGIS//GRID repository instructions

Read and follow `AEGIS_GRID_MASTER_PROMPT.md` as the build constitution and
`AEGIS_GRID_BUILD_PHASES.md` as the ordered work orders. Both supplied files are
authoritative project instructions. Preserve them unchanged.

## Current execution state

- Assigned work: **remaining phases in order**, authorized on 2026-10-15.
  Phase 1 passed at `f024ab5`; Phase 2 at `57010e1`; Phase 3 at `b9985f6`.
  Phase 4 passed at `12c2d86` on 2026-10-16. Phase 5 local gate passed at `5513a27`; Evolus/Pinecone live gates remain blocked.
  Phase 6 local gate accepted on 2026-10-16 at `7dfe7e4`.
  Phase 7 local gate passed; see docs/results/PHASE7.md.
  Phase 8 local gate passed; see docs/results/PHASE8.md.
  Current phase: **9**. Phases 7–12 are authorized sequentially with the local backend.
  MI300X/Evolus/Pinecone live acceptance gates remain BLOCKED until verified.
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
