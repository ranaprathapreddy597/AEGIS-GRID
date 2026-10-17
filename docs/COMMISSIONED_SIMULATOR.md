# Commissioned simulator runbook

This separate fixture demonstrates authorized **safe-stop containment and
cooldown**, not equipment repair or production restart. Its original enforcing
source twin stops immediately; the authorized resource is a frozen replay fork.
Original contradictory-manual investigations remain closed. See ADR 0015,
COMMISSIONED_POLICY_REVIEW.md and results/COMMISSIONED_RECOVERY.md.

## Configuration and operation

1. `python tools/dev.py start` builds, provisions scoped local storage and uses
   administrative `$setOnInsert` for the new signed fixture. An existing resource
   is never reset. Fresh configuration disables commissioned authorization.
2. In the ignored local `.env`, explicitly select
   `AEGIS_COMMISSIONED_SIMULATOR_ENABLED=true` when this simulator fixture is
   intended. Existing approval/DB credentials are still required; do not paste
   them into reports or source control. Physical and enterprise actions stay absent.
3. For real inference, retain the existing read-only knowledge/model artifacts and
   provider configuration, then run `python tools/hosted_mode.py hosted`.
   No ingestion or snapshot regeneration is required. Default/offline mode is
   `python tools/hosted_mode.py offline`; a useful hosted opinion is required for
   commissioned proposal admission, so offline mode abstains from that authority.
4. In the localhost dashboard, connect the viewer, start an owner session and
   enroll/select a passkey in “Ask first. Verify again.” The viewer cannot enroll,
   approve or execute. The commissioned panel is a separate plant/workflow.
5. Investigate the commissioned incident. Inspect raw diagnosis, sources, native
   challenge results and fixed-rule applicability. A schema-valid abstention,
   unavailable provider, infeasible recommendation or missing source blocks the
   proposal; do not reset the API session to evade budgets.
6. Prepare the incident-bound proposal, inspect its immutable JSON/digest and exact
   shared six-cell stop, approve with the passkey, then execute the approved action.
   The actual executor verifies signature/state/rules again before committing.
7. Read the persistent receipt, all six before/after temperatures, native version
   and snapshot hashes. The fault remains injected and productive restart stays
   disabled. The resource is one-shot: no public reset or repeat execution exists.

## Evidence helpers and tests

- `python tools/commissioned_audit.py before` and `... after` perform actual
  read-only namespace statistics, resource/rule integrity and receipt audits.
  They make no model calls or Pinecone writes. Preserve existing evidence before
  using these fixed filenames for another independent fixture run.
- `node tools/check_commissioned_live.mjs` performs the real dashboard/AMD/
  dual-Pinecone/native/virtual-CTAP2 workflow and negative approval checks. It
  reuses its saved investigation UUID on an interrupted retry and refuses to
  overwrite a successful one-shot proof. It never substitutes a diagnosis or
  hand-constructs an approval signature. Only public assertion data is retained.
- Existing `.run/webauthn-ci.json` and `.run/commissioned-browser-state.json` are
  ignored, private local CI material. They must never be committed or logged.
  Chromium CTAP2 is a virtual authenticator, not physical hardware acceptance.
- `python tools/dev.py check` includes the new strict policy/native/API/browser
  regressions and existing original contradiction, crypto, boundary and security
  checks. Explicit unit opinion/storage/signing doubles are not live evidence.
- `python tools/clean_demo.py --evidence-prefix commissioned-final`, followed by
  `python tools/check_clean_source.py --evidence-prefix commissioned-final`, tests
  a staged source export with its own project, credentials, storage, venv and
  node_modules. The automated clean demo exercises the existing offline stationary
  sandbox, not another hosted commissioned recovery. No paid provider credentials
  are copied into its source or environment. Same-host caches are reused.

After a successful run, use authenticated read APIs rather than attempting another
execution. Reproducing an additional live run requires a separately named isolated
Compose project/storage with the same pinned fixture and explicit hosted settings;
preserve the earlier evidence and respect provider quotas. Do not delete/reset
the completed resource or alter the signed rules to improve an outcome.

API surfaces are `/api/v1/commissioned/status`, read-only commissioned reports,
and owner-cookie routes under `/api/v1/approval/commissioned/`. The Node route
`/v1/commissioned/execute` and protected API route `/internal/v1/commissioned/execute`
are private network/service-token surfaces; nginx returns 404 for `/internal/`.
Capabilities are not browser API responses. Receipt reads reconcile an interrupted
response without creating another operational write.

MI300X/Evolus, production identity/TLS, physical keys/interlocks/calibration,
external audit anchoring, independent industrial/OEM review and physical plant
acceptance remain blocked or unverified.
