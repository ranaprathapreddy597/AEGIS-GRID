# Sprint AI quality — PASS implementation, PARTIAL diagnostic coverage

Measured 2026-10-17. This is deterministic CPU reasoning over the actual C++
simulator. No AMD inference, Pinecone request, ingestion, physical action or
protected application write was performed by these evaluators.

The previous numerical detective accepted low common pressure as weak pump,
near-zero flow as restriction, and high load as overload without checking whether
those observations also describe healthy commanded operation. It also allowed a
large transport residual to imply sensor bias. New observed-only ranking:

- Abstains on missing packets or sensor age above two seconds.
- Requires fresh physics-disagreement evidence for sensor bias/freeze; makes no
  claim that disagreement proves malicious spoofing.
- Uses a loaded branch's flow relative to its peers for restricted-flow candidates;
  records the unobserved valve-command confounder explicitly.
- Uses heat above the load-conditioned native envelope for overload candidates.
- Abstains on weak pump because requested pump/valve state is absent from the
  observed diagnostic input. High commanded load alone is insufficient evidence.
- Ranks an independently corroborated thermal symptom after underlying causes.
- Filters future hosted alternatives against independently supported causes;
  context-only citations cannot establish a cause. Empty support or explicit model
  abstention stays abstention. Existing persisted hosted opinions are unchanged.

Scores remain engineering support ranks, not probabilities. Existing approval,
manual contradiction, native rollout, executor and contract boundaries are intact.

## Measured seed holdout

`sprint-ai-evaluation.json` contains all 100 rows, protocol hash, source/binary
hashes and per-family metrics. Ten new seeds each run all ten existing native
families, changing target cell and observation cutoff (90–270 seconds). Inputs
contain no injected mask, scenario ID, seed, hidden truth or source manual text.
Labels enter only metric computation. Expected combined-fault labels include all
four causes, so missed weak pump/overload count as false negatives.

| Metric | Legacy numerical detective | Grounded numerical detective |
|---|---:|---:|
| Micro cause precision | 100% (70/70) | 100% (48/48) |
| Micro cause recall | 70% (70/100) | 48% (48/100) |
| Top-1/appropriate-abstention accuracy | 75% | 65% |
| Top-1 fault recall | 64.29% | 50% |
| Abstention coverage | 55% | 65% |
| Prediction coverage | 45% | 35% |
| Selective top-1 accuracy | 100% | 100% |

Elapsed native evaluator time was 2.4724 s with two CPU cores/768 MiB container
limits. Resource limits are not a measured peak-memory claim. This evaluator
does **not** show improved general diagnosis accuracy: rejecting unidentifiable
causes reduces recall. The lower recall is retained as a material limitation.
Selective accuracy includes only issued top-1 causes and must never be presented
as overall accuracy. Delay/drop families lack a representable root-cause enum and
are scored for appropriate abstention; per-family rows expose that choice.

The initial version, preserved in `sprint-ai-development.json`, required residual
evidence before accepting directly observed relative flow/heat evidence. That
overconservative precondition was removed after inspecting the first 100 cases
(precision 100%, recall 26%, accuracy 47%, abstention 83%). Final seed range starts
1,734,001 instead of development 734,001; the revision precedes the final run.
These are seed-held-out tests of familiar synthetic equations/families, **not**
unseen-fault, independently curated industrial data or hosted-model evaluations.
No further tuning was performed after the final evaluation.

## Targeted confounder demonstration

`sprint-ai-confounders.json` separately runs 30 fault-free native clones: ten seeds
each for intentionally low pump demand, high commanded load, and closed idle
branches. After 60 seconds settling, the previous detector asserted one false
cause in every case (30/30). Grounded ranking abstained in all 30 (zero asserted
false causes). These are targeted post-development counterexamples, reported
separately from the seed holdout; they demonstrate the intended specificity
improvement without disguising the recall tradeoff.

## Verification and reproduction

Focused new confounder/grounding tests plus the existing graph-security and real
native LangGraph tests: **19 passed in 10.30 s**. All-source strict mypy:
**67 source files passed** at this slice. Focused Ruff passed.

Run in the existing QA image with a workspace mount and source PYTHONPATH:

```powershell
$sourcePaths = '/workspace/packages/contracts/python:/workspace/services/agents:/workspace/services/edge:/workspace/services/ingestion:/workspace/services/inference'
docker run --rm --network none --cpus 2 --memory 768m --mount 'type=bind,source=D:\AEGIS GRID,target=/workspace' --workdir /workspace -e "PYTHONPATH=$sourcePaths" --entrypoint python aegis-grid-qa:phase12 tools/evaluate_sprint_ai.py --output /workspace/docs/results/sprint-ai-reproduction.json
docker run --rm --network none --cpus 2 --memory 768m --mount 'type=bind,source=D:\AEGIS GRID,target=/workspace' --workdir /workspace -e "PYTHONPATH=$sourcePaths" --entrypoint python aegis-grid-qa:phase12 tools/evaluate_sprint_ai_confounders.py --output /workspace/docs/results/sprint-ai-confounders-reproduction.json
```

Evaluators reject existing output paths. They instantiate private native objects
and make no live application API call. Repeated run metrics/trajectories should
match; elapsed duration is intentionally machine-dependent. Main/full clean-source
gate evidence belongs to the integrated sprint report, not this focused slice.
