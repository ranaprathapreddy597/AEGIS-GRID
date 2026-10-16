# ADR 0008: exact citations before manual-derived constraints

Accepted 2026-10-16. Phase 5 follows Phase 4 commit `12c2d86`.

The supplied `api-1.json` is Evolus Integration API v1 / OpenAPI 3.0.4.
Its original SHA-256 is
`0af55c67c60d07dc35f37b70553f1a2a6b1cce76a3311d014c6be1473fadd4f8`.
The original is unchanged. `tools/vendor_evolus_spec.py` derives a read-only
contract subset, including provider component schemas, into the adapter package.
This is supplied documentation, not a recording or evidence of a live response.

The actual interface is memory document ingestion and chunk retrieval. There is
no separately documented Document Extractors endpoint in this specification.
Application auth is `X-ApiKey` plus `X-Application-Id`; personal auth uses
`X-User-ApiKey`. Memory discovery explicitly requires personal user auth.
Do not send an application key under the personal header to guess a scheme.

The adapter supports only documented GET formats, memories, documents, chunks
and original download routes. HTTPS origin is fixed, redirects/proxy inheritance
are disabled, credentials are secret-wrapped, responses are bounded, and safe
read retries are capped at three. Formats and limits are read from the provider;
no page limit, price, OCR model assignment or successful ingestion is assumed.
OpenAPI 3.0 nullable is translated mechanically to JSON Schema Draft4 and supplied
response schemas are validated without coercion. Provider error text is not logged.

The specification documents upload/background jobs and retry/reindex writes, but
this phase does not expose or invoke them: repository instructions prohibit
external writes before the authorization gates. A provisioned existing document
can be downloaded and its chunks matched to exact source PDF text. An exact
unique match yields a derived citation. Missing, cross-page or ambiguous chunks
remain unmapped. ChunkResponse has no guaranteed page, revision or confidence;
none are fabricated. Numeric ingestion status labels are not guessed from enum
values. No unverified polling-state machine or OCR call is implemented.

Local parsing uses pinned pypdf; born-digital pages have exact canonical text
fingerprints (document ID, revision, page number, extracted text), plus the whole
original PDF hash. They are logical page hashes, not pixel/image or PDF-object
hashes. Empty text marks OCR required and blocks action. Only the deliberately
structured synthetic table grammar is converted into operating constraints;
arbitrary OEM prose needs a reviewed mapper and verified revision authority.
Unverified provider content always yields no action, even if it copies fixture
syntax. Procedures are non-executable evidence and interlocks are non-overridable.

Page checkpoints use source/revision binding, exclusive single-writer lock,
atomic file replacement and fsync. Restart recomputes extraction from the source
and compares existing pages before reusing them; missing pages are reconstructed.
An interrupted worker can leave `writer.lock`; an operator must confirm the
worker has stopped before removing that job-local lock. No automatic lock stealing.
Local bounds are 32 MiB / 1,000 pages / 100,000 characters per page / windows 1-100.
These are AEGIS limits, not claimed provider limits. Parser CPU/memory isolation
for arbitrary hostile PDFs remains a hardening item; API accepts no uploads.

The reproducible corpus is project-authored CC0 test data: a 999-page PDF and a
one-page contradictory bulletin. It is not a real OEM manual or 1,000 pages of
unique engineering knowledge. Known table rows vary cell, quantity and record ID.
Every extracted row has exact quote, units, page, revision and source fingerprints.
Unresolved competing ranges block action even if their intersection is nonempty;
we do not automatically trust a newer-looking revision or infer supersession.
The corpus contains an explicit prompt-injection fixture retained as inert text.
No raw document string is ever passed to an executor or used as a policy source.

FAISS IndexFlatIP holds 256-dimensional normalized hashed lexical vectors for
at most 1,000 pages, on one CPU thread. Scores are lexical cosine overlap, not
semantic embedding quality, probabilistic confidence or engineering reliability.
All safety constraints are checked across the entire bounded corpus, independently
of retrieval top-k, so a low-ranked bulletin cannot disappear from the decision.

Pinecone vectors use the same dimensions and citation IDs. Local indexing batches
are prepared, never sent. The verified 2025-10 query adapter fixes namespace,
tenant and plant filters, validates source/revision/ID against local records and
refuses foreign results. Existing vector index, credentials and approved indexing
are required for live comparisons. This is not verified cloud indexing.

References inspected: supplied provider OpenAPI; Pinecone official
[upsert](https://docs.pinecone.io/reference/api/2025-10/data-plane/upsert) and
[query](https://docs.pinecone.io/reference/api/2025-10/data-plane/query) contracts.
Live Evolus and Pinecone gates remain explicit until actual access is tested.
