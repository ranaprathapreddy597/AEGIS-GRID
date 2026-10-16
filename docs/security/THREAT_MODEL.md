# Security model — local phases 1–9

Assets: local viewer/owner/service secrets, Ed25519 signing seed, WebAuthn public
credential registry, native snapshots, approval/receipt integrity and local process
availability. No physical plant or live third-party write connector is connected.

| Threat | Implemented control | Remaining limitation |
|---|---|---|
| Anonymous telemetry reads | Required bearer token; comparison uses constant-time library primitive | Shared local development identity, not per-user authorization |
| Viewer reaches write path | Separate owner bootstrap/session, required WebAuthn UV, signed scoped capability, independent Node and native shield | Only stationary authorization sandbox is enabled; incident/enterprise writes closed |
| Child output malformed/stalled | Bounded lines, strict schema, versions/deadline/health and independent conservative simulator shield | No industrial controller/physical I/O or automatic energized restart |
| Cloud impersonation/data substitution | Explicit authenticated HTTPS AEGIS client and constrained inference interface | Actual remote endpoint/device acceptance BLOCKED |
| Old data looks live | Edge/API/browser freshness checks; distinct run UUID; visible stale label | Polling transport is not lossless or persistent |
| Token leakage | In-memory browser token, no access logs, no query credentials, masked config, `.env` excluded | Docker admins and same-user local processes can read `.env`/container env |
| Browser script injection | React escaping, local static assets, CSP, no document/model content | Inline style allowed for charts; stricter nonces later |
| Resource exhaustion | Stream cap, read token bucket, bounded buffers, container memory/CPU/PID caps | Auth brute-force uses no distributed limiter; health is public and local |
| Dependency compromise | Exact Python/Node locks, image digests, direct build-tool pins, 24h npm release-age guard, audits | Audits are snapshots; OS transitive packages not hermetic |
| Accidental network exposure | Only loopback web port; two internal Docker networks plus a web-only ingress bridge; storage disconnected from app | Docker host/admin is trusted; web bridge permits outbound traffic |

The application containers run unprivileged with read-only root filesystems,
dropped capabilities and no-new-privileges. Vendor Redis/Mongo entrypoints use
their image defaults, with isolated storage/network access. Do not expose this
development configuration to an untrusted network.

No physical safety claim is made. The deterministic emergency controller and
counterfactual search operate only in the synthetic simulator. Full-corpus manual
contradiction still prevents incident execution. Approval proof is confined to a
separately provisioned healthy stationary sandbox, with no public reset endpoint.

| Approval attack | Boundary |
|---|---|
| Owner token confused with viewer token | Separate high-entropy bootstrap secret; HttpOnly path-scoped session; viewer rejected |
| CSRF / wrong origin | SameSite Strict cookie plus exact Origin on approval POST/DELETE; no CORS |
| Modified action or wrong resource | Immutable canonical action/digest, server-bound challenge, literal sandbox scope and generated schemas |
| Replayed assertion / wrong session | Atomic expiring challenge consumption, credential ownership, UV and real signature/counter verification |
| Signed unsafe instruction | Independent Node exact stop interlock and repeated native shield/certificate checks |
| Stale state / changed code | Database/native versions, source snapshot/binary/certificate hashes rechecked before CAS |
| Duplicate execution / timeout | Atomic snapshot/version/nonce/receipt update; identical retry returns one receipt; checkpoint reconciliation |
| Partial native computation | Private C++ copy discarded before commit; no live handle changes |
| Trace/source injection | Primitive-only checkpoint codec, bounded typed data, no dynamic code/pickle, no raw tokens in graph inputs |
| Privilege escalation | Separate telemetry, graph, authorizer and gateway Mongo roles; actual denial checks |

Node verifies a public key and cannot mint approval. The local Python API process
currently holds both authorizer and gateway configuration; process compromise is
inside the trusted boundary, and this is not OS process isolation for the graph.
Even a signed action is restricted to the fixed simulator stop by Node and the
gateway. Production deployment requires separately secured authorizer/gateway
principals, TLS, enterprise identity, credential lifecycle/revocation, external
audit anchoring and a hardened secrets store. None is silently claimed here.

Actual receipt chains detect partial/tampered state in reads. An administrator
rolling back the entire Mongo database can restore a self-consistent old chain;
detecting that requires an external trusted anchor. Single-Mongo local journaling
is not HA or an exactly-once distributed transaction. No blind reversal of a
committed safe stop reenergizes loads. The local browser test uses a labeled
virtual authenticator and real cryptographic verification; physical key acceptance
and hardware attestation remain unverified. See ADR 0012.

`tools/secret_scan.py` catches accidentally tracked generated local tokens and
private-key headers. It is a narrow baseline, not a general-purpose secret scanner.
Python and npm dependency audits are executed during the phase gate; production
release also requires container/OS scanning and the Phase 12 hostile audit.
