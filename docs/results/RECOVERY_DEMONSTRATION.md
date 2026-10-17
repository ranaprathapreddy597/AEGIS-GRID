# Final recovery demonstration — 2026-10-17

Overall **BLOCKED** for complete incident recovery. Scenario A is **BLOCKED**;
Scenario B is **PARTIAL**. No incident authorization or recovery is claimed.
The two real hosted investigations and their refusal paths are persisted and
replayable in the dashboard. Safety rules and original manuals are unchanged.

## Why no safe authorized scenario can currently qualify

The original pinned 1,000-page plant corpus includes simultaneous R1 70 C and
R2 95 C limits for CELL-01 without authenticated supersession. The existing
decision function returns `no_action` for every one of the six cells. The
available stop affects the shared six-cell plant; selecting another cell or
excluding the bulletin would evade the current gate. Static eligibility review
of the 100 registered scenarios (90 fault scenarios) found no qualifying
noncontradictory plant-wide rule set. This is a registry/manual audit, not a
claim to have rerun all 100 native simulations in this follow-up.

Separately, the existing signed capability/executor contract permits only
`authorization-sandbox-01`, policy `authorization-test-sandbox-v1`, and rejects
nonzero fault masks. A stationary sandbox signature cannot authorize recovery
of either incident. We did not widen that contract, remove a source, issue an
incident-specific challenge, or substitute a sandbox approval for Scenario A.

## Actual live scenarios

See [raw evidence](recovery-scenarios-live.json), including complete incident
records, fault fixture hashes, observed histories, snapshots, opinions, source
references, native forecasts, provider diagnostics and protected-state snapshots.
The unchanged supervised twin generated both incidents; no observe-only mode or
fault label was substituted for the actual anomaly detector. Observation was
bounded to the existing 600-second benchmark horizon.

| Case | Native fixture | Actual hosted result | Safety/authorization result |
|---|---|---|---|
| A — BLOCKED | scenario-010, sensor spoof, detection at 380 simulated seconds | DeepSeek diagnosis `insufficient_evidence`; DeepSeek planning `minimax_candidate`, referencing candidate evaluations and retrieved sources | Native adversary checked candidates, but shared manual conflict and unsupported incident gateway scope block approval. Meaningful diagnosis criterion also fails. No recovery. |
| B — PARTIAL | scenario-090, cascade fault, detection at 110 simulated seconds | Diagnosis route exhausted validation/transport fallbacks; DeepSeek planning `abstain` | Unsafe first challenger rejected, manual conflict retained, no authorization. The specific requested condition of AMD recommending an action in B was not demonstrated. |

A does show an actual AMD action recommendation remaining blocked by independent
rules. It does not establish successful diagnosis, approval or recovery, and is
not relabeled as the requested distinct B proof. Each performed 409 native
minimax rollouts with a `checked_non_executable` assessment. Both graphs end at
`paused_no_action`. Existing automatic emergency supervision is independent of
these graphs; it is not a WebAuthn-authorized recovery operation.

The successful pair took 87.8302 seconds. One shared client enforced the existing
aggregate six-model-request/32,768-reserved-token budget across both scenarios:
six actual AMD POST attempts, four catalog requests and 30,407 conservatively
reserved tokens. There were three accepted opinions (4,124 acknowledged tokens).
Failed-attempt usage is unknown, not zero. The fixed routing order remains
DeepSeek → GLM → Qwen. Diagnostics retain a reference-validation rejection,
GLM ReadTimeout and an unfinished/empty Qwen response. No retries beyond the
bounded client/session budget were made to force success. No 429 was observed.
Served model identity is recorded; dedicated accelerator hardware is unverified.

Pinecone returned HTTP 200 for 16 queries and four statistics reads. Both runs
retain eight verified references spanning both namespaces, including revision,
hash, synthetic label, license, attribution, tenant and applicability. Counts
remained **1,235 synthetic + 103 real-world = 1,338**. There were **zero Pinecone
writes**, uploads, overwrites or deletions. External OEM references remain
untrusted context, with no authenticated mapping to this simulated plant.

Protected state was identical before and after: 45 historical proposals, 42
historical capability records, zero ceremonies, executor version 21 and 20
historical receipts; snapshot and last receipt hashes also match. The deltas are
**zero new proposals, challenges, capabilities, protected writes or receipts**.
Historical sandbox receipts are not incident recovery evidence.

## Application and browser evidence

[Browser/API evidence](recovery-browser.json) passes both cases: actual dashboard
selected-incident replay, idempotent investigation POST/read-back HTTP 200 with
identical persisted reports, SSE investigation/complete frames HTTP 200,
authenticated recovery eligibility GET 200, and mutation attempt 405. No extra
inference or passkey ceremony was performed during replay. Screenshots:
[A](recovery-scenario-A.png), [B](recovery-scenario-B.png).

The new authenticated, rate-limited read-only eligibility endpoint and dashboard
panel expose the exact incident, full corpus hash, contradictory citations,
diagnosis/plan qualification and blockers. Its frozen generated contract cannot
represent `eligible=true`, `challenge_issued=true` or `capability_issued=true`.
It does not create an alternative authorization mechanism. The dashboard now
investigates the journal-selected incident instead of silently choosing latest.
Hosted diagnosis additionally receives existing observed trends/correlations;
no private fault truth or commands are added to the model boundary.

After the main regression gate, the main application was restored to explicit
hosted mode and both persisted incidents passed authenticated
[final eligibility read-back](recovery-delivery-readback.json). These were reads
only, with no new investigation, approval or execution request. Offline mode
remains available with `python tools/hosted_mode.py offline`.

## Retained failures and reproducibility

The initial harness stopped before AMD inference because 300 seconds was shorter
than the registered spoof detector's 380-second detection time. The next attempt
failed typed-history validation before AMD inference. Both original evidence
files are retained: [horizon](recovery-initial-horizon-failure.json),
[history](recovery-initial-history-failure.json), with original
[horizon traceback](recovery-initial-horizon-failure.txt) and
[history traceback](recovery-initial-history-failure.txt). Each made only two Pinecone
statistics reads and zero model requests. The repaired harness uses typed
observations and the existing 600-second horizon, with native regression cases
for both fixtures. Original failures are not rewritten as successes.
Across all three harness attempts, this follow-up made 16 Pinecone queries,
eight statistics reads, four AMD catalog requests and six AMD inference attempts.

Run `python tools/recovery_scenarios.py` only with explicitly configured hosted
credentials and cached pinned knowledge/embedding artifacts; it performs new
bounded live reads/inference and saves new UUIDs. Preserve old evidence before
rerunning. `node tools/check_recovery_browser.mjs` replays the saved IDs without
new inference. It intentionally uses their existing idempotency keys rather
than creating another investigation. Original files and keys remain local.

## Validation scope

The [main full gate](recovery-regression.txt) passes **332 Python / 3 CTest /
16 Node / 14 Chromium** tests, Ruff, strict mypy, generated-contract and fixture
drift checks, lint/type/build, dependency/secret audits and actual storage,
transport and authorization boundary checks. Browser stream interruptions logged
during deliberate service restarts were followed by passing reconnect tests.
Fresh main browser artifacts are in `recovery-regression-browser/`; original
Phase 12 files were restored unchanged. These sandbox regression operations
occurred after the live scenarios' protected-state snapshots and are not
attributed to those scenarios.

The [separate full clean gate](recovery-final-clean-check-proof.json) also passes
**332 Python / 3 CTest / 16 Node / 14 Chromium**, all configured scans/audits and
actual API/storage/authorization checks. Its [raw log](recovery-final-clean-checks.txt)
is retained. The proof export installed its own frozen venv and node_modules;
only proof containers/networks were stopped and every volume/main service was
preserved. The main stack remains healthy in controlled hosted mode.

[Clean bootstrap](recovery-final-clean-bootstrap.json) passed the actual
180.0182-second browser demo in a new Compose project with new credentials and
storage. Its virtual CTAP2 approval, server signature verification, independent
executor and persistent receipt apply only to the existing stationary sandbox,
not A or B. Same-host Docker/download/browser caches were reused; no cold-machine,
physical-key or provider hardware acceptance is inferred.
[Source identity](recovery-source-identity.json) verifies unchanged executable,
test, helper, fixture, generated-contract and configuration sources relative to
frozen tree `d056438ff740f79f6dabb6db4010a212d008ba11`. Completion documentation
and evidence were added after that export.

## Remaining acceptance gates

Scenario A requires authenticated, consistent, applicable shared-plant evidence
and a separately reviewed incident-bound authorization/executor implementation,
plus meaningful hosted diagnosis. These are substantive missing gates, not a
request to disable checks. B needs a separately budgeted real action-producing
provider run before its exact conditional claim can pass. Do not invent either.
MI300X, Evolus, NASA license/provenance, physical passkeys, production identity,
external audit anchoring and physical plant acceptance remain BLOCKED/unverified.
No deployment, release tag, physical I/O or production acceptance occurred.
