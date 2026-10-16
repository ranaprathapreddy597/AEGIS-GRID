# Synthetic AMD / Pinecone integration

The user authorized live synthetic index population on 2026-10-16. Only the
dedicated corpus namespace in `aegis-grid-memory` is written. No unrelated records
are deleted. Physical I/O, Evolus invocation and dedicated MI300X remain blocked.

Run from the repository root, after installing the locked dependencies:

```powershell
.venv/Scripts/python tools/live_knowledge.py ingest
.venv/Scripts/python tools/dev.py start
.venv/Scripts/python tools/run_hosted_graph.py
```

Configure `PINECONE_API_KEY`, `PINECONE_INDEX_HOST` and `INFERENCE_API_KEY` only in
ignored `.env`. The hosted adapter uses the reviewed fixed AMD origin. The host
runner passes secrets by process environment, never command-line values. It mounts
only the public model cache, tools and evidence output into the native Linux image.
Default Compose investigation remains offline; `build_graph` and
`InvestigationService` accept explicitly injected hosted/retrieval adapters. The
live runner exercises those exact graph nodes. It does not provision production
egress, enable unattended external calls, or grant execution authority.

`minishlab/potion-base-8M` is loaded from upstream revision
`bf8b056651a2c21b8d2565580b8569da283cab23`. Its pretrained token matrix has 256
columns. The pipeline normalizes its native outputs, with no vector slicing,
padding, random projection or replacement hashing. Model artifact SHA-256s are
recorded in live ingestion evidence. Initial acquisition requires public model
download access; subsequent graph runs use a local offline cache.

The deterministic source allowlist is the verified 1,000-page synthetic manual
library, all 100 registered scenario descriptors, the 100 measured synthetic
benchmark rows, one validated observed incident, and validated Phase 8 recovery
assessment. Text chunks are at most 1,200 characters with a 160-character overlap.
Each chunk binds source hash, revision, source-relative location, span, text hash,
model revision and pipeline version. Versioned identifiers deduplicate identical
source spans; repeated manual pages retain distinct citations. The sorted corpus
digest selects a versioned namespace. Changing the corpus/model creates a separate
namespace and does not silently mix vector spaces or remove earlier versions.
For manual chunks, `source` names the normalized `pages.jsonl` container and
`source_sha256` binds the original PDF identified by `document_id` in the verified
manual catalog; `page_sha256` binds the logical page. It is not the JSONL file hash.

Batches have at most 50 vectors and a 1.9 MB serialized bound. Retries are bounded
and repeat identical IDs. Authentication/quota failures stop all remaining batches
and open a circuit; unattempted and unconfirmed IDs are reported. Counts are polled
for bounded eventual consistency. A repeat batch proves count stability. Only a
randomly named `aegis-integration-test-*` namespace can be cleaned by the test
method; corpus namespace deletion is refused.

Retrieval requires tenant, isolated plant, synthetic label, model identity and
optional knowledge-kind filters. Every returned ID, exact text and metadata must
match the local source manifest. Diagnosis receives only observed sensor evidence
and manual knowledge, never scenario labels or private state. Planning receives
bounded recovery evidence and numerical candidate summaries. Source IDs are saved
with the graph and mapped to page/revision/span/hash evidence in the live report.
All text is untrusted. Models can return only strict diagnostic enums or one of
three planning recommendations; no tool or command payload can pass validation.
The numerical optimizer, adversarial search, native referee, manual contradiction
gate and independent safety shield remain authoritative. The graph interrupts
before execution; the separate cryptographic HITL flow remains mandatory.

AMD routing remains DeepSeek-V4-Flash → GLM-5.3-Flash → Qwen3.8-Flash-Next. Only
reviewed exact response aliases are accepted. Each opinion has a 60-second total
deadline, 20-second HTTP timeout, bounded response/output, strict usage accounting
and no shared-auth/quota fallback fanout. A client session has at most six model
requests and 32,768 conservatively reserved tokens; failed attempts retain their
reservation. Graph execution uses a separate 16,384-token admission/usage budget.
These are cost/traffic bounds, not provider price or SLA measurements. A 429 opens
a five-minute session circuit. Sanitized diagnostics record stage and validation
field/type, never raw responses, model reasoning or input values.

Sources: [model card](https://huggingface.co/minishlab/potion-base-8M),
[AMD model API](https://amd-aim.github.io/radeon-cloud-docs/guides/model-apis/),
[Pinecone upsert](https://docs.pinecone.io/reference/api/2025-10/data-plane/upsert),
[query](https://docs.pinecone.io/reference/api/2025-10/data-plane/query),
[stats](https://docs.pinecone.io/reference/api/2025-10/data-plane/describe_index_stats),
[delete](https://docs.pinecone.io/reference/api/2025-10/data-plane/delete).

Measured results and remaining gates are in `results/LIVE_INTEGRATION.md`.
