# Commissioned simulator incident recovery — 2026-10-17

**PASS: actual simulator safe-stop authorization and cooldown. PARTIAL: hosted
diagnostic specificity. BLOCKED: production/physical plant acceptance.**

The separate plant completed real AMD/dual-Pinecone LangGraph investigation,
native adversarial evaluation, an incident-specific WebAuthn challenge, genuine
Chromium virtual CTAP2 assertion, server verification, independent Node/Python
execution checks, native simulator mutation and a persistent receipt. This is a
frozen native incident replay, not a physical plant or an equipment repair.

## Fixture and rule origin

Plant `commissioned-simulator-01`, revision `commissioned-stop-v1`, uses a new
signed engineering package in `data/commissioned/`. SHA256:
`a22dbd91274b67c8fd7f099a5f5a36ede6e8382967d5eca6b699e4b7d0fbe4e7`.
The package and scenario were authored/signed before measurement; the dedicated
software signing key's private component was not retained. Trusted code pins
the public key and rule hash and verifies the Ed25519 signature and scenario
hash. This authenticates local engineering origin/integrity, **not OEM approval**.
The signed review status discloses the automated-review requirement and lack of
human industrial/OEM assessment. The separate automated review and tests are in
[COMMISSIONED_POLICY_REVIEW](../COMMISSIONED_POLICY_REVIEW.md) and ADR 0015.

Rules retain the existing 70 C hard limit, 65 C operating stop guard and native
flow/pressure/feeder/ramp constraints. The only authorized action is a shared
six-cell stop: pump=1, all six loads=0, all six valves=1, for 120 simulated seconds.
There is no fault clear, latch release, production restart, public reset, physical
I/O or enterprise command. The new setting is disabled by default and was
explicitly enabled only in the local demonstration configuration.

The separately pinned scenario is `scenario-910`, seed 73, sensor spoof fixture.
An unchanged enforcing SupervisedTwin detected a real anomaly at 378 simulated
seconds and captured its pre-stop snapshot. Its own native instance immediately
received the independent emergency stop. The commissioned resource is a frozen
fork of that captured trigger; its clock does not advance during cloud/HITL wait.
No running plant waits for this cloud or approval sequence.

## Actual hosted investigation

[Raw live proof](commissioned-live.json) preserves the exact evidence inputs,
validated opinions, provider attribution/diagnostics, licensed source references,
native assessment, immutable action, challenge, public virtual-authenticator
assertion, HTTP outcomes and receipt. The private CTAP2 key and owner cookie are
only in ignored local CI files, never in the evidence bundle.
The [original server report JSON](commissioned-persisted-report.json) also
preserves numeric formatting for reproducible canonical report hashing; browser
JSON serialization can normalize equivalent numbers such as `1275.0` to `1275`.

- Investigation `727bf9ff-c886-42e0-a360-e1e99b587d9c`.
- Incident `c6030cbab0496e16682e53f5d68ee0627dc532823211424f3674f1e5f276db44`.
- Two actual AMD inference POSTs and two catalog requests. Both served
  `self-dploy/DeepSeek-V4-Flash`, requested `DeepSeek-V4-Flash`, HTTP 200 and
  validated. No GLM/Qwen fallback or 429 was observed in this live run. The
  reviewed DeepSeek → GLM → Qwen order and six-attempt/32,768-reserved-token
  session cap are unchanged. No session was reset to obtain another opinion.
- Diagnosis latency 13,315.988 ms, 1,575 prompt + 66 completion tokens; planning
  9,882.942 ms, 1,448 + 33 tokens. Total acknowledged usage **3,122 tokens**;
  conservative reservation **10,778 tokens**. Hardware identity remains unverified.
- Eight actual Pinecone queries returned 200, supplying eight verified references
  from both existing namespaces. Their original tenant/plant, source hash,
  revision, license, attribution and applicability remain intact. They are context
  for the commissioned fixture, never relabeled as its safety authority.
- The cyclic Blue/Red path rejected the planted unsafe controls, revised to the
  exact stop, checked 37 native uncertainty cases and retained the 409-rollout
  numerical artifact. That reused search artifact remains explicitly non-executable
  with its original conservative gate labels; it does not grant authority. The
  separate authenticated commissioned certificate/policy governs this action.
- Dashboard run elapsed **48.7483 s**, including inference, retrieval, native checks,
  browser approval and execution. This is one development run, not a provider SLA.

### Diagnosis qualification and limitation

AMD returned `assessment=investigate`, evidence references to observed/residual/
trend/correlation/retrieved fields, and hypotheses:
`sensor_bias`, `restricted_flow`, `weak_pump`, `overload`. Planning returned
`emergency_stop`, citing `candidate_evaluations` and `retrieved_sources`.
Neither response was an abstention or a substituted local opinion.

The predeclared minimum admission criterion requires non-abstention, supplied
numeric evidence references, and overlap with independent physics hypotheses.
It passed on **sensor_bias**. The other three alternatives lack independent
support in this incident and remain **unconfirmed**. We do not count all four
as correct causes or claim precise/held-out diagnostic accuracy. Diagnostic
specificity is **PARTIAL**, recorded in [preservation/grounding evidence](commissioned-preservation.json).
Safety does not depend on choosing among these labels: only the independently
checked exact stop can be proposed or executed.

The commissioned quality route can reject/retain abstentions and infeasible
planning recommendations before trying the next reviewed model within the same
budget/deadline. HTTP contract tests verify this and auth/429 stop behavior.
The original graph's ordinary opinion/abstention behavior is unchanged.

## Approval and execution evidence

The canonical action binds plant/resource, incident, exact parameters, duration,
rule revision/hash, investigation ID/hash, native binary, snapshot/state/database
version, expiration and nonce. Challenge bytes contain 32 random bytes followed
by its SHA256 digest. A distinct server-side ceremony binds the owner session,
RP/origin, plant, incident, rule package and action nonce. The consumed assertion
is verified as ES256 WebAuthn with user verification and credential counter checks.
Only then is a separate 60-second Ed25519 executor capability minted; its raw
value never reaches the browser or evidence files.
The saved historical public assertion was also
[independently re-verified](commissioned-assertion-verification.json) with the
server's public COSE credential key and exact challenge/origin/RP. This offline
signature check did not mint authority or replay current counter admission.

The real Node executor verifies the signature, schemas, mirrored bindings and
all six controls; the Python gateway independently rechecks durable approval,
authenticated rules, report/source/binary binding, current native state, and fresh
native certificate. It evolves a private native copy and atomically commits
snapshot, version, consumed nonce and receipt. The approval LangGraph resumes
its durable interrupt only after verified approval. The sealed investigation
report remains its original pre-approval artifact; the separate approval view
and receipt carry the executed state.

Observed results:

| Measurement | Actual result |
|---|---|
| Investigation / WebAuthn verification / execution HTTP | 200 / 200 / 200 |
| Database version | 1 → 2 |
| Native state version | 378 → 498 |
| Hottest cell before / after | 42.3748099464 → 33.4510429263 C |
| Hottest-cell decrease | 8.9237670201 C |
| Native certificate peak across integration substeps | 42.3776003286 C, below 70 C |
| Peak pressure / feeder in certificate | 116.8831168831 kPa / 10414.94375 W |
| Receipt's one-second sampled maximum | 42.3748099464 C |
| Fault configuration after execution | Retained, unchanged |
| Committed receipts / consumed action nonces | 1 / 1 |

Per-cell temperatures, exact native snapshots and the approval audit are retained
in [before](commissioned-audit-before.json) and [after](commissioned-audit-after.json).
The certificate includes substep peaks; receipt temperature samples are at one
simulated second. No model-estimated outcome is substituted for native measurements.

Receipt SHA256:
`96b9c3f4338f75c56e452205fcfa446ee714a45303ab4c27a3775faea822ed2e`.
The new receipt integrity format encodes floating measurements as IEEE754 binary64
hex for hashing so Python and Node verify identical bytes; displayed values remain
numeric. This is a local hash chain, not an externally anchored production audit.

Two distinct actions against the same initial state received actual CTAP2/server
approval for the stale-state test; only the first executed. The second remains
approved but unexecuted, and its expired/changed-state authority cannot be reused.
[Stale approval evidence](commissioned-stale-approval.json) retains its server
signature-verification audit without exposing the capability.

Actual refusal HTTP results were all **403**: no approval, wrong origin,
assertion replay, changed action digest, repeat execution, and the separately
approved stale action. An original contradictory-plant investigation ID could
not create a commissioned proposal (403). Unit/native tests additionally cover
forged/expired/wrong-scope capabilities, per-cell parameter changes, corrupted
rules, changed snapshots/certificates/binaries and failure before atomic commit.

Screenshots: [investigation](commissioned-investigation.png),
[authorized cooldown and receipt](commissioned-authorized-recovery.png).

## Preservation and scope

Pinecone namespace counts before/after were **1,235 + 103 = 1,338**, with four
successful statistics reads across the two audits. There were **zero Pinecone
writes**, reuploads, overwrites or deletions. Combined provider operations in this
follow-up: eight queries, four stats reads, two AMD catalogs and two inference POSTs.

The original PDFs, 100 scenarios, vector snapshots/manifests, previous refusal
report and master/build instructions are unchanged. The original sandbox resource
snapshot/version/receipt chain is identical before and after this live workflow.
Its manual decision still returns `no_action`; the actual old action-producing
AMD report remains ineligible. Regression writes to the separate stationary
sandbox occur later and are not attributed to commissioned recovery.

The initial Docker bootstrap failed because the new package directory was not
copied into the image. An initial QA invocation also selected the previous image
before its replacement finished building and found no new test files. Both are
harness/packaging failures before any AMD call, retained separately. The corrected
focused suite passed 67 native/crypto/provider-contract tests before the live run.

## Reproduction and remaining gates

The [main full gate](commissioned-regression.txt) passed **379 Python / 3 CTest /
35 Node / 15 Chromium** tests, formatting/lint/type/build, generated contract and
fixture drift checks, dependency/secret audits, and actual API/storage/authorization
boundary checks. Newly captured regression browser evidence is in
`commissioned-regression-browser/`; original Phase 12 artifacts were restored.
Those later stationary-sandbox test writes are separate from the commissioned
run's before/after preservation audit.

The [clean bootstrap/demo](commissioned-final-clean-bootstrap.json) passed at
**180.006432 seconds**, in a new project with fresh credentials and storage.
Its virtual CTAP2 action is the existing stationary sandbox demonstration, not
another hosted commissioned recovery. Same-host Docker/download/browser caches
were reused; this is not a cold-machine or physical-key proof.
[Source identity](commissioned-source-identity.json) verifies the live runtime,
test/helper/fixture/contract/configuration sources match frozen Git tree
`002a7ec731d86ddacc86ff741e676c55ee70512a`. Only completion documentation and
evidence changed after export.
The [separate full clean gate](commissioned-final-clean-check-proof.json) also
passed **379 Python / 3 CTest / 35 Node / 15 Chromium**, with all configured
audits and actual API/storage/authorization checks. Its
[raw log](commissioned-final-clean-checks.txt) is retained. The export installed
its own frozen venv/node_modules; only proof containers/networks were stopped,
and all volumes plus the main stack were preserved. Both full gates observed
23 actual Mongo privilege denials with zero successful forbidden writes in that
boundary check. This does not imply a production security certification.
After the main gate's process restarts, authenticated
[delivery read-back](commissioned-delivery-readback.json) confirmed the identical
report and persistent receipt and re-verified their grounding/digests. The main
stack is restored to controlled hosted mode. These were reads, not another
provider probe, approval or execution.

See [commissioned runbook](../COMMISSIONED_SIMULATOR.md). The resource is deliberately
one-shot with no public reset. Read existing receipt/report evidence after success;
do not rerun the live execution proof or reset resources to improve a result.
Default/offline operation remains available. Fresh-source validation uses a new
isolated project, new credentials and storage; it does not overwrite this plant.

MI300X, Evolus, physical passkeys, independently reviewed industrial rules,
production IAM/TLS/process isolation, external audit anchoring, NASA provenance,
hardware interlocks/calibration and physical plant acceptance remain BLOCKED or
unverified. No enterprise connector, deployment, release tag or physical action
was enabled. No OEM approval, repaired equipment or production restart is claimed.
