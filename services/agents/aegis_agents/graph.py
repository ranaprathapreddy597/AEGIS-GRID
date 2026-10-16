"""Actual cyclic LangGraph with physics reasoning, native forecasts and a durable interrupt."""

import asyncio
import hashlib
import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypedDict

from aegis_contracts.inference import ModelOpinion, PlanningOpinion
from aegis_contracts.investigation import DiagnosticHypothesis, GraphTrace, Investigation
from aegis_contracts.models import AnomalyEvidence, IncidentRecord, SensorFrame, SimulatorControls
from aegis_edge.sentinel import SafetyShield
from aegis_edge.twin import NativeTwin, scenario_from_file
from aegis_inference.client import InferenceUnavailable, OfflineDevelopmentBackend, VLLMClient
from aegis_inference.token_factory import TokenFactoryClient
from aegis_ingestion.evolus import ProviderUnavailable
from aegis_ingestion.knowledge import KnowledgeChunk
from aegis_ingestion.library import fixture_library
from aegis_ingestion.semantic_store import SemanticStore
from langchain_core.runnables import RunnableLambda
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from aegis_agents.history import observed_window, summarize
from aegis_agents.optimizer import optimize


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
    backend: OfflineDevelopmentBackend | VLLMClient | TokenFactoryClient | None = None,
    knowledge: SemanticStore | None = None,
) -> Any:
    model = backend or OfflineDevelopmentBackend()
    graph = StateGraph(State)
    retrieved: dict[str, list[KnowledgeChunk]] = {}

    def retrieve(data: dict[str, Any], kind: str, query: str) -> list[dict[str, str]]:
        if knowledge is None:
            return []
        if kind not in retrieved:
            try:
                retrieved[kind] = asyncio.run(knowledge.search(query, kind=kind))
            except ProviderUnavailable:
                retrieved[kind] = []
                data["provider_failures"].append("Pinecone unavailable; local evidence retained")
        hits = retrieved[kind]
        if hits:
            data["retrieval_backend"] = "pinecone_semantic"
            data["live_gates"] = "MI300X/Evolus BLOCKED; Pinecone synthetic retrieval verified"
            data["retrieved_source_ids"] = sorted(
                set(data["retrieved_source_ids"] + [hit.identifier for hit in hits])
            )[:15]
        return [{"id": hit.identifier, "untrusted_text": hit.text[:600]} for hit in hits[:2]]

    def hosted(data: dict[str, Any], evidence: dict[str, Any], planning: bool) -> str:
        assert isinstance(model, TokenFactoryClient)  # noqa: S101 - internal narrowing
        field = "hosted_planning" if planning else "hosted_diagnosis"
        if data[field] is not None or data["iteration"] > (2 if planning else 1):
            return "Hosted opinion already attempted; no repeated quota consumption"
        payload = json.dumps(evidence)
        remaining = data["model_token_budget"] - data["model_tokens_used"]
        # UTF-8 bytes are a conservative token admission estimate for bounded ASCII evidence.
        if len(payload.encode()) + 1800 > remaining:
            data["provider_failures"].append("AMD graph token preflight abstention")
            return "Insufficient hosted budget; deterministic local reasoning retained"
        try:
            result = asyncio.run(
                model.plan(payload, 256) if planning else model.investigate(payload, 256)
            )
            used = result.prompt_tokens + result.completion_tokens
            if used > remaining:
                raise InferenceUnavailable("AMD actual usage exceeds graph budget")
            data["model_tokens_used"] += used
            data["backend"] = result.backend
            expected = PlanningOpinion if planning else ModelOpinion
            if not isinstance(result.opinion, expected):
                raise InferenceUnavailable("Unexpected hosted schema")
            data[field] = result.opinion.model_dump()
            return (
                "Validated AMD opinion recorded; independent numerical safety remains authoritative"
            )
        except InferenceUnavailable:
            data["provider_failures"].append("AMD unavailable/refused; local fallback/abstention")
            return "AMD unavailable; deterministic local reasoning retained"

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
        if isinstance(model, TokenFactoryClient):
            sources = retrieve(
                data, "manual", "temperature sensor disagreement coolant flow safety"
            )
            return hosted(
                data,
                {
                    "observed": [
                        {"temperature_c": c.temperature_c, "flow_kg_s": c.flow_kg_s}
                        for c in record.event.observed.cells
                    ]
                    if record.event.observed
                    else [],
                    "residuals": [e.model_dump() for e in record.event.evidence][:2],
                    "retrieved_sources": sources,
                },
                False,
            )
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
        retrieve(data, "manual", "temperature sensor disagreement coolant flow safety")
        evidence = fixture_library().evidence("CELL-01 temperature flow")
        data["manual_decision"] = evidence.decision.status
        data["evidence_page_hashes"] = [hit.citation.page_sha256 for hit in evidence.hits]
        return "Verified source retrieval; local full-corpus contradiction gate checked"

    def cascade(data: dict[str, Any]) -> str:
        if data["recovery_assessment"] is None:
            data["recovery_assessment"] = optimize(record, library).model_dump()
        if data["baseline_maximum_temperature_c"] is None:
            data["baseline_maximum_temperature_c"] = forecast(record, None, library)
        data["native_binary_sha256"] = hashlib.sha256(library.read_bytes()).hexdigest()
        return "Actual C++ 120-second unmitigated counterfactual, not observed sensor evidence"

    def blue(data: dict[str, Any]) -> str:
        sources = retrieve(data, "recovery", "minimax recovery emergency stop thermal safety")
        search = data["recovery_assessment"]
        selected = next(
            (
                item
                for item in search["candidates"]
                if item["candidate_id"] == search["selected_candidate_id"]
            ),
            None,
        )
        if data["iteration"] == 1:
            controls = {"pump": 0.0, "loads": [1.0] * 6, "valves": [0.0] * 6}
            rationale = "Deliberately flawed productivity candidate for Red challenge"
        elif data["iteration"] == 2 and selected:
            controls = selected["controls"]
            rationale = "Minimax optimum; still subject to independent latched-stop policy"
            if isinstance(model, TokenFactoryClient):
                hosted(
                    data,
                    {
                        "candidate_evaluations": {
                            "minimax_candidate": {"feasible": selected["feasible"]},
                            "emergency_stop": "Independent policy requires latched stop",
                        },
                        "retrieved_sources": sources,
                    },
                    True,
                )
                opinion = data["hosted_planning"]
                if not opinion or opinion["recommendation"] != "minimax_candidate":
                    controls = SafetyShield.emergency_controls().model_dump()
                    rationale = "Hosted stop/abstention or unavailable; preserve independent stop"
        else:
            controls = SafetyShield.emergency_controls().model_dump()
            rationale = "Preserve independent emergency stop after adversarial feedback"
        data["candidates"].append(
            {
                "candidate_id": f"blue-{data['iteration']}",
                "controls": controls,
                "rationale": rationale,
                "red_accepted": False,
                "simulation_checked": False,
                "maximum_temperature_c": None,
                "executable": False,
            }
        )
        return "Bounded typed controls proposed; no plant/executor write"

    def red(data: dict[str, Any]) -> str:
        candidate = data["candidates"][-1]
        checked = next(
            (
                item
                for item in data["recovery_assessment"]["candidates"]
                if item["controls"] == candidate["controls"]
            ),
            None,
        )
        candidate["red_accepted"] = bool(checked and checked["feasible"]) and (
            candidate["controls"] == SafetyShield.emergency_controls().model_dump()
        )
        return (
            "Counterexample or independent latched-stop policy rejected candidate"
            if not candidate["red_accepted"]
            else "All 37 native cases checked; stop preserved"
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
