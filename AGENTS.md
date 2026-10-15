# AEGIS//GRID repository instructions

Read and follow `AEGIS_GRID_MASTER_PROMPT.md` as the build constitution and
`AEGIS_GRID_BUILD_PHASES.md` as the ordered work orders. Both supplied files are
authoritative project instructions. Preserve them unchanged.

## Current execution state

- Assigned work: **Phase 2** (explicit continuation authorized on 2026-10-15).
  Phase 1 passed at `f024ab5`. Complete/test/commit Phase 2 before proceeding.
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
- Phase 2 extends the isolated twin. Safety controller, persistent graph, approval,
  and enterprise writes belong to later phases. Do not expose incomplete mutation routes.
