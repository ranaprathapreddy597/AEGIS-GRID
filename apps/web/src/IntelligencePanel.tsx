import { useEffect, useRef, useState } from "react";
import type { components } from "../../../packages/contracts/generated/api";
import type { Telemetry } from "./stream";

type Forecast = components["schemas"]["ThermalForecast"];
type Evidence = components["schemas"]["SprintEvidence"];

export function IntelligencePanel({ token, history, live }: { token: string; history: Telemetry[]; live: boolean }) {
  const [forecast, setForecast] = useState<Forecast | null>(null);
  const [forecastFrame, setForecastFrame] = useState<number | null>(null);
  const [evidence, setEvidence] = useState<Evidence | null>(null);
  const [evidenceError, setEvidenceError] = useState("");
  const [error, setError] = useState("");
  const frames = useRef(history);
  frames.current = history;
  useEffect(() => {
    const controller = new AbortController();
    void fetch("/api/v1/analysis/sprint-evidence", { headers: { Authorization: `Bearer ${token}` }, signal: controller.signal }).then(async response => {
      if (!response.ok) throw new Error(`Recorded evaluation unavailable (${response.status}).`);
      setEvidence(await response.json() as Evidence);
    }).catch(problem => { if (!controller.signal.aborted) setEvidenceError(problem instanceof Error ? problem.message : "Recorded evaluation unavailable."); });
    return () => controller.abort();
  }, [token]);
  useEffect(() => {
    const controller = new AbortController();
    let inFlight = false;
    const update = async () => {
      if (!frames.current.length || inFlight || !live) return;
      inFlight = true;
      // Explicit observation allowlist: no ground truth, injected masks or scenario labels.
      const observations = frames.current.map(({ cells, coolant_temperature_c, loop_pressure_kpa, measurement, simulation_time_s, state_version }) => ({ cells, coolant_temperature_c, loop_pressure_kpa, measurement, simulation_time_s, state_version }));
      try {
        const response = await fetch("/api/v1/analysis/forecast", { method: "POST", signal: controller.signal, headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" }, body: JSON.stringify({ history: observations }) });
        if (!response.ok) throw new Error(`Thermal forecast unavailable (${response.status}).`);
        const value = await response.json() as Forecast;
        if (!controller.signal.aborted) { setForecast(value); setForecastFrame(observations.at(-1)?.state_version ?? null); setError(""); }
      } catch (problem) { if (!controller.signal.aborted) { setForecast(null); setError(problem instanceof Error ? problem.message : "Thermal forecast unavailable."); } }
      finally { inFlight = false; }
    };
    void update();
    const timer = setInterval(() => { void update(); }, 5000);
    return () => { controller.abort(); clearInterval(timer); };
  }, [token, live, history.at(-1)?.run_id]);
  return <section className="panel intelligence-panel" aria-labelledby="intelligence-heading"><div className="manual-body"><div className="explorer-heading"><div><span className="section-kicker">PREDICTIVE INTELLIGENCE / OBSERVED INPUT ONLY</span><h2 id="intelligence-heading">See the trend. Measure the limits.</h2><p>Local deterministic extrapolation · no cloud calls · no control authority</p></div><span className="boundary-tag predicted">60 SECOND FORECAST</span></div>
    {error && <p role="alert" className="error">{error}</p>}{evidenceError && <p role="alert" className="error">{evidenceError}</p>}
    {!live && <p className="manual-decision">Signal stale or unavailable · forecasting paused · retained predictions are not current.</p>}
    {forecast ? <div data-testid="thermal-forecast"><p className="forecast-state"><strong>{forecast.status === "abstained" ? "ABSTAINED" : forecast.warning ? "THERMAL WARNING" : "NO PREDICTED CROSSING"}</strong> · {forecast.reason} · {forecast.observation_count} fresh independent samples · source frame #{forecastFrame}</p>{forecast.cells.length > 0 && <div className="forecast-grid">{forecast.cells.map(cell => <article key={cell.cell_id} className={cell.warning ? "forecast-warning" : ""}><span>{cell.cell_id}</span><strong>{cell.projected_temperature_c.toFixed(1)} °C</strong><p>+{forecast.horizon_s} s projected</p><small>Observed {cell.observed_temperature_c.toFixed(1)} °C<br/>Heuristic error ±{cell.extrapolation_error_c.toFixed(2)} °C<br/>{cell.crossing_in_s !== null && cell.crossing_in_s <= forecast.horizon_s ? `70 °C crossing in ${cell.crossing_in_s.toFixed(1)} s` : "No crossing within horizon"}</small></article>)}</div>}<p className="muted">{forecast.limitation}</p></div> : <p>Waiting for fresh observations and the local forecast service.</p>}
    {evidence && <div data-testid="sprint-evidence"><h3>Recorded evaluation</h3><p>Offline experiments from preserved artifacts. These results describe synthetic simulator fixtures and are separate from this live forecast.</p><div className="experiment-grid">{evidence.experiments.map(experiment => <article key={experiment.name}><span className="capability-state">{experiment.state}</span><h4>{experiment.name}</h4><p>{experiment.scope}</p><dl>{experiment.metrics.map(metric => <div key={metric.name}><dt>{metric.name.replaceAll("_", " ")}</dt><dd>{metric.value === null ? "unavailable" : metric.unit === "fraction" ? `${(metric.value * 100).toFixed(1)}%` : `${metric.value.toFixed(2)} ${metric.unit}`}</dd></div>)}</dl><details><summary>Limits and artifact provenance</summary><ul>{experiment.limitations.map(limit => <li key={limit}>{limit}</li>)}</ul><p>{experiment.artifact}</p><code>{experiment.artifact_sha256}</code></details></article>)}</div><h3>Reproducible adversarial boundary checks</h3><div className="attack-grid">{evidence.attacks.map(attack => <article key={attack.name}><span>{attack.state === "PASS" ? "BOUNDARY CHECK PASSED" : "BOUNDARY CHECK FAILED"}</span><h4>{attack.name}</h4><p>{attack.reason}</p><small>{attack.passed} actual passing checks · {attack.selector}</small></article>)}</div><ul className="evaluation-limits">{evidence.limitations.map(limit => <li key={limit}>{limit}</li>)}</ul></div>}
  </div></section>;
}
