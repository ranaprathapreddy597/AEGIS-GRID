# Commissioned simulator incident authorization

Status: implementation design frozen before live measurement, 2026-10-17.
Origin: repository engineering fixture, requested by the local simulator owner.
Review: automated policy/security review and adversarial tests required; no human
industrial assessor or OEM approval is asserted. Production acceptance is blocked.

Use a new plant `commissioned-simulator-01`, new resource/proposal collections,
new exact contracts and new executor route. Do not widen stationary sandbox
contracts, revise original PDFs/scenarios, reingest Pinecone, or exempt a shared
cell from the stop. Preserve original whole-corpus refusal.

The engineering rule package is signed by a dedicated software fixture signing
key, whose public key and content hash are pinned in trusted code. This proves
local package integrity/origin only. It does not authenticate real OEM rules.
It retains 70 C hard maximum, 65 C operating stop guard, existing ramp/flow,
pressure and feeder bounds, and permits only pump=1, six loads=0, six valves=1.
Every branch is checked. No fault clear, latch release, production resume,
enterprise mutation, physical I/O, arbitrary parameter, source-derived command
or alternate plant is permitted.

The commissioned resource is a frozen native incident replay fork at the actual
Sentinel trigger, captured before the supervisor's emergency command. The source
supervisor remains enabled and immediately stops its own native instance. No
wall-clock plant progresses while awaiting approval. This is an isolated replay
demonstration, not a claim that a live plant waits for a human or cloud service.
Authorized recovery means 120 simulated seconds of exact safe-stop containment
and measured cooldown with the injected fault retained. It is not fault repair.

Real AMD diagnosis and planning plus both existing Pinecone namespaces are
required by the hosted demo admission gate. Diagnosis must be non-abstaining,
cite observed numeric evidence, and agree with independent physics hypotheses.
Planning must be non-abstaining and cite evaluated candidates and retrieval.
All retrieved chunks remain context only; metadata/tenant identity is preserved,
never relabeled to claim commissioned-plant authority. A bounded cyclic
LangGraph performs evidence, diagnosis, manual verification, 409 native minimax
rollouts, explicit unsafe challenger rejection, exact-stop referee, and approval
interrupt. Local regression can test this machinery with labeled opinion doubles,
which are never evidence for the hosted demo.

WebAuthn challenge: random 32-byte nonce plus SHA-256 canonical action binding,
stored once server-side with owner session, plant/incident, rule revision/hash,
exact controls, snapshot/version, investigation hash, expiration and action nonce.
Verify ES256 WebAuthn origin/RP/UV/counter; consume challenges before verification.
Only then mint a 60-second Ed25519 executor capability. The separate Node policy
checks signature, schema and every mirrored binding; the Python gateway independently
rechecks rules, immutable report/incident/approval, current snapshot, native binary,
native safety certificate and all-six-cell exact controls. Private native evolution
and receipt/nonce/version commit use one Mongo compare-and-swap. Repeated capability
use is refused; receipt reads provide reconciliation without re-execution.

Required negative checks: missing/forged/expired/wrong-scope capabilities,
cross-plant/incident/rule/nonce/digest/parameter substitution, changed snapshots,
replayed assertions/capabilities, no approval, unsafe cells, failed native rollout,
partial commit and wrong owner/origin. Physical and enterprise routes stay absent.
Original contradiction gate must still reject action-producing model opinions.
