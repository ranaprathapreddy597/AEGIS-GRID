# Synthetic manual corpus

Project-authored AEGIS simulator test data, dedicated under CC0-1.0.
No manufacturer endorsement, physical operating envelope or OEM provenance.

`synthetic-manual.pdf` contains 999 born-digital reference sheets with structured
table rows across six cells and four quantities. `contradictory-bulletin.pdf`
adds one unresolved conflicting temperature range. These are deliberately
repetitive extraction/load fixtures, not 1,000 pages of distinct OEM knowledge.
Page 999 includes an instruction-injection test which remains untrusted text.

Reproduce using pinned development dependencies:

```powershell
.venv/Scripts/python tools/generate_manual_corpus.py --create-pdfs
.venv/Scripts/python tools/generate_manual_corpus.py --check
```

The first command deterministically recreates PDFs and checkpointed page records.
The check recomputes source extraction and validates every persisted page.
`pages.jsonl` and `catalog.json` carry source/page fingerprints and revision
authority. The ordinary API serves only these read-only fixtures, with authentication.
Provider PDFs are separate caller-owned local jobs and never silently replace them.
