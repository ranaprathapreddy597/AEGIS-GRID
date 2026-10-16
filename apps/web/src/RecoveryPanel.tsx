import { useEffect, useState } from "react";
import type { components } from "../../../packages/contracts/generated/api";

type Assessment = components["schemas"]["RecoveryAssessment"];

export function RecoveryPanel({ token, incidentId }: { token: string; incidentId?: string }) {
  const [report, setReport] = useState<Assessment | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => { setReport(null); setError(""); }, [incidentId]);
  async function search() {
    if (!incidentId) return;
    setBusy(true); setError("");
    try {
      const response = await fetch(`/api/v1/incidents/${incidentId}/optimize`, { method: "POST", headers: { Authorization: `Bearer ${token}` } });
      if (!response.ok) throw new Error(`Recovery search unavailable (${response.status}).`);
      setReport(await response.json() as Assessment);
    } catch (problem) { setError(problem instanceof Error ? problem.message : "Recovery search unavailable."); }
    finally { setBusy(false); }
  }
  const baseline = report?.baseline;
  const intervention = report?.intervention;
  const ceiling = Math.max(80, baseline?.maximum_temperature_c ?? 80);
  const points = (samples: components["schemas"]["FutureSample"][]) => samples.map((item) => `${10 + item.elapsed_s / 600 * 580},${180 - item.maximum_temperature_c / ceiling * 160}`).join(" ");
  return <section className="panel recovery-panel" aria-labelledby="recovery-heading"><div className="manual-body"><h2 id="recovery-heading">Adversarial recovery search</h2><p>Finite minimax · actual C++ physics · isolated counterfactuals</p><button disabled={busy || !incidentId} onClick={() => { void search(); }}>{busy ? "Simulating futures…" : "Compare recovery futures"}</button>{!incidentId && <p>Waiting for a recorded anomaly.</p>}{error && <p role="alert" className="error">{error}</p>}
    {report && <div data-testid="recovery-report"><p className="manual-decision"><strong>{report.status === "abstained" ? "ABSTAINED" : "CHECKED · NON-EXECUTABLE"}</strong> · {report.reason}</p><p>{report.total_rollouts} actual rollouts · {report.cases.length} initial-state cases · {report.native_substeps.toLocaleString()} native substeps</p>{baseline && intervention && <><svg viewBox="0 0 600 200" role="img" aria-label="Actual C++ maximum temperature timelines: unmitigated and selected intervention, zero to 600 seconds"><line x1="10" x2="590" y1={180 - 70 / ceiling * 160} y2={180 - 70 / ceiling * 160} stroke="currentColor" strokeDasharray="4 4" /><polyline fill="none" stroke="#f19e96" strokeWidth="3" points={points(baseline.samples)} /><polyline fill="none" stroke="#7ddcd0" strokeWidth="3" points={points(intervention.samples)} /></svg><p>Unmitigated peak {baseline.maximum_temperature_c.toFixed(2)} °C · intervention {intervention.maximum_temperature_c.toFixed(2)} °C · synthetic bound 70 °C</p><p>Selected: {report.selected_candidate_id} · production {intervention.production_units.toFixed(2)} synthetic units · downtime {intervention.downtime_s.toFixed(0)} s · {intervention.energy_kwh.toFixed(3)} kWh</p></>}
      <div className="recovery-table"><table><caption>Blue candidates / Red counterexamples</caption><thead><tr><th>Candidate</th><th>Hard constraints</th><th>Worst peak</th><th>Worst assumed cost</th></tr></thead><tbody>{report.candidates.map((candidate) => <tr key={candidate.candidate_id}><td>{candidate.candidate_id}{candidate.candidate_id === report.selected_candidate_id && " · selected"}</td><td>{candidate.feasible ? "37/37 checked" : `${candidate.failed_cases} failures`}</td><td>{candidate.worst_temperature_c.toFixed(1)} °C</td><td>{candidate.worst_objective.toFixed(2)}</td></tr>)}</tbody></table></div>
      <details><summary>Scope, evidence hashes and assumptions</summary><ul>{report.assumptions.map((item) => <li key={item}>{item}</li>)}</ul><p className="fingerprint">Artifact {report.artifact_sha256}</p><p className="fingerprint">Native binary {report.native_binary_sha256}</p></details><p className="muted">Manual action gate BLOCKED · {report.live_gates}. Costs are dimensionless assumptions. The running edge latch remains active.</p></div>}
  </div></section>;
}
