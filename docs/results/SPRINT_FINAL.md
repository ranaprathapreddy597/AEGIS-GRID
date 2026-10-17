# Competitive sprint final evidence — 2026-10-17

Working integrated application delivered locally. Production release remains
BLOCKED. Quantitative diagnosis and forecasting quality remain PARTIAL.

## Actual gates

| Gate | Result | Raw evidence |
|---|---|---|
| Main complete configured gate | PASS: 398 Python / 3 CTest / 35 Node / 17 Chromium | sprint-full-regression.txt |
| Optimized frozen-source three-minute demo | PASS: 180.0125390 seconds | sprint-optimized-clean-bootstrap.json; sprint-optimized-demo/proof.json and demo.webm |
| Optimized separate clean-source complete gate | PASS: 398 Python / 3 CTest / 35 Node / 17 Chromium | sprint-optimized-clean-check-proof.json; sprint-optimized-clean-checks.txt |
| Final frozen-source three-minute demo | PASS: 180.0162159 seconds | sprint-verified-clean-bootstrap.json; sprint-verified-demo/proof.json and demo.webm |
| Earlier isolated demo, same application before evidence-runner CLI hardening | PASS: 180.0069936 seconds | sprint-final-clean-bootstrap.json; sprint-final-demo/ |
| Final separate clean-source complete gate | PASS: 398 Python / 3 CTest / 35 Node / 17 Chromium | sprint-verified-clean-check-proof.json; sprint-verified-clean-checks.txt |
| Source and preservation comparison | PASS: 234 runtime/test/helper/configuration files, zero mismatches after CRLF normalization | sprint-source-preservation.json |

The main gate includes Ruff formatting/lint, strict mypy, generated OpenAPI/TS
and fixture drift checks, ESLint/TypeScript/Vite, dependency and secret audits,
actual authenticated API/SSE/source transport, storage persistence, Redis delivery,
checkpoint ACLs, real WebAuthn/Node/native sandbox verification, browser restart,
fault, accessibility and mobile checks. Authorization checks recorded 23 actual
Mongo privilege denials and zero forbidden operational writes. Browser captures
and the exact 17-test JSON are retained in sprint-main-browser/. Historical
Phase 12 browser outputs were restored after copying the new proof.

Frozen tree `9cfd5b67660d41f81be8f7859f7c3b982ac2815d` runs in isolated project
`aegis-proof-9e0a8d11`, with fresh credentials/storage and its own installed frozen
host venv/node_modules for the complete clean gate. Same host OS, browser,
download and Docker caches are reused. This is not a cold-machine, physical-key,
GPU/provider or production acceptance result. Proof stacks stop after validation;
all volumes and the main application are retained.

## Improvements and measured limits

- Grounding rejects stale-channel cause assertions, unsupported low-common-pressure
  causes and unsupported hosted alternatives.
  - Native fault diagnosis optimization (100 fresh-seed native cases):
    - Initial sprint: 48 TP, 0 FP, 52 FN; precision 100%, recall 48%, accuracy 65%, abstention 65%.
    - Optimized: 73 TP, 0 FP, 27 FN; precision 100%, recall 73% (+25 pp, z = 3.74, p < 0.001), accuracy 80% (+15 pp), abstention 33%.
    - Legacy baseline: recall 70%, accuracy 75%. The optimized grounded model outperforms the legacy baseline on both recall and accuracy while preserving 100% precision.
  - Honest abstention: in Family 1 (`scenario-010`, unmanifested sensor clamp at 38 C under nominal load where operating temperatures stay <= 38 C), temperature residuals are <= 0.07 C; abstention is physically preserved.
- In 30 explicitly targeted native healthy operating confounders, unsupported
  cause assertions remain zero (100% correct abstention).
- Thermal forecasting optimization across 30 new-seed native episodes (1,566 windows, 20 upcoming hazards):
  - Baseline persistence: 0% recall.
  - Baseline operating guard: 10% recall, 11% precision, 16 FP.
  - Initial sprint: 2 TP, 2 FP, 18 FN; precision 50%, recall 10%, F1 0.167.
  - Optimized multi-telemetry energy estimation: 14 TP, 7 FP, 6 FN; precision 66.7%, recall 70% (+60 pp, Fisher p = 0.00022), F1 0.683 (4x gain), accuracy 99.12%, FPR 0.48% (7 / 1,455 negative windows). Median warning lead time: 25.0 seconds across 14 detected hazard windows.
- Six-cell live observed temperature/flow/pressure/status/limits and incident
  timing, forecast/provenance panel, native candidate selection, actual modeled
  energy/downtime/production and explicit infeasibility are integrated in React.
- Six selected attack families, 13 passing native/crypto assertions. Storage
  doubles and historical actual CTAP2 proof remain distinctly identified.

Protocols, native/source hashes, raw rows and initial weaker development results
are retained in SPRINT_AI.md, sprint-ai-*.json, ../SPRINT_FORECAST.md,
SPRINT_FORECAST.json and SPRINT_ADVERSARY.json. No final-holdout tuning, new hosted
evaluation or real-world calibration is claimed. Both new evidence runners reject
existing output paths; existing-path refusals were exercised before delivery.

## Preservation and retained failures

No changes to the original master/build instructions, manuals, scenarios,
commissioned signed package, vector manifests or historical proof. The main
commissioned resource is identical before/after the full gate, including its one
receipt `96b9c3f4338f75c56e452205fcfa446ee714a45303ab4c27a3775faea822ed2e`.
There were zero provider requests, vector writes/reuploads or enterprise/physical
actions in this sprint. Historical verified counts remain 1,235 + 103; external
counts were deliberately not queried anew. Full regression sandbox writes are
separate from that completed commissioned resource.

Docker Desktop's engine pipe became unavailable during the first main gate and
first clean startup. Those failures are preserved in
sprint-full-initial-engine-failure.txt and sprint-initial-clean-engine-failure.json.
The engine was started, existing containers/volumes restored, and actual gates
rerun. No test or safety check was disabled to resolve that interruption.

Dedicated MI300X/HBM/long-context, Evolus invocation/extraction, physical passkeys,
industrial calibration, independent OEM review, production security/deployment,
NASA provenance and official hackathon rubric verification remain BLOCKED or
unverified. No release tag, external publication or prize claim was made.
