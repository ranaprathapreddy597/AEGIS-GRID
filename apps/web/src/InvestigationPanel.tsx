import { useEffect, useRef, useState } from "react";
import type { components } from "../../../packages/contracts/generated/api";

type Report = components["schemas"]["Investigation"];

export function InvestigationPanel({ token, incidentId }: { token: string; incidentId?: string }) {
  const [report, setReport] = useState<Report | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const key = useRef(crypto.randomUUID());
  useEffect(() => { key.current = crypto.randomUUID(); setReport(null); setError(""); }, [incidentId]);
  async function investigate() {
    if (!incidentId) return;
    setBusy(true); setError("");
    try {
      const response = await fetch(`/api/v1/incidents/${incidentId}/investigate`, { method: "POST", headers: { Authorization: `Bearer ${token}`, "Idempotency-Key": key.current } });
      if (!response.ok) throw new Error(`Investigation unavailable (${response.status}).`);
      setReport(await response.json() as Report);
    } catch (problem) { setError(problem instanceof Error ? problem.message : "Investigation unavailable."); }
    finally { setBusy(false); }
  }
  return <section className="panel investigation-panel" aria-labelledby="investigation-heading"><div className="manual-body"><h2 id="investigation-heading">Forensic investigation</h2><p>Persistent LangGraph · physics reasoners + C++ forecasts · labeled offline model template</p><button disabled={busy || !incidentId} onClick={() => { void investigate(); }}>{busy ? "Investigating…" : "Investigate latest incident"}</button>{!incidentId && <p>Waiting for a recorded simulator anomaly.</p>}{error && <p role="alert" className="error">{error}</p>}
    {report && <div data-testid="investigation-report"><p className="manual-decision"><strong>PAUSED · NO ACTION</strong> · {report.refusal}</p><p>{report.backend} · {report.iteration} investigation cycles · {report.live_gates}</p><div className="causal-strip" aria-label="Actual graph transitions">{report.traces.slice(0, 18).map((trace, index) => <span key={index}><small>{trace.iteration} / {index + 1}</small>{trace.node.replaceAll("_", " ")}{index < Math.min(17, report.traces.length - 1) && <b aria-hidden="true">→</b>}</span>)}</div><div className="hypothesis-grid">{report.hypotheses.map((item) => <article key={item.cause}><strong>{item.cause.replaceAll("_", " ")}</strong><p>{item.explanation}</p><small>Heuristic support {item.support_score.toFixed(2)} · not a probability</small></article>)}</div><p>Actual unmitigated C++ forecast peak: {report.baseline_maximum_temperature_c?.toFixed(2) ?? "unavailable"} °C</p><ul>{report.candidates.map((candidate) => <li key={candidate.candidate_id}>{candidate.candidate_id} · load {Math.round(Math.max(0, ...candidate.controls.loads) * 100)}% · {candidate.red_accepted ? "retained for review" : "rejected by Red/Shield"} · C++ peak {candidate.maximum_temperature_c?.toFixed(2)} °C · execution closed</li>)}</ul><details><summary>Inspect causal and adversarial trace ({report.traces.length} steps)</summary><ol>{report.traces.map((trace, index) => <li key={index}><strong>{trace.node.replaceAll("_", " ")}</strong> · cycle {trace.iteration} · {trace.elapsed_ms.toFixed(2)} ms<p>{trace.detail}</p></li>)}</ol></details><p className="muted">Investigation {report.investigation_id} · independent emergency shield remains active.</p></div>}
  </div></section>;
}
