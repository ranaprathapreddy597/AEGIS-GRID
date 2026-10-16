import { useEffect, useRef, useState } from "react";
import type { components } from "../../../packages/contracts/generated/api";

type Preview = components["schemas"]["ScenarioPreview"];
type Investigation = components["schemas"]["Investigation"];
type Ensemble = components["schemas"]["FuturesEnsemble"];
const scenarios = ["Healthy reference", "Sensor bias", "Frozen sensor", "Coolant blockage", "Weak pump", "Demand burst", "Delayed measurements", "Dropped packets", "Power spike", "Deceptive cascade"];

export function LaboratoryPanel({ token }: { token: string }) {
  const [investigation, setInvestigation] = useState<Investigation | null>(null);
  const investigationKey = useRef(crypto.randomUUID());
  const [family, setFamily] = useState("9");
  const [seed, setSeed] = useState("42");
  const [preview, setPreview] = useState<Preview | null>(null);
  const [ensemble, setEnsemble] = useState<Ensemble | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [cursor, setCursor] = useState(0);
  const [playing, setPlaying] = useState(false);
  useEffect(() => {
    if (!playing || !preview) return;
    const timer = setInterval(() => setCursor((value) => {
      if (value >= preview.samples.length - 1) { setPlaying(false); return value; }
      return value + 1;
    }), 100);
    return () => clearInterval(timer);
  }, [playing, preview]);
  useEffect(() => { investigationKey.current = crypto.randomUUID(); setInvestigation(null); }, [family, seed]);
  async function investigate() {
    setBusy(true); setError("");
    try {
      const response = await fetch("/api/v1/analysis/investigate", { method: "POST", headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json", "Idempotency-Key": investigationKey.current }, body: JSON.stringify({ scenario_id: `scenario-${(Number(family) * 10).toString().padStart(3, "0")}`, seed: Number(seed) }) });
      if (!response.ok) throw new Error(`Investigation refused (${response.status}); a detected anomaly and durable storage are required.`);
      setInvestigation(await response.json() as Investigation);
    } catch (problem) { setError(problem instanceof Error ? problem.message : "Investigation unavailable."); }
    finally { setBusy(false); }
  }
  async function run() {
    setBusy(true); setError(""); setPlaying(false);
    try {
      const response = await fetch("/api/v1/analysis/scenario", { method: "POST", headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" }, body: JSON.stringify({ scenario_id: `scenario-${(Number(family) * 10).toString().padStart(3, "0")}`, seed: Number(seed) }) });
      if (!response.ok) throw new Error(`Analysis unavailable (${response.status})${response.status === 429 ? "; capacity reached, retry shortly" : ""}.`);
      setPreview(await response.json() as Preview); setCursor(0); setPlaying(true);
    } catch (problem) { setError(problem instanceof Error ? problem.message : "Analysis unavailable."); }
    finally { setBusy(false); }
  }
  async function futures() {
    setBusy(true); setError("");
    try {
      const response = await fetch("/api/v1/analysis/futures", { headers: { Authorization: `Bearer ${token}` } });
      if (!response.ok) throw new Error(`Verified futures unavailable (${response.status}).`);
      setEnsemble(await response.json() as Ensemble);
    } catch (problem) { setError(problem instanceof Error ? problem.message : "Futures unavailable."); }
    finally { setBusy(false); }
  }
  function download() {
    if (!preview) return;
    const url = URL.createObjectURL(new Blob([JSON.stringify(preview, null, 2)], { type: "application/json" }));
    const anchor = document.createElement("a"); anchor.href = url; anchor.download = `aegis-analysis-${preview.request.scenario_id}-${preview.request.seed}.json`; anchor.click(); URL.revokeObjectURL(url);
  }
  const sample = preview?.samples[cursor];
  const y = (temperature: number) => 175 - (temperature - 20) * 1.5;
  const maximumBin = Math.max(1, ...(ensemble?.histogram.flatMap((bin) => [bin.baseline, bin.intervention]) ?? []));
  return <section className="panel laboratory-panel" aria-labelledby="laboratory-heading"><div className="manual-body">
    <div className="section-kicker">COUNTERFACTUAL LAB / PRIVATE C++ COPIES</div><h2 id="laboratory-heading">Inject a fault. Examine the consequence.</h2>
    <p>Run a seeded fault in two isolated analysis copies, then replay their actual recorded frames at 100×. The live edge and approval sandbox are separate. No operational mutation occurs.</p>
    <form className="lab-controls" onSubmit={(event) => { event.preventDefault(); void run(); }}>
      <label>Fault family<select value={family} onChange={(event) => setFamily(event.target.value)}>{scenarios.map((name, index) => <option key={name} value={index}>{name}</option>)}</select></label>
      <label>Replay seed<input type="number" min="0" max="4294967295" step="1" required value={seed} onChange={(event) => setSeed(event.target.value)}/></label>
      <button disabled={busy || !seed}>{busy ? "Computing…" : "Run isolated fault"}</button><button type="button" disabled={busy || !seed} onClick={() => { void investigate(); }}>Investigate selected fault</button><button type="button" disabled={busy} onClick={() => { void futures(); }}>Inspect 10,000 actual futures</button>
    </form>{error && <p role="alert" className="error">{error}</p>}
    {preview && sample && <div data-testid="laboratory-replay">
      <div className="lab-readout"><div><span>RECORDED CLOCK</span><strong>{sample.baseline.simulation_time_s.toFixed(0)} / 600 s</strong></div><div><span>SENTINEL DETECTION</span><strong>{preview.detection_s === null ? "No detection" : `${preview.detection_s.toFixed(1)} s`}</strong></div><div><span>BASELINE PEAK / SHIELDED PEAK</span><strong>{preview.baseline_peak_c.toFixed(2)} / {preview.shielded_peak_c.toFixed(2)} °C</strong></div></div>
      <div className="actions"><button onClick={() => setPlaying(!playing)} disabled={cursor === preview.samples.length - 1}>{playing ? "Pause replay" : "Play replay"}</button><button onClick={() => { setCursor(0); setPlaying(false); }}>Reset replay</button><button onClick={download}>Download analysis replay</button></div>
      <label className="scrubber">Recorded frame {cursor + 1} / {preview.samples.length}<input aria-label="Analysis replay position" type="range" min="0" max={preview.samples.length - 1} value={cursor} onChange={(event) => { setPlaying(false); setCursor(Number(event.target.value)); }}/></label>
      <div className="paired-cells">{[sample.baseline, sample.shielded].map((frame, side) => <div key={side}><h3>{side === 0 ? "Unmitigated analysis" : "Independent shield analysis"}</h3><div className="mini-cells">{frame.cells.map((cell, index) => <div className={frame.ground_truth.cells[index]!.temperature_c >= 70 ? "hot" : ""} key={cell.cell_id}><span>{cell.cell_id}</span><strong>{cell.temperature_c.toFixed(1)} °C</strong><small>Truth {frame.ground_truth.cells[index]!.temperature_c.toFixed(1)} °C · flow {frame.ground_truth.cells[index]!.flow_kg_s.toFixed(3)}</small></div>)}</div></div>)}</div>
      <svg className="lab-chart" viewBox="0 0 660 200" role="img" aria-label="Actual paired replay: red unmitigated maximum truth temperature and green shielded maximum truth temperature"><line x1="40" x2="640" y1={y(70)} y2={y(70)} stroke="#c69c62" strokeDasharray="4 4"/><text x="42" y={y(70)-8}>70 °C thermal bound</text>{[0, 1].map((side) => <polyline key={side} points={preview.samples.slice(0, cursor+1).map((item, i) => `${40+i/59*600},${y(Math.max(...(side === 0 ? item.baseline : item.shielded).ground_truth.cells.map((cell) => cell.temperature_c)))}`).join(" ")} fill="none" stroke={side === 0 ? "#f29898" : "#77dfc4"} strokeWidth="2.5"/>)}<text x="40" y="195">0 s</text><text x="600" y="195">600 s</text></svg>
      <p className="replay-policy">RECORDED ANALYSIS · {sample.sentinel?.state.replaceAll("_", " ") ?? "Awaiting delivered sensors"} · source and final state hashes included in download</p><p className="fingerprint">ARTIFACT {preview.artifact_sha256}</p>
    </div>}
    {investigation && <div data-testid="laboratory-investigation"><h3>Selected fault · real persistent LangGraph</h3><p className="manual-decision">{investigation.status} · {investigation.refusal}</p><p>{investigation.iteration} actual cycles · {investigation.backend} · private analysis origin · no operational authority</p><div className="causal-strip" aria-label="Selected fault actual graph transitions">{investigation.traces.map((trace, index) => <span key={index}><small>Cycle {trace.iteration}</small>{trace.node.replaceAll("_", " ")}</span>)}</div><ul>{investigation.hypotheses.map((item) => <li key={item.cause}><strong>{item.cause.replaceAll("_", " ")}</strong> · support {item.support_score.toFixed(2)} (not probability) · {item.explanation}</li>)}</ul>{investigation.recovery_assessment && <><h3>Selected fault · actual Red / Blue tournament</h3><p>{investigation.recovery_assessment.total_rollouts} actual rollouts · manual action gate BLOCKED</p><div className="table-scroll" tabIndex={0} aria-label="Selected fault actual candidates"><table><thead><tr><th>Candidate</th><th>Feasible</th><th>Worst peak / °C</th><th>Assumed cost</th></tr></thead><tbody>{investigation.recovery_assessment.candidates.map((item) => <tr key={item.candidate_id}><td>{item.candidate_id}</td><td>{item.feasible ? "yes" : `${item.failed_cases} failures`}</td><td>{item.worst_temperature_c.toFixed(2)}</td><td>{item.worst_objective.toFixed(2)}</td></tr>)}</tbody></table></div></>}<p>Use the cited manual panel to inspect the contradiction. Ask First below operates only on its separately identified stationary authorization resource.</p><p className="fingerprint">Persisted investigation {investigation.investigation_id} · source incident {investigation.incident_id}</p></div>}
    {ensemble && <div data-testid="futures-ensemble"><div className="section-kicker">MEASURED CPU ENSEMBLE / PRECOMPUTED</div><h3>10,000 native futures. 5,000 paired priors.</h3><p>Red bars: unmitigated baseline · green bars: exact emergency stop.</p><p>Scenario-090 seed 42 · 600 seconds per future · 120,000,000 native substeps. This fixed experiment is independent of the selected fault and current live incident.</p>
      <svg className="histogram" viewBox="0 0 660 245" role="img" aria-label="Histogram of actual maximum temperatures: red baseline, green emergency stop"><text x="35" y="18">Peak temperature distribution · counts per 10 °C bin</text>{ensemble.histogram.map((bin, index) => <g key={bin.lower_c}><rect x={35+index*60} y={200-bin.baseline/maximumBin*150} width="23" height={bin.baseline/maximumBin*150} fill="#f29898"/><rect x={60+index*60} y={200-bin.intervention/maximumBin*150} width="23" height={bin.intervention/maximumBin*150} fill="#77dfc4"/><text x={38+index*60} y="224">{bin.lower_c}°</text></g>)}</svg>
      <div className="table-scroll" tabIndex={0} aria-label="Actual future counts and economics"><table><caption>Actual synthetic outcomes; production and downtime expose the stop's tradeoff.</caption><thead><tr><th>Metric</th><th>Baseline</th><th>Exact stop</th></tr></thead><tbody><tr><th>Constraint failures / 5,000</th><td>{ensemble.baseline_failed}</td><td>{ensemble.intervention_failed}</td></tr><tr><th>Mean energy / kWh</th><td>{ensemble.baseline_mean_energy_kwh.toFixed(3)}</td><td>{ensemble.intervention_mean_energy_kwh.toFixed(3)}</td></tr><tr><th>Mean production / model units</th><td>{ensemble.baseline_mean_production.toFixed(3)}</td><td>{ensemble.intervention_mean_production.toFixed(3)}</td></tr><tr><th>Mean stop downtime / s</th><td>—</td><td>{ensemble.intervention_mean_downtime_s.toFixed(1)}</td></tr>{ensemble.histogram.map((bin) => <tr key={bin.lower_c}><th>{bin.lower_c}–{bin.upper_c} °C{bin.lower_c === 20 || bin.upper_c === 120 ? " (outer overflow included)" : ""}</th><td>{bin.baseline}</td><td>{bin.intervention}</td></tr>)}</tbody></table></div>
      <details><summary>Inspect real failure cases and assumptions</summary><ul>{ensemble.counterexamples.map((item) => <li key={item.case}>Prior {item.case} · seed {item.seed} · cell {item.target+1} · severity {item.severity.toFixed(3)} · {item.baseline_peak_c.toFixed(2)} → {item.intervention_peak_c.toFixed(2)} °C · violation masks {item.baseline_violations} → {item.intervention_violations}</li>)}</ul>{ensemble.assumptions.map((item) => <p key={item}>{item}</p>)}</details><p className="fingerprint">ENSEMBLE {ensemble.artifact_sha256}</p>
    </div>}
  </div></section>;
}
