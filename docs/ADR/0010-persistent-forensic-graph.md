# ADR 0010: bounded forensic graph, isolated native forecasts and checkpoint authority

Accepted 2026-10-16. User accepted Phase 6 local gate and authorized sequential
Phases 7–12 with the existing local backend. External live gates remain blocked.

Use pinned LangGraph 1.2.15 and langgraph-checkpoint-mongodb 0.5.1, inspected from
upstream package metadata and installed source. A real StateGraph runs Sentinel,
Collector, Detective, Manual Expert, Forecaster, Blue, Red, Referee, Shield,
Reporter and durable Approval interrupt; Executor/Verifier exist as closed nodes.
Red rejection routes back to Collector and revised Blue controls. The graph is
bounded to three iterations, 64 framework steps and 80 trace entries. Candidate
and opinion schemas have no execution authority. No public graph resume route.

The local backend is the previously implemented deterministic abstention template,
not a local generative LLM. Physics reasoning is executable numerical/rule code,
not a simulated conversation between invented AI personas. Sensor/thermal
hypotheses use explicit heuristic support scores, not calibrated probabilities.
The optional remote adapter is connected at the interface but refuses while the
MI300X/budget-preflight live gate is blocked. No fake model tokens, price or GPU
timing: offline token usage is zero and monetary cost is unknown/null.

New incidents persist an allowlisted SensorFrame, up to 21 actually delivered
temperature samples and residual evidence. Collector computes temperature slopes
and neighbor Pearson correlations; constant channels are undefined/null. Repeated
or regressing sampled times from transport delay are excluded from trends. Raw
snapshot history is not used: it can contain undelivered measurements.
Detector/model inputs exclude hidden truth, fault masks, scenario labels, seed
and snapshot internals. Tests capture actual backend inputs to enforce this.
Historical incidents without SensorFrame use residuals only and cannot support
claims about absent channels. Native forecasts restore complete validated
snapshots into separate C++ handles. Hidden simulator parameters are used only
inside that referee, never as diagnostic labels. Both baseline and candidate
120-second futures are actually stepped, with the executing binary hash recorded.
These are model-informed counterfactuals, not physical measurements or a robust
uncertainty certificate. Genuine robust search is Phase 8.

Red initially tests a productivity candidate against a latched-stop constraint;
its rejection creates feedback and a zero-load/max-cooling candidate. The
independent Phase 3 SafetyShield checks exact allowlisted controls/version again.
Manual Expert checks the complete corpus independently of FAISS top-k: the
unresolved bulletin pauses action even if the candidate's native rollout passes.
No graph result may override the running edge emergency latch.

MongoDBSaver persists real framework checkpoints/writes using separate
`aegis_graph` credentials. This identity has find/insert/update/listIndexes only
on graph_checkpoints and graph_writes. It has no plan/action/audit write privileges;
actual Mongo refusal checks enforce that. Monitoring identities remain append-only.
The bootstrap migration creates unique indexes and 30-day created_at TTLs. Saver
TTL is enabled after construction to avoid the inspected 0.5.1 helper's list/tuple
comparison causing runtime attempts to recreate an already matching TTL index.
Runtime credentials never receive index/admin privileges.

The custom serializer supports only primitive JSON, tagged bytes/tuples and the
fixed LangGraph Interrupt data type. Dict/list encodings are wrapped so source
text cannot impersonate codec tags. No pickle, dynamic import, arbitrary class
construction or model-provided callable. Checkpoints are capped at 2 MB. Local
checkpoint quota is 5,000 documents (single API worker); it is not a distributed
quota/tenant guarantee. API admits one investigation at a time and uses explicit
UUID idempotency keys, bound to immutable incident IDs. Different incidents cannot
reuse a key. Traces stay local; external LangSmith tracing is explicitly disabled.

Authenticated analysis POSTs create diagnostic/checkpoint records only. They do
not touch protected plans/actions or the executor. GET replay survives a real API
restart; identical retries return the stored report. Missing storage returns 503,
never an ephemeral successful investigation. Failed computation records a closed
outcome where persistence remains available. Real authorization and protected
mutation paths remain the numbered Phase 9/10 gates.

Primary references: [LangGraph state graph](https://reference.langchain.com/python/langgraph/graph/state),
[interrupt](https://reference.langchain.com/python/langgraph/types/interrupt), and
the installed pinned MongoDBSaver/SerializerProtocol source inspected locally.
