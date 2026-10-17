# Unified cloud integration — 2026-10-17

Overall PARTIAL: live guarded investigation PASS; useful hosted diagnosis
reliability PARTIAL and incident WebAuthn/recovery authorization BLOCKED by
conflicting manuals. The cloud investigation demo is ready through that boundary.
The final real browser/API run completed in 25.0848 seconds using existing
Pinecone data and a native recorded factory anomaly. No dataset was regenerated
or reuploaded, and no record was deleted or overwritten.

## Actual external operations

Recorded Pinecone reads across this follow-up: 156 (83 snapshot reads, two
28-operation retrieval checks, 16 investigation queries and one final stats read).
The two inference workflows recorded six model POST attempts in total: four in
the initial run and two in the successful run. Only the final two have durable
per-attempt HTTP/schema diagnostics; failed-call billing/usage is unknown.

- `cloud-knowledge-snapshot.json`: 15 list + 68 fetch HTTP 200 operations read
  all 1,338 existing records into integrity-pinned ignored local snapshots.
- `cloud-retrieval-live.json`: 24 query + four stats HTTP 200 operations; counts
  before/after remained 1,235 / 103. Six fixed development checks passed source
  recall@4 with both namespaces present. This is not held-out diagnosis accuracy.
  This check was repeated after namespace hardening; its original receipt is
  `cloud-retrieval-before-hardening.json`. `cloud-final-counts.json` independently
  confirms unchanged counts after the hosted UI workflow.
- `cloud-ui-live.json`: actual dashboard, authenticated POST/SSE/read-back HTTP 200,
  streamed checkpoints and identical persistent report. Eight Pinecone queries;
  two AMD catalog requests and two model POSTs. Both model POSTs returned HTTP 200
  and passed identity, strict schema, references and usage checks. Requested
  DeepSeek-V4-Flash; served `self-dploy/DeepSeek-V4-Flash` for both roles.
- Diagnosis: 3,059.54 ms; 1,251 prompt + 22 completion tokens; abstained with
  `insufficient_evidence`. Planning: 2,864.58 ms; 1,332 + 34 tokens; proposed
  `minimax_candidate`. Total acknowledged usage: 2,639 tokens. No provider errors
  in the final run. Dedicated hardware identity remains unverified.
- Eight source citations preserve namespace, license, attribution, revision,
  source hash and simulator applicability. Actual native adversarial evaluation:
  409 rollouts. The report reaches `paused_no_action`; independent manual and
  emergency controls prevent execution despite the model's planning recommendation.

## Retained failures and limits

`cloud-ui-initial-failure.json` retains the first run: eight Pinecone queries,
four model attempts, diagnosis route failure, valid planning abstention, safe
interrupt and a browser expectation failure caused by a display-label defect.
Its end-to-end harness elapsed time was 495.94 seconds; graph trace records a
64.715-second detective step including retrieval and the 60-second hosted route.
The display defect was fixed. Sanitized per-attempt diagnostics are now durable
in reports; exact original diagnosis rejection details were not retained and
cannot be reconstructed. A separate startup connection refusal performed no
provider calls and is retained in `cloud-ui-startup-refusal.json`.

No claim is made that provider reliability was repaired merely because a later
run passed. Diagnosis abstention remains a meaningful limitation. Existing
GLM timeout evidence remains applicable; fallback order is unchanged.

Post-live review added a strict synthetic-result namespace guard and serialized
lazy initialization so concurrent first requests cannot create independent quota
sessions. Seven focused boundary tests pass, including eight simultaneous HTTP
reads sharing one hosted service. Final live retrieval checks and final clean-source
gates cover this hardening. The retained hosted UI receipt predates those two
hardening changes; no further AMD inference was issued just to replay its opinions.

The guarded cloud investigation/citation/streaming demonstration is verified.
Incident execution remains BLOCKED by conflicting manuals. Actual WebAuthn is
tested independently in the stationary sandbox; no incident passkey approval
was fabricated. Dedicated MI300X, Evolus, external writes, production tenancy
and physical plant acceptance remain BLOCKED. NASA license/provenance remains
blocked from the earlier acquisition task.

## Regression and clean source

The main regression gate passed 325 Python / 3 CTest / 16 Node / 14 browser tests,
contracts, strict mypy, Ruff, scans, dependency audits and actual storage/graph/
authorization checks. Its raw output is `cloud-regression.txt`; newly captured
screenshots are in `cloud-regression-browser/`. Historical phase-12 screenshots
were restored only after copying the newly measured evidence to this folder.

After hardening, the final frozen-source full gate passed **326 Python / 3 CTest /
16 Node / 14 browser tests**, contracts/type/style checks, scans, audits and actual
storage/authorization checks. Graph credentials incurred three actual Mongo denials;
authorization checks incurred fourteen privilege denials and zero successful
operational writes. See `cloud-verified-clean-checks.txt` and
`cloud-verified-clean-check-proof.json` (PASS).

`cloud-verified-clean-bootstrap.json` and `cloud-verified-demo/proof.json` record
the separate actual **180.012692-second** browser demo, fresh generated credentials,
isolated storage and real server ES256 verification of a Chromium virtual passkey.
This is not a physical authenticator or plant acceptance proof. Frozen source tree:
`00707e8482cd2a3c27b2ac599e5f16854607bdfb`. Host venv/node_modules were installed
separately for the full gate; Docker/download/browser caches were reused on the
same host. `cloud-source-identity.json` confirms application and test sources match
that export; only documentation/evidence changed afterward.

Two preliminary 180-second source exports also passed before the final hardening;
their bootstrap summaries are retained as `cloud-unified-clean-bootstrap.json`
and `cloud-final-clean-bootstrap.json`. Their videos/screens remain locally in
ignored `.run/cloud-preliminary-proofs/`; the committed final demo is authoritative.

Configuration and repeatable read-only commands are in `../CLOUD_WORKFLOW.md`.
Delivery leaves the local application in explicit `amd_hosted` mode with offline
mode still available. `cloud-delivery-mode.json` verifies healthy HTTP 200,
anonymous access denied (401), hosted configuration and an identical persisted
cloud report read by the final backend. This initializes the pinned adapters but
issues no additional provider requests. Final repository scan: 674 files,
no local tokens/private keys found. No release tag, remote publication or physical
plant acceptance is claimed.
