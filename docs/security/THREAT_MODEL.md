# Phase 1 security baseline

Assets: local viewer/service secrets, integrity and provenance of simulator frames,
local process availability. No real plant, privileged enterprise connector or
third-party credential is connected.

| Threat | Implemented control | Remaining limitation |
|---|---|---|
| Anonymous telemetry reads | Required bearer token; comparison uses constant-time library primitive | Shared local development identity, not per-user authorization |
| Viewer reaches write path | No API mutation route; independent Node service denies all mutations | Capability/WebAuthn authorization not implemented |
| Child output malformed/stalled | 16 KiB line bound, strict schema, contiguous versions, deadline, health failure | No watchdog restart or independent controller yet |
| Cloud impersonation/data substitution | No cloud client; edge URL restricted to local allowlist | TLS and remote identity deferred |
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

No physical safety claim is made: a software-only thermal sample is not a safety
controller. The fail-closed behavior demonstrated here concerns data validity,
authentication and the absence of mutation paths. Later phases must prove local
safety under cloud failure, WebAuthn replay/tampering controls and compensations.

`tools/secret_scan.py` catches accidentally tracked generated local tokens and
private-key headers. It is a narrow baseline, not a general-purpose secret scanner.
Python and npm dependency audits are executed during the phase gate; production
release also requires container/OS scanning and the Phase 12 hostile audit.
