"""Actual cyclic LangGraph with physics reasoning, native forecasts and a durable interrupt."""

import asyncio
import hashlib
import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypedDict

from aegis_contracts.investigation import DiagnosticHypothesis, GraphTrace, Investigation
from aegis_contracts.models import AnomalyEvidence, IncidentRecord, SensorFrame, SimulatorControls
from aegis_edge.sentinel import SafetyShield
from aegis_edge.twin import NativeTwin, scenario_from_file
from aegis_inference.client import OfflineDevelopmentBackend, VLLMClient
from aegis_ingestion.library import fixture_library
from langchain_core.runnables import RunnableLambda
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from aegis_agents.history import observed_window, summarize


class State(TypedDict):
    report_json: str


def diagnose(
    sensor: SensorFrame | None, evidence: list[AnomalyEvidence]
) -> list[DiagnosticHypothesis]:
    """Only observed channels/residuals. Scenario labels/snapshot truth cannot enter."""
    scores: dict[str, tuple[float, str]] = {}
    if any(abs(item.residual_c) > 2 for item in evidence):
        scores["sensor_bias"] = (0.9, "Independent physics estimate disagrees with sensor")
    if any(item.observed_temperature_c >= 70 and abs(item.residual_c) <= 2 for item in evidence):
        scores["true_thermal"] = (0.9, "High sensor reading agrees with independent estimate")
    if sensor:
        if any(cell.flow_kg_s < 0.02 for cell in sensor.cells):
            scores["restricted_flow"] = (0.6, "Observed branch flow below synthetic envelope")
        if sensor.loop_pressure_kpa < 20:
            scores["weak_pump"] = (0.5, "Observed common pressure is low")
        if any(cell.load_fraction > 0.9 for cell in sensor.cells):
            scores["overload"] = (0.5, "High observed load adds heat demand")
    return [
        DiagnosticHypothesis.model_validate(
            {"cause": cause, "support_score": score, "explanation": explanation}
        )
        for cause, (score, explanation) in sorted(
            scores.items(), key=lambda item: (-item[1][0], item[0])
        )
    ]


def forecast(record: IncidentRecord, controls: SimulatorControls | None, library: Path) -> float:
    snapshot = record.event.snapshot
    if snapshot is None:
        raise ValueError("Native snapshot required; no invented forecast")
    # Initial scenario is immediately replaced by the complete validated native snapshot.
    with NativeTwin(scenario_from_file(Path("data/scenarios"), "scenario-000"), library) as twin:
        twin.restore(
            json.dumps({"sha256": snapshot.sha256, "payload": snapshot.payload_json}).encode()
        )
        if controls is not None:
            twin.controls(snapshot.state_version, controls)
        maximum = 0.0
        for _ in range(120):
            frame = twin.step(1.0)
            maximum = max(maximum, max(cell.temperature_c for cell in frame.ground_truth.cells))
        return maximum


def build_graph(
    record: IncidentRecord,
    checkpointer: Any,
    library: Path,
    backend: OfflineDevelopmentBackend | VLLMClient | None = None,
) -> Any:
    model = backend or OfflineDevelopmentBackend()
    graph = StateGraph(State)

    def node(name: str, function: Callable[[dict[str, Any]], str]) -> Callable[[State], State]:
        def run(state: State) -> State:
            started = time.perf_counter_ns()
            data = Investigation.model_validate_json(state["report_json"]).model_dump()
            detail = function(data)
            data["traces"].append(
                GraphTrace(
                    node=name,
                    iteration=data["iteration"],
                    elapsed_ms=(time.perf_counter_ns() - started) / 1e6,
                    detail=detail,
                ).model_dump()
            )
            report = Investigation.model_validate(data)
            return {"report_json": report.model_dump_json()}

        return run

    def sentinel(data: dict[str, Any]) -> str:
        if record.event.kind != "anomaly":
            raise ValueError("Investigation requires an anomaly event")
        return "Native incident accepted; local emergency policy remains independent"

    def collect(data: dict[str, Any]) -> str:
        data["iteration"] += 1
        samples = observed_window(record.event.observed_history)
        largest = max(record.event.evidence, key=lambda item: abs(item.residual_c), default=None)
        target = int(largest.cell_id[-2:]) - 1 if largest else 0
        slopes, correlations = summarize(samples, target)
        data["observed_history_samples"] = len(samples)
        data["observed_temperature_slopes_c_s"] = slopes
        data["observed_neighbor_correlations"] = correlations
        return (
            "Observed history/trends and neighbor Pearson correlations; constant channels undefined"
        )

    def detective(data: dict[str, Any]) -> str:
        data["hypotheses"] = [
            item.model_dump() for item in diagnose(record.event.observed, record.event.evidence)
        ]
        if isinstance(model, VLLMClient):
            data["refusal"] = "MI300X live gate blocked; remote budget preflight unverified"
            return str(data["refusal"])
        remaining = data["model_token_budget"] - data["model_tokens_used"]
        if remaining < 128:
            data["refusal"] = "Model budget exhausted"
            return "No further model call"
        result = asyncio.run(
            model.investigate(
                json.dumps(
                    {
                        "observed": record.event.observed.model_dump()
                        if record.event.observed
                        else None,
                        "residuals": [item.model_dump() for item in record.event.evidence],
                        "observed_temperature_slopes_c_s": data["observed_temperature_slopes_c_s"],
                        "observed_neighbor_correlations": data["observed_neighbor_correlations"],
                    }
                ),
                min(remaining, 256),
            )
        )
        data["backend"] = result.backend
        used = (result.prompt_tokens or 0) + (result.completion_tokens or 0)
        if used > remaining:
            raise ValueError("Actual model usage exceeds investigation budget")
        data["model_tokens_used"] += used
        return "Physics hypotheses retained; model opinion has no policy or execution authority"

    def manual(data: dict[str, Any]) -> str:
        evidence = fixture_library().evidence("CELL-01 temperature flow")
        data["manual_decision"] = evidence.decision.status
        data["evidence_page_hashes"] = [hit.citation.page_sha256 for hit in evidence.hits]
        return "FAISS exact-citation evidence; full-corpus contradiction gate checked"

    def cascade(data: dict[str, Any]) -> str:
        data["baseline_maximum_temperature_c"] = forecast(record, None, library)
        data["native_binary_sha256"] = hashlib.sha256(library.read_bytes()).hexdigest()
        return "Actual C++ 120-second unmitigated counterfactual, not observed sensor evidence"

    def blue(data: dict[str, Any]) -> str:
        load = 0.6 if data["iteration"] == 1 else 0.0
        data["candidates"].append(
            {
                "candidate_id": f"blue-{data['iteration']}",
                "controls": {"pump": 1.0, "loads": [load] * 6, "valves": [1.0] * 6},
                "rationale": "Productivity candidate"
                if load
                else "Preserve deterministic local stop",
                "red_accepted": False,
                "simulation_checked": False,
                "maximum_temperature_c": None,
                "executable": False,
            }
        )
        return "Bounded typed controls proposed; no plant/executor write"

    def red(data: dict[str, Any]) -> str:
        candidate = data["candidates"][-1]
        candidate["red_accepted"] = all(load == 0 for load in candidate["controls"]["loads"])
        return (
            "Latched-stop recovery rejected" if not candidate["red_accepted"] else "Stop preserved"
        )

    def referee(data: dict[str, Any]) -> str:
        candidate = data["candidates"][-1]
        candidate["maximum_temperature_c"] = forecast(
            record, SimulatorControls.model_validate(candidate["controls"]), library
        )
        candidate["simulation_checked"] = True
        if candidate["maximum_temperature_c"] >= 70:
            candidate["red_accepted"] = False
        return "Real C++ candidate rollout; synthetic 70 degC hard bound checked"

    def shield(data: dict[str, Any]) -> str:
        candidate = data["candidates"][-1]
        if not SafetyShield.authorize(
            SimulatorControls.model_validate(candidate["controls"]),
            record.event.state_version,
            record.event.snapshot.state_version if record.event.snapshot else -1,
        ):
            candidate["red_accepted"] = False
        if data["manual_decision"] == "no_action":
            data["refusal"] = "Unresolved manual evidence; no action"
        if not data["candidates"][-1]["red_accepted"]:
            data["refusal"] = "Adversarial or native rollout refusal"
        return data["refusal"] or "Proposal still requires separate human authorization"

    def route(state: State) -> str:
        data = Investigation.model_validate_json(state["report_json"])
        if not data.candidates[-1].red_accepted and data.iteration < data.max_iterations:
            return "evidence_collector"
        return "reporter"

    def reporter(data: dict[str, Any]) -> str:
        data["status"] = "paused_no_action"
        return "Investigation complete through candidates; protected gateway untouched"

    functions = {
        "sentinel": sentinel,
        "evidence_collector": collect,
        "causal_detective": detective,
        "manual_expert": manual,
        "cascade_forecaster": cascade,
        "blue_planner": blue,
        "red_examiner": red,
        "simulation_referee": referee,
        "safety_shield": shield,
        "reporter": reporter,
    }
    names = list(functions)
    for name, function in functions.items():
        graph.add_node(name, RunnableLambda(node(name, function)))
    graph.add_edge(START, names[0])
    for current, following in zip(names[:-2], names[1:-1], strict=True):
        graph.add_edge(current, following)
    graph.add_conditional_edges("safety_shield", route, ["evidence_collector", "reporter"])

    def approval(state: State) -> State:
        interrupt(
            {
                "gate": "human_approval",
                "operational_write_allowed": False,
                "reason": "Phase 9 authorization unavailable; evidence may also block",
            }
        )
        raise ValueError("No resume/execution path exists before authorization gate")

    graph.add_node("approval", approval)

    def executor(state: State) -> State:
        raise ValueError("Execution gateway closed until cryptographic authorization is verified")

    def verifier(state: State) -> State:
        report = Investigation.model_validate_json(state["report_json"])
        if report.operational_write_allowed:
            raise ValueError("Unexpected execution authority")
        return state

    graph.add_node("executor", executor)
    graph.add_node("verifier", verifier)
    graph.add_edge("reporter", "approval")
    graph.add_edge("approval", "executor")
    graph.add_edge("executor", "verifier")
    graph.add_edge("verifier", END)
    return graph.compile(checkpointer=checkpointer)
