# Phase 12 report — 2026-10-16, Asia/Calcutta

Main and clean-source local gates PASS. Release BLOCKED.
Previous phase e9b0e21; original supplied master/phase prompts unchanged.

## Actual work and evidence

- Frozen 100-scenario native benchmark against threshold, Sentinel and actual
  learned CPU logistic/centroid baseline; 30 disjoint training seeds, observed-only
  features, real timings/RSS, confusion matrices, family-bootstrap intervals,
  diagnosis and paired recovery/production/energy/downtime. All raw rows retained.
- Original benchmark exposed five late thermal trips. Policy v2 now uses a 65 C
  operating guard to reserve sampled/ramp headroom; the hard limit stays 70 C.
  Original results remain unchanged. Separate post-fix regression recovers 16/16
  hazardous cases with 0 thermal hazards across all 100. This is post-evaluation
  validation; Sentinel still misses 44/90 faults and diagnosis is limited.
- Generated hostile PDF, hostile/tool-bearing model output, timeout/503 contract
  doubles, all 512 one-bit Ed25519 signature mutations, partial database rollback,
  receipt/snapshot corruption and actual concurrent read-capacity denial tested.
  No provider double is counted as live evidence; whole-admin rollback is unverified.
- Expensive futures reads are bounded. Compose migration now respects a unique
  project network. UI displays the actual policy revision and reads old v1 records.
- Actual package inventory and runtime Node/lock comparison, dependency audits,
  baseline secret scan, updated threat/architecture diagrams, hostile audit,
  capability scoreboard, demo narration/FAQ and explicit release checklist.
- Actual 180.0156-second browser demo with video, nine captures, analysis export,
  real persistent graph/tournament, manual refusal and actual WebAuthn/Node/Mongo
  maintenance receipt. Virtual CTAP2 authenticator is explicitly labeled; physical
  acceptance is unverified. Both live-twin and receipt captures visually inspected.

## Reproduction and tests

Executed tools/dev.py start/check; bounded network-none tools/benchmark_scenarios.py
for both detector versions; focused final hardening (16 pass); tools/clean_demo.py;
then tools/check_clean_source.py for a separate venv/node_modules and complete gate.

Main full gate: **268 Python / 3 CTest / 16 Node / 14 Chromium PASS**, plus all
format/lint/type/build/contract/fixture checks, secret/pip/pnpm audits, actual SSE,
cross-language validation, Mongo/Redis checks, six storage, three graph and
fourteen authorization privilege denials. Raw phase12-checks.txt ends PASS. Console-log trailing whitespace is normalized;
measurement/result content is unchanged.

Clean-source demo tree: 64d4da5ded1a00b056e137af853e95e908a3e0b7. New project,
credentials and volumes, port 58983, startup 64.0277 s, frontend 200 and anonymous
API read 401. Actual demo receipt:
87e46b39444636f7d62c5d277fbb0197cf4597e6c80620ca287c0ac702a5da95.
The captured fault/seed reset step completed in 1.531 s including screenshot;
it creates private copies, not a public operational reset. Existing host Docker,
download and browser caches were reused; no cold-machine timing claim.
Only documentation/evidence and a follow-up validation helper were added after
that export; runtime source/contracts match it exactly. Proof containers/networks
are stopped independently; all volumes and the main stack are retained.
Clean-source complete gate: **268 Python / 3 CTest / 16 Node / 14 Chromium PASS**
with its own frozen host venv and node_modules, scoped proof database, complete
audits/contracts and actual privilege denials. See phase12-clean-checks.txt and
phase12-clean-check-proof.json. The manifest tracked only exported source paths;
private configuration and virtual-authenticator material stayed ignored.

## Limits and next acceptance

See BENCHMARKS.md for original/post-fix numbers and misses, FINAL_AUDIT.md for
file/line findings and capability scoreboard, and RELEASE_CHECKLIST.md for gates.
MI300X/Evolus/Pinecone and approved GitHub/hosted CI live gates remain **BLOCKED**.
Production TLS/IAM/process isolation, physical key acceptance, external trusted
audit anchoring, OS vulnerability scan/HA/OEM calibration remain unverified or not
implemented. No physical I/O, deployment, provider mutation or release tag.
The authorized local work does not complete the master production/live gates.
