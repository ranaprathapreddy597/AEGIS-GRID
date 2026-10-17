# Competitive engineering sprint — 2026-10-17

## Implementation log and feature matrix

| Phase | State | Working implementation / qualification |
|---|---|---|
| 1 targeted audit | PASS | Source/API/UI/test audit; existing working components reused; SPRINT_AUDIT.md |
| 2 AI quality | PARTIAL | Observed-only ranked candidates, stale abstention, unsupported hosted cause rejection; 100 fresh-seed native cases, precision 1.00, recall .48, accuracy .65, abstention .65. Legacy recall .70/accuracy .75; no accuracy improvement claimed. |
| 3 command center | PASS implementation | Six live cells, observed temperature/flow trends, status/limits, measured-vs-truth-vs-prediction/action legend, timestamped incidents and reasoning/citations; browser gate recorded separately |
| 4 counterfactual explorer | PASS bounded model | Existing native minimax candidates now selectable; feasibility failures, temperature, modeled energy/downtime and native sampled uncertainty; private analysis only. Physical isolation/restart/repair BLOCKED, not modeled. |
| 5 forecasting | PARTIAL | Fixed observed OLS trend versus persistence/65 C guard on 30 new-seed native episodes; 2 TP, 2 FP, 18 FN; 60s lead on two correlated TP windows; no calibration/generalization claim |
| 6 adversarial resilience | PASS selected checks | Six named attack families, 13 actual native/crypto assertions. Stale signed capability uses explicit storage doubles; historical real CTAP2 browser evidence stays separately attributed. Finite coverage, no certification. |
| 7 integration/demo/submission | PASS (clean 398 Python / 3 CTest / 35 Node / 17 Chromium; 180.016s demo) | New typed read-only APIs, generated contracts, recorded experiment panel, verified 180s browser demo and clean-source gate; see docs/results/SPRINT_FINAL.md |
| Dedicated MI300X / Evolus / physical production | BLOCKED | No new device/provider/physical proof; never implied by local tests |

The 30-case targeted fault-free native operating-confounder demonstration reduces
unsupported diagnoses from 30 to zero. It is a development counterexample set,
not independent held-out accuracy. Diagnosis/forecast raw results, protocol,
source/native hashes and raw rows are retained in docs/results; initial weaker
AI development run is retained too. No changes were made after seeing the final
holdout. Existing Pinecone records are untouched, with no provider request needed.

## Run and inspect

Follow README's frozen dependency setup and `python tools/dev.py start`.
Connect with the local viewer token; inspect the live six-cell trends, allow at
least ten seconds for the forecast window, and load recorded experiments.
The forecast accepts no scenario/ground-truth fields. Run an isolated fault and
investigate it, then compare actual native candidates and rejection reasons.
No analysis UI result can enable a protected write.

Run `python tools/sprint_adversary.py --output docs/results/sprint-attacks-new.json`
after building the QA image to execute
named attacks with network disabled. New reports must use fresh evidence paths
when preserving an already-delivered measurement. Native evaluators are
`tools/evaluate_sprint_ai.py`, `tools/evaluate_sprint_ai_confounders.py` and
`tools/evaluate_forecasting.py`; see their result documents for exact protocols.
Run `python tools/dev.py check` for the complete configured regression gate.
Run `python tools/clean_demo.py --evidence-prefix sprint-new` then
`python tools/check_clean_source.py --evidence-prefix sprint-new` for isolated
source export, fresh credentials/storage and the complete clean gate.
Choose a fresh prefix each time; delivered `sprint-verified` evidence is preserved.

## Judge narration

- 0–30s: Six actual native cells and live observed-flow/temperature traces. Show
  observed versus simulator truth. Forecast is a fixed experimental extrapolation,
  not a measured future or industrial calibration.
- 30–75s: Run private seeded fault copies; sentinel catches deceptive evidence;
  cyclic graph gathers cited sources and uses conservative grounded candidates.
  Its offline language backend abstains. Historical AMD evidence is labeled replay.
- 75–115s: Compare native recovery candidates; inspect infeasibility, energy,
  downtime and robust sampled priors. Manual contradiction means no incident
  authority. Show the tradeoff between stopping and modeled lost production.
- 115–150s: Separate stationary sandbox demonstrates virtual CTAP2 approval,
  exact immutable diff, independent execution and receipt. This does not authorize
  the faulty original plant. Completed commissioned receipt is read-only history.
- 150–180s: Show recorded evaluation/attack evidence and limitations. Explain
  lowered confounder false assertions alongside lower diagnosis recall and weak
  forecast sensitivity. Export replay; dedicated hardware/physical gates blocked.

The existing runner provides the reliable timed/captured acceptance path. These
extra panels can be inspected during its matching cues or a manual narration;
do not label a historical provider run as a fresh live call.

## Criteria and limitations

The supplied constitution names AMD ACT III Track 1 Intelligent Industry and
requires coupled physics, useful reasoning, independent authorization, measurable
results and an operational demonstration. No official scoring rubric was supplied
in the repository; official eligibility/criteria verification remains BLOCKED.
No first-place, MI300X/HBM, Evolus tool, real-world diagnostic accuracy, physical
passkey, equipment repair or production deployment claim is made.
