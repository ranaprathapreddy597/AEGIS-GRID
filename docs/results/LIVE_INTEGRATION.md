# AMD hosted + Pinecone synthetic integration — 2026-10-16

This is synthetic simulator acceptance, separate from dedicated MI300X, Evolus,
physical plant and production acceptance. The user explicitly authorized the
Pinecone upserts. No unrelated records were deleted and no HITL gate was bypassed.

| Gate | Actual result |
|---|---|
| Index identity | PASS: authenticated control-plane HTTP 200; `aegis-grid-memory`, ready, dense 256 dimensions, cosine, configured host matched |
| Real semantic model | PASS: pinned `minishlab/potion-base-8M`, native 256 dimensions, artifact hashes recorded; no random/padded/truncated vectors |
| Corpus | PASS: 1,235 unique versioned chunks: 1,000 manual, 100 scenario, 102 incident, 33 recovery; all explicitly synthetic |
| Main upserts | PASS: 25 HTTP 200 batches, 1,235 acknowledged vectors, zero failed/unconfirmed IDs |
| Persistence/idempotency | PASS: namespace count 0 → 1,235; identical two-record repeat leaves count 1,235 |
| Retrieval quality | PASS on 12 fixed development queries: 12/12 top-1 and top-5 relevant; not held-out or industrial accuracy |
| Metadata isolation | PASS: wrong-tenant query returns zero; returned source/text/revision/model metadata checked against local manifest |
| Test cleanup | PASS: separate two-record test namespace 2 → 0, HTTP 200 upsert/delete/stats; main corpus retained |
| Hosted LangGraph | PASS for connectivity/validation: real new native fault → Pinecone manual/recovery retrieval → two AMD HTTP 200 validated opinions → numerical adversarial planning → native recovery rollout → approval interrupt |
| Hosted reasoning reliability | PARTIAL: graph diagnosis/planning abstained; stronger diagnostic case validates DeepSeek and Qwen, GLM hits bounded ReadTimeout |
| Full regression/security/clean-source | PASS: main full gate 298 Python; final clean-source gate 299 Python / 3 CTest / 16 Node / 14 browser, audits/contracts/storage/authorization checks |
| Dedicated MI300X / Evolus / production | BLOCKED; no hardware/runtime/provider execution proof or production acceptance implied |

Evidence is in `live-knowledge-ingest.json`, `live-knowledge-graph.json` and
`live-amd-diagnostics.json`. The retained main namespace is
`aegis-synthetic-v1-6e4d75051cbcaf1e`. The initial stored-incident graph run is
retained separately as `live-knowledge-graph-initial.json`; final acceptance
generates a new native scenario-090 fault rather than inventing an incident.

Ingestion took 87.511 seconds on this host including metadata, embedding,
upserts/counts, 13 queries, idempotency and cleanup checks. That is one end-to-end
sample, not a provider latency SLA. Repeat embeddings were bit-identical, finite
and normalized. Coolant-blockage versus flow-obstruction cosine was 0.255859;
versus unrelated music/dancing was 0.003524. These two pairs are a sanity check,
not a semantic benchmark. The 12-query set and every returned ID are published.

The final graph records exact source references and measured token usage. Its
two hosted opinions used 1,973 reported tokens. Both requested DeepSeek-V4-Flash
and matched the reviewed `self-dploy/DeepSeek-V4-Flash` response alias. Diagnosis
abstained and planning recommended abstention, so numerical reasoning and the
independent latched stop remained decisive. The actual native minimax search ran
409 rollouts / 4,908,000 physics substeps. The planted flawed candidate failed;
the stop counterfactual peaked at 41.1040 Celsius. These are simulator predictions,
not physical recovery or a protected execution receipt. Full-corpus contradictory
manual evidence still forces `no_action` and the graph pauses at HITL.

Routing is preserved: DeepSeek-V4-Flash → GLM-5.3-Flash → Qwen3.8-Flash-Next.
The separate focused live diagnostic used one small synthetic sensor case per
model. DeepSeek validated in 3,115.48 ms and Qwen in 16,178.32 ms, each returning
`investigate` with allowed hypotheses/references. GLM timed out. Earlier observed
429 and validation failures remain in the historical AMD evidence; their original
text was not retained, so no retrospective cause is asserted. New field/stage
diagnostics, malformed-envelope tests and strict reference validation make future
failures distinguishable. HTTP doubles prove ordered timeout fallback, exact alias
rejection, tool/command injection refusal, bounded quota circuits and no fanout
after 401/403/429. They are not live reliability measurements.

The normal Compose application stays offline by default. The explicit hosted
runner invokes the same LangGraph implementation using real provider adapters
and an in-memory primitive-only checkpoint saver. `InvestigationService` also
accepts explicit hosted/retrieval adapters with Mongo checkpoints; automatic
provider credentials/egress are not injected into the default local service.
Hosted Mongo checkpoint acceptance has not been separately demonstrated; local
Mongo checkpoint/restart/isolation gates remain part of regression. Production
multi-tenant identity, egress deployment, physical WebAuthn keys, calibration,
IAM/TLS and dedicated GPU gates remain unverified.

## Validation log

The initial regression passed 291 Python tests, 3 CTest cases, Node tests,
contracts, scans and local API/storage checks. Its browser segment overlapped a
local stack rebuild and failed three cases. The full raw log is preserved as
`live-integration-checks-initial.txt`; this is not counted as a passing full gate.
The subsequent stable main gate passed 298 Python / 3 CTest / 16 Node / 14 browser
tests, dependency/secret scans, generated contracts/types, real HTTP/SSE and
Mongo/Redis checks. One additional absent-reference refusal test and its client
hardening then passed the 29-test focused adapter/retrieval suite. The final
clean-source gate includes that change and passes 299 Python / 3 CTest / 16 Node /
14 browser tests plus all prior scans/contracts/transport/storage/authorization
checks. The final runtime source, contracts and lockfiles match the export; only
instructions, README files, completion documentation and evidence changed afterward.
No failure is waived and no release tag is authorized.

Executed commands (project virtualenv Python):

```text
python tools/live_knowledge.py ingest
python tools/diagnose_hosted.py
python tools/dev.py start
python tools/run_hosted_graph.py
python tools/dev.py check
python tools/clean_demo.py --evidence-prefix live-integration
python tools/check_clean_source.py --evidence-prefix live-integration
```

The fresh-source export is `a33d50206fb4c35b8ae5ab2ccca8637d85fcde0b`, project
`aegis-proof-68dbffb2`. Its actual browser demo ran 180.0068 seconds with a virtual
CTAP2 authenticator and real server ES256 verification, independent executor,
local native stop and local Mongo receipt. The separate installation used new
host venv/node_modules and its isolated proof database/credentials. Docker layers,
downloads, browser tooling and the OS were reused; this is not cold-machine proof.
Only proof containers/networks were stopped; all volumes and main stack retained.

Proof files: `live-integration-checks.txt`, `live-integration-clean-bootstrap.json`,
`live-integration-clean-checks.txt`, `live-integration-clean-check-proof.json` and
`live-integration-demo/proof.json` (plus actual video/screenshots). Original
Phase 12 browser evidence was restored; new captures are in
`live-regression-artifacts/`. Logs preserve actual output whitespace.

The hosted fault/Pinecone/AMD/native graph was repeated against the image built
from the clean export: PASS in 17.5494 seconds, two validated DeepSeek opinions,
1,973 provider-reported tokens, exact source references and a protected approval
interrupt. This connectivity/validation pass does not turn the abstentions into
successful hosted diagnoses. The in-memory hosted checkpoint scope and separate
local persistent/HITL acceptance remain explicitly distinguished.

`live-knowledge-final-count.json` records an additional authenticated HTTP 200
stats read after graph/cleanup acceptance: the retained main namespace still has
exactly 1,235 records. No provider key, raw reasoning, secret value, release tag,
enterprise mutation or production deployment is part of this evidence.
