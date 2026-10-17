# Controlled cloud investigation

Default application mode remains `offline`. Existing Pinecone records are reused:
`aegis-synthetic-v1-6e4d75051cbcaf1e` (1,235) and `real-world-v1` (103).
Do not rerun ingestion for this workflow.

The ignored `.run/cloud-knowledge/` directory contains read-only snapshots fetched
from the existing index. `data/cloud-knowledge-manifest.json` pins their bytes;
record IDs, text hashes, embedding revision and tenant/plant scope are checked
again at startup. The frozen native 256-D potion model's three artifact hashes
must match `data/cloud-embedding-manifest.json`. Model weights stay in the local
HuggingFace cache; no download is attempted by the application. Missing assets
block hosted initialization. Public-source originals and license evidence remain
in `.run/real-world-v1/`; references preserve their licenses and attribution.

With the local stack running and the existing provider credentials in ignored
`.env`, run:

```powershell
.venv/Scripts/python tools/hosted_mode.py hosted
node tools/check_cloud_ui.mjs
.venv/Scripts/python tools/hosted_mode.py offline
```

`hosted_mode.py` explicitly adds `infra/local/compose.hosted.yaml`: only the API
receives provider credentials and an outbound network; knowledge/model mounts are
read-only. Clients accept fixed AMD and validated Pinecone HTTPS origins, disable
proxies/redirects and expose no provider mutation routes. The override grants
network egress, not a network-level domain firewall or production tenancy.
Only tenant `local` / plant `isolated-simulator` is supported. Do not use this mode
as a multi-tenant deployment configuration.

Each API process admits at most six AMD model requests, six catalog requests,
32,768 conservative reserved tokens and twelve dual searches. Failed model calls
retain reservations. Requests are serialized; provider calls have bounded deadlines,
and authorization/quota failures open circuits. Limits are not reset per incident.
An explicit process restart starts a new local session; do not automate restarts
to evade provider quotas. Failures retain deterministic local reasoning/abstention.
The verified model order is DeepSeek-V4-Flash, GLM-5.3-Flash, Qwen3.8-Flash-Next.

Authenticated dashboard investigation POSTs run the actual persistent Mongo-backed
LangGraph. A separate authenticated SSE endpoint streams durable report checkpoints
with bounded duration and concurrency. Reports preserve requested/served model IDs,
usage, latency, sanitized attempt diagnostics, namespace/reference IDs, revision,
source hashes, license and attribution. Replaying a completed idempotency key reads
the saved result. Changing mode does not rewrite earlier reports.

Dual retrieval retains two synthetic and two external hits per role. The external
reader uses its existing semantic source routing/reranking. All matches must equal
the pinned metadata/text and pass the role filter. No acquired external hardware
manual has a verified equipment mapping to the fictional six-cell simulator.
Those manuals remain `external_context_only`; they are never elevated to plant
constraints. Applicable manufacturer priority requires a verified equipment mapping
and a subsequent reviewed change. Synthetic manuals remain explicitly synthetic.

Retrieved text is inert, untrusted model context. Model schemas permit opinions
and evidence field IDs, never tools or executable instructions. Native minimax,
Red/referee, latched emergency policy and contradictory-manual refusal remain
independent. The graph reaches an approval interrupt, but the incident's conflicting
manuals prohibit authorization. The existing real WebAuthn/capability/executor demo
is a separate stationary simulator sandbox. Cloud reports do not authorize that
sandbox or manufacture a passkey approval. No physical I/O is present.
Combined connector/capability gates remain BLOCKED for their aggregate operational
acceptance, including Evolus and dedicated hardware. Scoped Pinecone/AMD results
are shown separately on each investigation; they do not waive those gates.

See `results/CLOUD_INTEGRATION.md` and its raw JSON/browser evidence for measured
provider results, retained failures and demo readiness.
