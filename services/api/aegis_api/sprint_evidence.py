"""Summaries of preserved experiments, never live accuracy or authorization claims."""

import hashlib
import json
from pathlib import Path
from typing import Any

from aegis_contracts.sprint import AttackCheck, ExperimentMetric, ExperimentSummary, SprintEvidence


def read_report(name: str) -> tuple[dict[str, Any], str]:
    raw = (Path("docs/results") / name).read_bytes()
    value: dict[str, Any] = json.loads(raw)
    return value, hashlib.sha256(raw).hexdigest()


def sprint_evidence() -> SprintEvidence:
    experiments = []
    forecast, fingerprint = read_report("SPRINT_FORECAST.json")
    for method, values in forecast["metrics"].items():
        experiments.append(
            ExperimentSummary(
                name="Thermal forecast / " + method,
                state="PARTIAL",
                scope=f"{forecast['episodes']} new-seed native episodes; "
                f"{forecast['windows']} correlated pre-hazard windows; known fault families",
                metrics=[
                    ExperimentMetric(
                        name=name,
                        value=value,
                        unit="seconds"
                        if name.endswith("_s")
                        else "count"
                        if name in {"tp", "fp", "fn", "tn"}
                        else "fraction",
                    )
                    for name, value in values.items()
                ],
                limitations=forecast["limitations"]
                + ["Low recall and severe class imbalance; accuracy alone is misleading."],
                artifact="SPRINT_FORECAST.json",
                artifact_sha256=fingerprint,
            )
        )
    diagnosis, fingerprint = read_report("sprint-ai-evaluation.json")
    for method in ("grounded", "legacy"):
        values = diagnosis[method]
        experiments.append(
            ExperimentSummary(
                name="Diagnosis / " + method,
                state="PARTIAL",
                scope="Observed-only native synthetic diagnosis; new seeds, known fault families",
                metrics=[
                    ExperimentMetric(name=name, value=values[name])
                    for name in ("precision", "recall", "accuracy", "abstention_coverage")
                ],
                limitations=diagnosis["limitations"]
                + [
                    "Abstention coverage is the fraction with no hypothesis, not accuracy.",
                    "Accuracy counts correct no-cause abstentions; "
                    "seed holdout uses familiar families.",
                    "Grounding trades lower recall for more conservative assertions; "
                    "this evaluation does not show improved accuracy over legacy.",
                ],
                artifact="sprint-ai-evaluation.json",
                artifact_sha256=fingerprint,
            )
        )
    confounders, fingerprint = read_report("sprint-ai-confounders.json")
    experiments.append(
        ExperimentSummary(
            name="Diagnosis / targeted operating confounders",
            state="PASS",
            scope="30 fault-free native commanded operating cases; targeted development checks",
            metrics=[
                ExperimentMetric(
                    name=method + "_false_causes",
                    value=confounders[method]["false_positive_causes"],
                    unit="count",
                )
                for method in ("legacy", "grounded")
            ],
            limitations=[confounders["limitations"]],
            artifact="sprint-ai-confounders.json",
            artifact_sha256=fingerprint,
        )
    )
    adversary, _ = read_report("SPRINT_ADVERSARY.json")
    return SprintEvidence(
        experiments=experiments,
        attacks=[
            AttackCheck.model_validate({key: row[key] for key in AttackCheck.model_fields})
            for row in adversary["checks"]
        ],
        limitations=adversary["limitations"]
        + [
            "Recorded offline experiments; these numbers do not measure hosted LLM accuracy.",
            "Native strategies are analysis only; physical isolation is not modeled.",
        ],
    )
