# ADR 0012: WebAuthn approval, signed capabilities and atomic sandbox execution

Accepted 2026-10-16. Prior local gate: Phase 8 at a856d6b. MI300X/Evolus/Pinecone
live gates remain BLOCKED. This design enables one narrowly defined local scope;
it does not authorize the contradictory incident, external tools or physical I/O.

## Owner and ceremony boundary

A distinct, generated owner bootstrap token starts a fifteen-minute HttpOnly,
SameSite=Strict cookie session. Viewer/service tokens cannot enroll or approve.
The cookie path is limited to `/api/v1/approval`. Every state-changing public
approval request requires the exact configured `http://localhost:PORT` Origin;
there is no CORS permission. Localhost's browser secure-context exemption permits
WebAuthn on loopback HTTP. This is a development identity/session arrangement,
not production TLS, enterprise IAM or an attested hardware deployment.

Pinned py_webauthn 3.0.1 verifies actual registration and assertion responses.
RP ID is exactly localhost; expected origin/challenge come from server state.
Both user presence and user verification are required. Only ES256 is enrolled.
Credential ownership, user handle when present, RP hash, type, signature, flags
and counter semantics are checked. Zero counters on synced passkeys are allowed
under the maintained verifier's semantics; fresh challenges and one-use approvals
still prevent assertion replay. Registration attestation is `none`; hardware
provenance is not asserted. Cross-origin/top-origin credential use is refused.

Each 32-byte CSPRNG challenge is persisted with owner session, user, RP/origin,
action ID, exact digest and ninety-second expiry. Atomic find-and-delete consumes
it before verification, including a failed attempt. Wrong sessions cannot consume
someone else's challenge. Credential counters update with optimistic comparison.
An approval CAS changes only waiting → approved for the bound immutable proposal.
WebAuthn signs authenticator data plus the hash of clientDataJSON, not action JSON;
the server-side challenge record binds that proof to the exact action digest.

## Scope and independent execution

Administrative startup provisions `authorization-sandbox-01` once from the real
C++ healthy fixture after thirty steps. It is stationary, separate from the live
edge and incident, has no injected fault and has a distinct explicitly synthetic
authorization-test policy. There is no public creation/reset endpoint. This test
scope permits only pump 1, six loads 0, six valves 1 with native bounded ramps.
It cannot waive the incident's OEM contradiction or restart its emergency latch.

Canonical immutable ProposedPlan binds resource, tenant, action, scope, risk,
before/after controls, database/native versions, source snapshot and native binary
hashes, actual native stop-rollout artifact, expiry and compensation. It is stored
before the real LangGraph Ask First interrupt. The UI displays exact JSON, digest
and semantic diff. Protected execution additionally requires the displayed digest;
an edited digest or unknown execution fields are rejected. Browsers never receive
the signed capability or privileged gateway/database credentials.

Only successful WebAuthn verification issues a fixed-algorithm Ed25519 capability
with issuer, audience, owner, one-use nonce, action digest/ID, scope, versions and
at most sixty-second lifetime. The random private seed exists only in ignored
local configuration and the Python authorizer. The independent Node process gets
the DER public verifier key, not the signing seed. It validates generated schemas,
actual signature, fixed issuer/audience/user/scope, digest, expiry, expected
versions and exact stop controls before forwarding to a fixed internal URL.
The public ingress refuses `/internal/`; the private gateway has another credential
and independently repeats signature, durable approval, current-state, binary,
rollout and deterministic shield checks. No model has raw tokens or callable
privileged connectors. External systems are not reachable through this scope.

## Atomicity, replay and failure

The private gateway restores a C++ copy, checks the actual 120-second stop
certificate, applies exact controls and verifies sixty native steps. Only then
does a single Mongo compare-and-swap replace the stationary snapshot, increment
database version and append nonce plus hash-chained receipt atomically. A stale
version/state, changed binary/certificate, used nonce or policy failure discards
the copy. Failure before commit leaves the resource unchanged; failure after
commit can return the existing receipt, including after an API/checkpoint restart.
The approval workflow resumes only after reading verified durable approval; client
`approved:true` data has no authority. The original incident graph remains paused.

Exact repeated execution returns the identical receipt without a second effect;
replayed WebAuthn assertions, nonce reuse for another action and stale proposals
are refused. A successful atomic state change is the compensation boundary;
retaining the committed safe stop is preferable to blindly restoring energized
loads. No physical transaction/rollback guarantee is claimed. Receipt hashes,
version progression and the snapshot/receipt relationship are verified on reads.
This is a local single-Mongo deployment without an independent external anchor;
administrator rollback of the entire database cannot be detected cryptographically
without an external trusted checkpoint. Public expected-state checks still fail
closed on disagreement. Receipts are bounded to 256 per stationary test resource.

Separate Mongo roles permit approver metadata only, gateway resource update plus
proposal read, graph checkpoints/append-only analysis, and append-only monitoring.
Runtime users cannot provision/reset the sandbox or write unrestricted enterprise
plans/actions/audit. Actual role-denial checks are part of the local gate.

## Verification and limits

CI uses Chromium's **virtual** CTAP2 authenticator with real browser APIs and real
server cryptographic verification; it does not mock navigator.credentials. An
ignored `.run/webauthn-ci.json` holds only that generated virtual key, reused with
increasing counters so repeated gates do not fill the enrollment quota. Never log
or distribute it. It is development test material, not a physical/production key.
The owner bootstrap token is still required to establish its session. Physical
Windows Hello/security-key acceptance remains unverified.

Real ES256 negative proofs, native copy/rollback tests, signed policy attacks and
Node verification tests accompany actual Mongo/browser/restart execution. No
live Evolus MCP, GitHub operation, MI300X success or general incident execution is
implied by passing this local scope.

Primary sources inspected: [py_webauthn registration](https://duo-labs.github.io/py_webauthn/registration.html),
[authentication](https://duo-labs.github.io/py_webauthn/authentication.html),
[pinned registration verifier](https://github.com/duo-labs/py_webauthn/blob/v3.0.1/webauthn/registration/verify_registration_response.py),
[pinned assertion verifier](https://github.com/duo-labs/py_webauthn/blob/v3.0.1/webauthn/authentication/verify_authentication_response.py).
Installed package signatures and official release/PyPI timestamps were inspected;
webauthn 3.0.1 (2026-09-25) and cryptography 50.0.2 (2026-09-30) are pinned.
