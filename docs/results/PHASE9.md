# Phase 9 report — 2026-10-16, Asia/Calcutta

Status: local gate PASS. MI300X/Evolus/Pinecone live gates BLOCKED.
Previous phase commit a856d6b. Physical passkey acceptance remains unverified.

Implemented actual WebAuthn enrollment/assertion verification, origin-bound owner
sessions, exact immutable action/digest, expiring one-use challenges, persistent
LangGraph approval interrupt/resume, Ed25519 capability, independent Node verifier,
private native gateway, atomic Mongo snapshot/version/nonce/receipt CAS, safe
retry/reconciliation, real React Ask First flow and scoped storage identities.
Only the explicitly separate stationary authorization sandbox can be changed;
the incident's manual contradiction and running edge latch remain closed.

Focused browser proof passed with actual Chromium WebAuthn **virtual** CTAP2
authenticator, maintained Python verifier, Node and actual Mongo/C++. It approved
two immutable plans at the same state, restarted the API, applied one through
the independent gateway and refused the stale second. Assertion replay, missing
approval, changed digest/unknown execution fields and wrong origin/viewer token
were denied. Idempotent retry returns the same receipt without another mutation.
See phase9-webauthn-browser.json; these are not physical hardware credentials.

The first browser test found the cookie test was querying `/` instead of its
narrow path, then an ambiguous status selector and collapsed-details read. These
test issues were fixed without broadening cookie scope. The completed flow also
found an actual keyboard accessibility issue in the scrollable exact-action JSON;
the `<pre>` now has a focus target and accessible name. Focused browser/axe proof
passed after repair. Unit proof tests execute actual ES256/Ed25519 signatures;
storage doubles are labeled and separate from real Mongo/browser evidence.

Commands executed:

```powershell
.venv/Scripts/python tools/dev.py start
.venv/Scripts/python -m pytest -q tests/security/test_capability_authorization.py tests/security/test_webauthn_proofs.py
pnpm build
pnpm test
pnpm exec playwright test tests/e2e/approval.spec.ts
.venv/Scripts/python tools/dev.py check
```

Final full gate: **244 Python / 3 CTest / 15 Node / 11 Chromium tests passed**.
All types/lints, generated contract/TS checks, fixture drift, cloud recipe render,
secret/dependency audits and actual HTTP/SSE/cross-language checks passed. Actual
Mongo authorization checks denied 14 additional privilege escalations, alongside
the existing monitoring/graph checks. Real C++ private-copy interruption tests
verify unchanged state before commit and identical receipt on retry. The browser
proof survives a real API restart and has zero axe findings. The final approval
capture was visually inspected; it contains no token or authenticator key.

The first full run had a browser owner-login transport failure; a later focused
run observed a 502 beyond the existing twenty-second restart deadline. Both are
preserved (phase9-first-full-gate.txt, phase9-restart-timeout.txt). A separate
open-SSE probe observed 8.32 s readiness; this does not establish the intermittent
failure's complete cause. Uvicorn graceful shutdown is now bounded to two seconds
so active SSE cannot wait indefinitely. The focused check and final full suite
passed without relaxing any security check or test timeout. Expected stream
closure during deliberate restart is recorded by sanitized transport diagnostics.
No production availability claim, release or external write is made.
