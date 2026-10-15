# ADR 0004: Local read-only credentials; no operational writes

Status: accepted, 2026-10-14.

Generate separate random viewer/service/Redis/Mongo values in ignored `.env`.
Browser users explicitly enter a viewer token; no automatic unauthenticated token
bootstrap endpoint exists. Clear browser state on disconnect; no localStorage.
The viewer token permits reads only. Service credentials cannot trigger a write.

The local API uses HTTP only across isolated containers/loopback. It is not a
production identity or encrypted edge-to-cloud design. No remote mode can be
configured in Phase 1. TLS, human identity/passkeys, capability signing, revocation,
durable nonce state and tenancy must pass their later gates before any writes.

Only six health services and read telemetry are exposed. All Node mutation attempts
are denied even with valid service credentials. No bearer value appears in error
bodies, query strings, logs, screenshots or generated contracts.
