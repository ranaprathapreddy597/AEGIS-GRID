# Commissioned simulator policy review

Review scope: ADR 0015 and the separate commissioned rule, WebAuthn, capability,
executor, native gateway, storage and browser paths. Reviewer: Codex automated
engineering review with executable adversarial tests; no independent human
industrial assessment, OEM approval, physical passkey or production certification.
The signed package itself deliberately retains that limitation in its review status.

The package was authored and signed before its first native/live measurements.
Its 70 C bound, 65 C guard and existing flow/pressure/feeder/ramp limits were not
adjusted after observing an outcome. The signing key was a dedicated one-time
software fixture key; its private component was not retained. This signature
authenticates local engineering origin/integrity and is distinct from the real
Chromium WebAuthn approval signature used later.

## Reviewed boundaries

- Original manual library, PDFs, scenario registry, refusal artifacts, stationary
  plan/capability/receipt contracts and sandbox gateway policy remain unchanged.
  The new plant has its own collection, incident identity, policy revision,
  proposal type, capability issuer/audience, receipt and executor endpoint.
- New authorization is explicitly disabled by default. The local owner can select
  the simulator fixture using `AEGIS_COMMISSIONED_SIMULATOR_ENABLED=true`; this
  does not open physical I/O, enterprise connectors, a plant reset or a restart.
- All six loads/valves and the common pump are checked independently by Python
  Pydantic, the existing SafetyShield, native rollouts and the Node policy.
  Node pins the rule hash independently. No model/source can supply parameters.
- The incident is a frozen native trigger replay, not an unattended running plant.
  Its source SupervisedTwin remains enforcing and applies its own immediate stop.
- A hosted opinion is never an execution instruction. The new quality route
  rejects/retains abstentions and infeasible planning recommendations, and tries
  only the next reviewed model within existing total deadlines/reservations.
  Original calls retain their previous abstention semantics. No quota reset,
  failure refund, parallel model fan-out or retry after auth/429 is added.
- WebAuthn challenge bytes contain 32 random bytes plus the canonical plan digest.
  That immutable plan binds plant, incident, exact controls, rules, investigation,
  native snapshot/binary/version, nonce, duration and expiration. Owner session,
  RP/origin, UV, credential counter and distinct ceremony kind are verified.
- Capabilities stay server-side. Node verifies Ed25519, fixed issuer/audience,
  strict generated schemas, expiration, nonce and mirrored scope. The Python
  gateway verifies those independently, verifies durable human approval and
  immutable investigation, and recomputes the native certificate before mutation.
- The gateway evolves a private native copy. Receipt, native snapshot, version
  and consumed nonce commit together using Mongo compare-and-swap. Failed
  validation/simulation/commit discards the copy. Repeated execution is refused;
  authenticated receipt reads reconcile an interrupted response without another
  mutation. Source fault configuration must remain identical after cooldown.
- Separate collection ACLs allow graph report inserts, approver proposal writes,
  and gateway resource CAS. Graph/telemetry cannot update the resource, the
  approver cannot edit reports/resources, and the gateway cannot write credentials
  or approvals. Actual Mongo denials are required in the full gate.

## Findings addressed before live execution

1. Initial container bootstrap lacked the new fixture directory. Explicit Docker
   packaging was added; original failure logs are retained. No AMD call occurred.
2. Python/JavaScript can render floating-point JSON differently. New receipt
   measurement fields use explicit IEEE754 binary64 hex in the integrity hash;
   public measurements remain numeric and both independent verifiers check them.
3. A schema-valid abstention is insufficient for this demo. It now fails the
   commissioned admission gate, is retained in diagnostics, and is never counted
   as diagnosis success. Planning must select a supplied, feasible evaluation.
4. A report flag alone is insufficient. Admission rechecks source snapshot,
   native binary, artifact hash, all 37 adversarial cases, safe stop feasibility,
   unsafe challenger rejection, both source namespaces and grounded opinions.
5. A receipt cannot imply repaired equipment. The sole outcome is explicitly
   `simulated_safe_stop_cooldown`, with per-cell measurements and fault retention.

Focused native/crypto tests use explicit storage and opinion doubles; they are
not hosted or WebAuthn evidence. Only the separate actual provider/browser proof
can establish those parts. Full results, unresolved failures, source identity and
clean-source checks are recorded in results/COMMISSIONED_RECOVERY.md after execution.

Production threats remain outside this local demonstration: privileged process
or database administrator compromise, whole-database rollback without an external
anchor, production tenant IAM/TLS, physical interlocks/calibration, physical keys,
independent human industrial assessment and dedicated accelerator acceptance.
