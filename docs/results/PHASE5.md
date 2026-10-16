# Phase 5 execution report — 2026-10-16, Asia/Calcutta

Status: **local gate PASS**; Evolus/Pinecone live gates **BLOCKED**, not waived.
Baseline Phase 4 commit: `12c2d86`. No external write or deployment performed.

## Implemented source

| Files | Behavior |
|---|---|
| `services/ingestion/aegis_ingestion/evolus.py`, derived read contract | Actual supplied Evolus routes/auth/response validation, bounded safe reads and retries; no invented extractor or operational writes |
| `provider_pipeline.py` | Read existing original PDF/chunks, resumable local pages, exact unique text mapping, unknown revision/OCR/mapping blocks |
| `corpus.py`, `library.py` | Source/page hashes, atomic checkpoints, strict synthetic table/unit parsing, typed alarms/procedures/interlocks, complete-corpus contradiction refusal |
| `retrieval.py`, `pinecone.py` | Actual bounded FAISS lexical index, scoped local cloud indexing payloads, verified Pinecone read contract and citation checks |
| Pydantic and generated schemas | Manual document, records, citation, equipment, units/ranges, revision, interlock, confidence/ambiguity and evidence contracts |
| FastAPI / React | Authenticated evidence/source reads, actual page/revision quotes, contradiction panel and working PDF download |
| Corpus generator and fixtures | Deterministic 999-page project-authored PDF plus one-page contradictory bulletin, exact page JSONL and source catalog |
| Tests/profile/probe tools | Separate labeled HTTP doubles; corruption, cache resume, malicious document, foreign search result and contract refusals; actual CPU measurements |

The original user-supplied `api-1.json` remains unchanged and untracked. The
read-only subset is reproducible using `tools/vendor_evolus_spec.py`; origin hash
is recorded in ADR 0008. Direct dependencies are pinned: pypdf 6.20.1,
jsonschema 4.26.0, reportlab 5.0.1 (development generator), with uv lock hashes.

## Commands and actual results

```powershell
.venv/Scripts/python tools/vendor_evolus_spec.py
.venv/Scripts/python tools/generate_manual_corpus.py --create-pdfs
.venv/Scripts/python tools/generate_manual_corpus.py --check
.venv/Scripts/python tools/probe_evolus.py
.venv/Scripts/python -m pytest -q tests/unit/test_manual_evidence.py tests/integration/test_evolus_adapter.py tests/integration/test_api.py
.venv/Scripts/python tools/dev.py start
.venv/Scripts/python tools/dev.py check
```

Focused suite passed 28 checks (`phase5-focused-tests.txt`). The full gate passed
**179 Python / 3 CTest / 7 Chromium** checks, two Node tests, axe, lints/types/builds,
all contract/fixture drift checks, secret/dependency audits, actual storage ACL/load,
and live HTTP/SSE/cross-language checks (`phase5-checks.txt`). The final CSS-only
control styling was separately rebuilt and passed the manual browser/axe/download/
mobile test again (1/1, `phase5-style-check.txt`). Final panel capture was inspected.
The first build caught a TypeScript parameter shadowing `document`; it was renamed
and rebuilt. This failure is resolved, not silently treated as a passing build.

The real network-none CPU profile ran the built Python image with two CPUs,
512 MiB memory and `tools/profile_manuals.py` bind-mounted read-only. It loaded
all 1,000 pages and built FAISS. Actual results (`phase5-manual-profile.json`):

- Initialization 0.2533 s; peak process RSS 96.70 MiB (excludes Docker/WSL).
- 24 preregistered exact-term development queries, top-1 relevant **20/24**.
- Query median 0.164 ms, p95 0.536 ms in this run.
- All 1,000 constraints checked independently of search ranking.
- Baseline 999 pages: simulator evidence only; added bulletin: **no action**.

Retrieval misses remain visible in the raw per-query rows. These are repetitive
synthetic lexical tests, not held-out semantic/OEM accuracy or a cloud comparison.
Pinecone retrieval quality cannot be measured without an indexed live resource.

The contradictory evidence is original manual R1 page 985, 0–70 degC, and bulletin
R2 page 1, 0–95 degC. Both rows retain exact quotes/table rows/source hashes. No
automatic supersession is inferred. Page 999's instruction-injection text is
retained in data but cannot create commands, change limits or unlock a write.

Original first/injection/bulletin PDF pages were rendered with Poppler and visually
inspected: readable, unclipped text. Generated files are CC0 project fixtures.
They are not real OEM manuals or 1,000 pages of unique engineering knowledge.

## External gates and practical limits

The user supplied application scope; it is stored only in ignored `.env`. A key
was previously exposed in chat and left unused; no rotated `EVOLUS_API_KEY` is
configured at the recorded probe. Probe output explicitly says blocked, not
successful extraction. Application-key auth cannot enumerate memories under the
supplied specification; existing memory/document IDs or personal read auth are
required. No provider upload, reindex, MCP action or billing operation was sent.

ChunkResponse guarantees no page number, revision authority or provider confidence.
Derived citations use a unique exact match against downloaded original text;
ambiguous/unmatched chunks abstain. Scanned pages need separately provisioned,
documented OCR. Free-form OEM engineering limits need a reviewed extraction mapper
and authenticated revision lineage; copying fixture syntax is insufficient.

Pinecone uses verified 2025-10 query/upsert schemas, fixed tenant/plant namespace
and local citation validation. Upsert payloads are prepared locally; no external
write method is exposed in Phase 5. Live index provisioning, approved indexing and
retrieval comparison remain blocked. All operational writes remain closed.

The local API exposes no arbitrary PDF upload. General hostile-PDF parsing needs
separate process resource enforcement before public ingestion. A crashed checkpoint
writer leaves a lock requiring operator confirmation before removal; no unsafe
automatic lock stealing. See ADR 0008 for exact bounds and remaining limitations.

Next: Phase 6 MI300X deployment/memory proof. The user will provide MI300X access
later; device, throughput, HBM and long-context live gates remain blocked.
