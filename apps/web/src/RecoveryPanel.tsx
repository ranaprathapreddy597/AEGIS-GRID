import { useEffect, useState } from "react";
import type { components } from "../../../packages/contracts/generated/api";

type Assessment = components["schemas"]["RecoveryAssessment"];
function strategyName(candidate: components["schemas"]["PlanEvaluation"]) {
  if (candidate.candidate_id === "planted-unsafe") return "planted-unsafe / adversarial control";
  const maximumLoad = Math.max(...candidate.controls.loads);
  return maximumLoad === 0 ? `Safe stop + cooldown / ${Math.round(candidate.controls.pump * 100)}% pump` : `${Math.round(maximumLoad * 100)}% load / ${Math.round(candidate.controls.pump * 100)}% pump`;
}

export function RecoveryPanel({ token, incidentId }: { token: string; incidentId?: string }) {
  const [report, setReport] = useState<Assessment | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [candidateId, setCandidateId] = useState<string | null>(null);
  useEffect(() => { setReport(null); setCandidateId(null); setError(""); }, [incidentId]);
  async function search() {
    if (!incidentId) return;
    setBusy(true); setError("");
    try {
      const response = await fetch(`/api/v1/incidents/${incidentId}/optimize`, { method: "POST", headers: { Authorization: `Bearer ${token}` } });
      if (!response.ok) throw new Error(`Recovery search unavailable (${response.status}).`);
      const value = await response.json() as Assessment;
      setReport(value); setCandidateId(value.selected_candidate_id ?? value.candidates[0]?.candidate_id ?? null);
    } catch (problem) { setError(problem instanceof Error ? problem.message : "Recovery search unavailable."); }
    finally { setBusy(false); }
  }
  const baseline = report?.baseline;
  const intervention = report?.intervention;
  const selected = report?.candidates.find(candidate => candidate.candidate_id === candidateId);
  const ceiling = Math.max(80, baseline?.maximum_temperature_c ?? 80);
  const points = (samples: components["schemas"]["FutureSample"][]) => samples.map((item) => `${10 + item.elapsed_s / 600 * 580},${180 - item.maximum_temperature_c / ceiling * 160}`).join(" ");
  return <section className="panel recovery-panel" aria-labelledby="recovery-heading"><div className="manual-body"><h2 id="recovery-heading">Adversarial recovery search</h2><p>Finite minimax · actual C++ physics · isolated counterfactuals</p><button disabled={busy || !incidentId} onClick={() => { void search(); }}>{busy ? "Simulating futures…" : "Compare recovery futures"}</button>{!incidentId && <p>Waiting for a recorded anomaly.</p>}{error && <p role="alert" className="error">{error}</p>}
    {report && <div data-testid="recovery-report"><p className="manual-decision"><strong>{report.status === "abstained" ? "ABSTAINED" : "CHECKED · NON-EXECUTABLE"}</strong> · {report.reason}</p><p>{report.total_rollouts} actual rollouts · {report.cases.length} initial-state cases · {report.native_substeps.toLocaleString()} native substeps</p>{baseline && intervention && <><svg viewBox="0 0 600 200" role="img" aria-label="Actual C++ maximum temperature timelines: unmitigated and selected intervention, zero to 600 seconds"><line x1="10" x2="590" y1={180 - 70 / ceiling * 160} y2={180 - 70 / ceiling * 160} stroke="currentColor" strokeDasharray="4 4" /><polyline fill="none" stroke="#f19e96" strokeWidth="3" points={points(baseline.samples)} /><polyline fill="none" stroke="#7ddcd0" strokeWidth="3" points={points(intervention.samples)} /></svg><p>Unmitigated peak {baseline.maximum_temperature_c.toFixed(2)} °C · intervention {intervention.maximum_temperature_c.toFixed(2)} °C · synthetic bound 70 °C</p><p>Selected: {report.selected_candidate_id} · production {intervention.production_units.toFixed(2)} synthetic units · downtime {intervention.downtime_s.toFixed(0)} s · {intervention.energy_kwh.toFixed(3)} kWh</p></>}
      <div className="explorer-heading"><div><span className="section-kicker">COUNTERFACTUAL EXPLORER</span><h3>Inspect the tradeoffs. Keep authority separate.</h3><p>Choose an evaluated native strategy to inspect its measured synthetic outcomes. Selection changes this view only.</p></div><span className="boundary-tag predicted">PREDICTED / NON-EXECUTABLE</span></div>
      <div className="candidate-picker" aria-label="Native recovery strategy selection">{report.candidates.map(candidate => <button key={candidate.candidate_id} aria-pressed={candidateId === candidate.candidate_id} onClick={() => setCandidateId(candidate.candidate_id)}><strong>{strategyName(candidate)}</strong><span>{candidate.feasible ? `Feasible in ${candidate.checked_cases} checked cases` : `${candidate.failed_cases} counterexamples`}</span></button>)}</div>
      {selected && <div className="candidate-inspection" data-testid="candidate-inspection"><div className="candidate-status"><h3>{selected.candidate_id}</h3><strong className={selected.feasible ? "feasible" : "infeasible"}>{selected.feasible ? "FEASIBLE IN SAMPLED PRIORS" : "INFEASIBLE"}</strong></div><div className="outcome-grid"><div><span>Worst peak</span><strong>{selected.worst_temperature_c.toFixed(2)} °C</strong></div><div><span>Maximum downtime</span><strong>{selected.maximum_downtime_s.toFixed(0)} s</strong></div><div><span>Mean energy</span><strong>{selected.mean_energy_kwh.toFixed(3)} kWh</strong></div><div><span>Minimum production</span><strong>{selected.minimum_production_units.toFixed(2)} units</strong></div></div><p>These aggregates span {selected.checked_cases} explicit initial-state priors, not a calibrated confidence interval. Risk is represented by hard-constraint failures ({selected.failed_cases}); no real-world risk probability is modeled.</p><p>Pump {Math.round(selected.controls.pump * 100)}% · cell loads {selected.controls.loads.map(value => `${Math.round(value * 100)}%`).join(" / ")} · valves {selected.controls.valves.map(value => `${Math.round(value * 100)}%`).join(" / ")}</p>{selected.counterexamples.length > 0 && <details><summary>Inspect native refusal evidence ({selected.counterexamples.length})</summary><pre>{JSON.stringify(selected.counterexamples, null, 2)}</pre></details>}<p className="muted">The paired timeline above belongs to the optimizer-selected candidate {report.selected_candidate_id ?? "none"}; other candidates expose aggregate outcomes only. Isolation is available only if explicitly represented by the controls above; fault clearance and restart are unsupported.</p></div>}
      <div className="recovery-table"><table><caption>Blue candidates / Red counterexamples</caption><thead><tr><th>Candidate</th><th>Hard constraints</th><th>Worst peak</th><th>Worst assumed cost</th></tr></thead><tbody>{report.candidates.map((candidate) => <tr key={candidate.candidate_id}><td>{candidate.candidate_id}{candidate.candidate_id === report.selected_candidate_id && " · selected"}</td><td>{candidate.feasible ? `${candidate.checked_cases}/${candidate.checked_cases} checked` : `${candidate.failed_cases} failures`}</td><td>{candidate.worst_temperature_c.toFixed(1)} °C</td><td>{candidate.worst_objective.toFixed(2)}</td></tr>)}</tbody></table></div>
      <details><summary>Scope, evidence hashes and assumptions</summary><ul>{report.assumptions.map((item) => <li key={item}>{item}</li>)}</ul><p className="fingerprint">Artifact {report.artifact_sha256}</p><p className="fingerprint">Native binary {report.native_binary_sha256}</p></details><p className="muted">Manual action gate BLOCKED · {report.live_gates}. Costs are dimensionless assumptions. The running edge latch remains active.</p></div>}
  </div></section>;
}
