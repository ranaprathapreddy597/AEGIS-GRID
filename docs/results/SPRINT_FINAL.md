# Competitive sprint final evidence — 2026-10-17

Working integrated application delivered locally. Production release remains
BLOCKED. Quantitative diagnosis and forecasting quality remain PARTIAL.

## Actual gates

| Gate | Result | Raw evidence |
|---|---|---|
| Main complete configured gate | PASS: 398 Python / 3 CTest / 35 Node / 17 Chromium | sprint-full-regression.txt |
| Final frozen-source three-minute demo | PASS: 180.0162159 seconds | sprint-verified-clean-bootstrap.json; sprint-verified-demo/proof.json and demo.webm |
| Earlier isolated demo, same application before evidence-runner CLI hardening | PASS: 180.0069936 seconds | sprint-final-clean-bootstrap.json; sprint-final-demo/ |
| Final separate clean-source complete gate | Running; final result recorded before delivery | sprint-verified-clean-check-proof.json; sprint-verified-clean-checks.txt |
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
  causes and unsupported hosted alternatives. Fresh-seed 100-case cause precision
  100%, recall 48%, top-cause/no-cause accuracy 65%, abstention 65%. Legacy recall
  70% and accuracy 75%; improved general accuracy is not demonstrated.
- In 30 explicitly targeted native healthy operating confounders, unsupported
  cause assertions fell from 30 to zero. This is development evidence, not held-out.
- Fixed observed-only thermal forecasting over 30 new-seed native episodes:
  1,566 correlated windows, 20 upcoming hazards; 2 TP, 2 FP, 18 FN, 50% precision,
  10% recall, 94.64% coverage. Median 60s lead concerns only two TP windows.
  High covered accuracy is dominated by negatives; sensitivity remains poor.
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
