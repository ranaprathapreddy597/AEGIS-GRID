# Phase 10 report — 2026-10-16, Asia/Calcutta

Status: local gate PASS. External live gates remain BLOCKED.
Previous local phase: d8ed0bd. No external write/deployment/PR was performed.

Implemented a real passkey-bound operational Mongo maintenance record update
inside the isolated authorization resource. Exact before/after diff, expected
record/database/native versions, binary/certificate hashes and one-use capability
are checked by Node and the native gateway. Snapshot + record + nonce + chained
receipt are atomic; precommit failure discards both, retry has one effect.
Receipt-v1 compatibility preserves actual Phase 9 records; new v2 receipts bind
the maintenance hash and local tool identity. Native and provider tests remain
separate: in-memory transaction doubles are labeled, actual Mongo/browser proof
comes through the running stack.

Inspected actual Evolus Agent/McpServerInfo schemas and inherited auth. Added
schema-validated read discovery, bounded secret-free projection and unconditional
refusal for unverified invocation. Configured tool names never become authority.
No verified Evolus MCP transport/tool schema or key is available; live gate is
BLOCKED. GitHub read preflight/publication draft follow official documentation;
publication is closed without remote scope, approval policy and required hosted
CI proof. This is not a working live GitHub publisher or Evolus mutation success.

Reproduced a real approval reload bug through Chromium (before: resumed=false).
Built/tested a standalone Phase 9 source patch and verified resumed=true on that
running candidate. Tool applies the exact diff and checks source hashes. The
immutable bundle is reviewable/downloadable through authenticated APIs/UI.
Its fingerprint is 2bb56230fdc448401e0290808e03c1cb5d9e4e44aa86d6bbaa27e9a94b9a6939.
It has no dependency on the new maintenance UI; the final UI adds that separately.
No fabricated hosted CI/branch/commit/PR receipt. See ADR 0013.

Focused actual browser: both simulator and Mongo-maintenance workflows pass,
including reload, API restart, stale/digest/assertion replay denials and same-receipt
retry. Provider contract doubles (read-only) pass. Final full gate passed:
248 Python / 3 CTest / 16 Node / 13 Chromium; schema/type/lint/build, dependency
audits, secret scan, HTTP/SSE and actual storage checks passed. Six storage,
three graph and fourteen authorization privilege denials passed. The actual
connector/diff screenshot was visually inspected; external actions stay closed.
Raw evidence: phase10-checks.txt and phase10-webauthn-browser.json.

Commands:

```powershell
.venv/Scripts/python tools/dev.py start
pnpm exec node tools/probe_approval_reload.mjs --output docs/results/phase10-repair-before.json --expect missing
pnpm exec node tools/probe_approval_reload.mjs --output docs/results/phase10-repair-after.json --expect resumed
.venv/Scripts/python tools/prepare_repair.py
pnpm exec playwright test tests/e2e/approval.spec.ts
.venv/Scripts/python tools/dev.py check
```

The baseline probe was run before the fix; the after probe while the standalone
candidate was deployed. Do not expect the baseline command to reproduce the old
result on an already repaired UI. Missing provider access is not waived to claim
release completion. Next ordered local phase is 11 after this phase commit.
