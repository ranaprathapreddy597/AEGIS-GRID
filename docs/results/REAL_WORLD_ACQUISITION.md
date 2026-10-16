# Public industrial reference acquisition — 2026-10-17

Overall: **PARTIAL**. The complete pipeline passed for five eligible public
sources. NASA PCoE acquisition remains **BLOCKED** on dataset-specific license /
redistribution provenance verification. No production or physical-plant claim.

## Actual retained originals and accepted material

| Source | Original bytes | Permission verified | Knowledge records |
|---|---:|---|---:|
| Raspberry Pi Compute Module introduction, official documentation | 25,627 | CC-BY-SA-4.0, pinned repository LICENSE | 23 |
| Arduino Opta industrial controller datasheet source | 42,093 | CC-BY-SA-4.0, pinned repository full license and link | 25 |
| NIST AMS 200-1 manufacturing test-bed technical report | 1,553,663 | NIST Technical Series worldwide reprint/derivative grant; report's own NIST contribution disclaimer | 14 |
| UCI 447 hydraulic-system condition monitoring archive | 76,601,704 | Dataset-specific CC-BY-4.0 on official UCI landing page | 9 |
| CIRA centrifugal pump A, 2024-04-10, Zenodo record 18479728 v2 | 985,538 | Dataset-specific CC-BY-4.0 in record metadata | 32 |
| **Total** | **79,208,625** | **Five accepted originals** | **103** |

The downloader recorded **79,436,077 body bytes**, including retained licensing
evidence. This is below the 1,000,000,000-byte limit; the largest original is below
200,000,000 bytes. Public discovery metadata read during browsing is separate from
that acquisition ledger. Downloads used one request at a time, approved HTTPS
origins, no credentials, no authentication bypass and no prohibited scraping.

Original files and license evidence remain at
`D:/AEGIS GRID/.run/real-world-v1/originals/`. They are ignored local data, not
uploaded to Pinecone or committed as bulk assets. Source/processing manifests,
download ledger and full processed chunks remain in `.run/real-world-v1/`.
Every original has a computed SHA-256, rechecked before processing. The CIRA
file also matched Zenodo's published MD5 and exact byte count. This does not
claim independent vendor SHA-256 signatures for sources that publish no digest.

Attribution and license links accompany every Pinecone chunk. Arduino's source
byline credits Ali Jahangiri and Julián Caro Linares; retained source links expose
the original byline. Its license introduction abbreviates the license name, but
the linked URL and complete legal body are BY-SA 4.0; derivatives use BY-SA 4.0.
Raspberry Pi Ltd and contributors retain their documented attribution. NIST
records credit Thomas Hedberg Jr. and Moneer Helu, and state “Republished courtesy
of the National Institute of Standards and Technology.” UCI credits Helwig,
Pignanelli and Schuetze; CIRA credits Angelo Martone and Gaetano Zazzaro. Modified
chunks identify the extraction/normalization date and preserve source license
URLs. No endorsement or correspondence to this simulator's equipment is implied.

## Verification, processing and quality limits

The reviewed registry is `data/real-world-sources.json`. License evidence is
obtained and checked before each original asset is accepted. Unknown/restricted
licenses, unapproved origins, unsafe redirects, unexpected file formats,
oversized bodies, encrypted/traversing/symlink/non-text archive members and malformed
measurements are refused. Authorization/quota failures stop further requests;
public transient transport errors have bounded backoff. Completed originals are
never silently overwritten; cached bytes must match the saved integrity ledger.

The NIST PDF was parsed by the repository's own worker inside a network-disabled,
read-only, capability-dropped Docker container limited to 256 MB, one CPU and a
60-second host timeout. Only selected source pages were extracted, with exact page
locations. The PDF and all other acquired data remain untrusted; no downloaded
script, binary, macro, include, image or link was executed or followed. Code blocks
and active HTML are removed from documentation views. The hydraulic archive is
retained intact; only the explicit profile/TS1/FS1 numeric members are read in memory.

UCI's **2,205 measured test-rig cycles** have validated profile labels and matrix
shapes. Nine cooler/leakage groups contain descriptive temperature/flow statistics
and membership hashes, with varying valve/accumulator conditions disclosed. They
are not causal effects or operating limits. The CIRA CSV contains **4,981 rows and
271 empty cells**. The initial strict numeric parser rejected these empty cells;
processing now preserves valid/missing counts and excludes empty cells from each
descriptive statistic, with **no imputation**. The provider description uses some
`.SV` field suffixes while actual pressure/temperature CSV columns use `.PV`.
Raw column names are preserved; units are not converted or claimed calibrated.
Sixteen ordered windows yield 32 concise records. No fault labels are invented.

Chunks are at most 1,200 characters with a 160-character overlap where needed.
Deterministic `agrw1-<SHA256>` IDs bind source revision/hash, normalized span or
data selection, text hash, license evidence, attribution, pipeline and embedding
identity. All records say `synthetic=false`, `kind=reference`, and
`authority=external_reference_not_plant_authority`; published simulation data was
not relabeled as measured data. Original references and statistical transformations
remain auditable against the retained files.

## Actual live Pinecone operations

Authenticated metadata HTTP 200 verified `aegis-grid-memory`, ready, 256 dimensions,
cosine and the configured index host. Destination is exactly **`real-world-v1`**.
The genuine native 256-dimensional model is pinned `minishlab/potion-base-8M`
revision `bf8b056651a2c21b8d2565580b8569da283cab23`, with artifact hashes matching
the earlier verified model. Outputs are finite, normalized and never random,
padded or truncated vectors.

1. The first live batch uploaded **20 records**, four per accepted source. Exact
   metadata and all 256 vector components were fetched and verified. Counts were
   0 → 20. Dense-only retrieval passed **8/10** queries; both CIRA pump queries
   failed. Bulk upload stopped. The original failure and HTTP evidence remain in
   `real-world-pilot-initial-failure.json`; it was not waived or hidden.
2. A query-only correction added semantic routing over source titles/origins,
   bounded source-filtered vector queries and semantic reranking. Reranking strips
   numeric JSON only from its query-time text view, preserving raw evidence and
   stored vectors. The same pinned model computes every semantic representation.
   **No pilot record was replaced or deleted**, and the fixed query set was not
   reduced. The existing 20 records were fetched, verified and skipped.
3. The unchanged pilot then passed **10/10 top-5** source-relevance checks, exact
   persisted metadata/vectors, count checks and a wrong-tenant query returning zero.
   Only that passing branch enabled bulk insertion: **50 + 33 new records**, both
   HTTP 200 acknowledgements. Total distinct records uploaded across the two runs:
   **103**. New records in the second run: 83; existing records skipped: 20.
4. All **103 records were fetched** in bounded batches and checked against the local
   manifest and regenerated native embeddings. Final namespace count: **103**.
   Failed/unconfirmed IDs: **0**; unattempted eligible records: **0**. Other namespace
   counts were unchanged, including the existing synthetic corpus. There was no
   delete request, blind update, unrelated write or ambiguous-write retry.

Final retrieval: **9/10 top-1 and 10/10 top-5**, on the ten published fixed
development source-relevance queries. This measures reference retrieval, not
held-out industrial diagnosis, temporal-window selection or recovery accuracy.
Dense-only limitations are retained. Source-aware retrieval is bounded to two
source routes and eleven candidates, rather than downloading the full index.

`real-world-ingestion.json` retains the second-run receipt: 2 upsert HTTP 200s,
7 fetch HTTP 200s, 61 query HTTP 200s and 5 stats HTTP 200s, plus authenticated
control-plane verification. Fetch-before-append skips identical existing records
and refuses mismatches. Local pipeline runs are serialized. Pinecone upsert is
not an atomic cross-client insert-if-absent primitive; concurrent independent
writers are outside this single-writer acceptance. Observed count growth exactly
matched new IDs. An uncertain write stops the run for fetch-based reconciliation.

## Actual LangGraph and regression acceptance

`real-world-langgraph.json` records PASS: a new actual native fault investigation
retrieved ten verified source IDs from the new namespace inside diagnosis, OEM
and planning nodes. This case cited Arduino/Raspberry Pi documentation and UCI
measurements; separate retrieval tests cover NIST and CIRA as well. The native
optimizer/adversary/referee still run independently. Source references cannot set
controls, plant limits, tool permissions or approval policy. Full-corpus manual
contradiction remains `no_action`; the graph interrupts before protected execution.
It uses the existing offline opinion template and a primitive-only in-memory
checkpoint for acceptance. **Only Pinecone reads** were made by this graph proof:
no AMD, Evolus, GitHub, enterprise write or physical I/O.

Backend regression: 319 Python tests, 3 native CTest cases and 16 Node executor
tests passed; generated Pydantic/OpenAPI/TypeScript contracts, TypeScript types,
Ruff and strict mypy checks passed. Malicious external-reference text cannot change
policy or enable commands. Offline HTTP tests cover no-overwrite, mismatched
existing IDs, authorization/quota stops, byte limits, redirect rejection, archive
traversal and missing-value handling. Final focused ingestion checks are retained
separately (28 focused checks). Final tools/tests ran as read-only mounts over the
QA image so the post-pilot failure-report regression is included. A separate
12-check evidence audit verifies the unchanged pilot IDs/query set, 20/50/33 insert
batches, count growth, skipped originals, retained file hashes, caps and no deletes.
See `real-world-evidence-audit.json`. No UI/production/physical-key acceptance is
inferred from this gate.

Reproduction (project virtualenv, ignored local Pinecone configuration):

```powershell
python tools/acquire_real_world.py all
python tools/check_real_world_graph.py
```

The recorded execution acquired the approved files with `PublicAcquirer`, then
used `tools/acquire_real_world.py upload` twice (first stopped at the failed
pilot, second skipped those 20 records and added 83 after repair). A separate
`acquire` invocation verified cached license evidence and original hashes without
overwriting the upload receipt. No new dependencies were installed for this work.

## Excluded / blocked material and remaining gates

- **NASA PCoE: BLOCKED.** The official catalog requests attribution but does not
  establish dataset-specific redistribution/adaptation licenses for every donated
  dataset. A Zenodo C-MAPSS mirror declares CC-BY-4.0, but its grant's provenance
  back to the official NASA distribution was not verified; C-MAPSS is also
  simulated data. No NASA original or mirrored archive was downloaded or uploaded.
- Raspberry Pi product PDFs with BY-ND restrictions were excluded from derivative
  processing; separately licensed online documentation was used.
- Zenodo 12750599 was licensed but geological and irrelevant; no asset downloaded.
- Dedicated MI300X, Evolus, other unverified external/production gates, hardware
  calibration, real-plant safety validation and physical passkeys remain BLOCKED
  or unverified. No release tag or deployment.

Reviewed source/license references:
[Raspberry Pi repository license](https://github.com/raspberrypi/documentation/blob/ddea98e98dafe9419feb4fd82710c2fbdef7dc44/LICENSE.md),
[Arduino repository license](https://github.com/arduino/docs-content/blob/404d4b35349e6558974af82a0966a2846dbbb510/LICENSE.md),
[NIST rights](https://www.nist.gov/open/copyright-fair-use-and-licensing-statements-srd-data-software-and-technical-series-publications),
[UCI 447](https://archive.ics.uci.edu/dataset/447/condition+monitoring+of+hydraulic+systems),
[CIRA record](https://zenodo.org/records/18479728),
[NASA catalog](https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/).
