# Sprint adversarial demonstration — PASS selected checks

`python tools/sprint_adversary.py` ran six named attack families through the
existing native/crypto implementation in the QA image with `--network none`.
All 13 selected assertions passed: native sensor spoofing/local latch (1), whole
manual conflict (1), malicious PDF text (1), signed unsafe proposal (1), stale
approved database state (1) and invalid WebAuthn proofs (8).

The raw JSON records exact selectors, source hashes and image identity.
Storage doubles are explicitly identified for the stale capability and WebAuthn
unit checks. These are separate from historical actual browser/server CTAP2,
Mongo compare-and-swap and commissioned receipt evidence; no claim of a new
hosted approval or physical-key ceremony is made. No provider or application
resource mutation occurred in this harness. Finite selected regression coverage
is not a security certification or evidence of all possible attack resistance.

Authenticated `/api/v1/analysis/sprint-evidence` exposes these recorded checks,
the held-out quality metrics, baseline comparisons and explicit limitations.
`/api/v1/analysis/forecast` is strictly observed-only, bounded to 121 frames and
never issues a capability. Its nginx body limit is scoped to that single route;
all other routes retain their existing limits. Two API tests pass for auth,
schema rejection, unavailable data abstention, ordering and recorded evidence.
Ruff, generated-contract drift and all-source strict mypy pass at integration.
