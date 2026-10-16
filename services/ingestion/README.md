# Document ingestion boundary

Current synthetic semantic pipeline uses pinned native 256-D potion-base-8M,
versioned provenance IDs and a dedicated Pinecone namespace. Real upserts,
persisted counts, metadata filters, retrieval and isolated cleanup are verified.
Returned text and metadata must match the local manifest before LangGraph uses
the sources. Documents never set safety policy or issue commands. See
[workflow](../../docs/LIVE_KNOWLEDGE.md) and
[actual results](../../docs/results/LIVE_INTEGRATION.md). Evolus remains blocked.

Not implemented in Phase 1. Phase 5 requires verified Evolus specifications before
any production adapter, strict citation/revision schemas and explicit test doubles.
