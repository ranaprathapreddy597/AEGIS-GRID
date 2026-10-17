import { useEffect, useRef, useState } from "react";
import { streamInvestigation } from "./stream";
import type { components } from "../../../packages/contracts/generated/api";

type Eligibility = components["schemas"]["RecoveryEligibility"];

type Report = components["schemas"]["Investigation"];

export function InvestigationPanel({ token, incidentId }: { token: string; incidentId?: string }) {
  const [eligibility, setEligibility] = useState<Eligibility | null>(null);
  const [report, setReport] = useState<Report | null>(null);
  const [mode, setMode] = useState("offline");
  const [streamState, setStreamState] = useState("");
  useEffect(() => { void fetch("/api/v1/investigation-mode", { headers: { Authorization: `Bearer ${token}` } }).then(async r => { if (r.ok) setMode((await r.json() as { mode: string }).mode); }).catch(() => {}); }, [token]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const active = useRef<AbortController | null>(null);
  const key = useRef(crypto.randomUUID());
  useEffect(() => { active.current?.abort(); key.current = crypto.randomUUID(); setReport(null); setEligibility(null); setError(""); return () => active.current?.abort(); }, [incidentId]);
  async function investigate() {
    if (!incidentId) return;
    setBusy(true); setError("");
    const controller = new AbortController();
    active.current = controller;
    const streaming = streamInvestigation(token, key.current, controller.signal, value => { setReport(value); setStreamState("Live graph checkpoints received"); }).catch(() => { if (!controller.signal.aborted) setStreamState("Checkpoint stream unavailable; final report retained"); });
    try {
      const response = await fetch(`/api/v1/incidents/${incidentId}/investigate`, { method: "POST", signal: controller.signal, headers: { Authorization: `Bearer ${token}`, "Idempotency-Key": key.current } });
      if (!response.ok) throw new Error(`Investigation unavailable (${response.status}).`);
      const value = await response.json() as Report;
      if (!controller.signal.aborted) setReport(value);
      const gate = await fetch(`/api/v1/investigations/${value.investigation_id}/recovery-eligibility`, { headers: { Authorization: `Bearer ${token}` }, signal: controller.signal });
      if (!gate.ok) throw new Error(`Recovery eligibility unavailable (${gate.status}); execution closed.`);
      if (!controller.signal.aborted) setEligibility(await gate.json() as Eligibility);
    } catch (problem) { setError(problem instanceof Error ? problem.message : "Investigation unavailable."); }
    finally { controller.abort(); await streaming; setBusy(false); }
  }
  return <section className="panel investigation-panel" aria-labelledby="investigation-heading"><div className="manual-body"><h2 id="investigation-heading">Forensic investigation</h2><p>Persistent LangGraph · physics reasoners + C++ forecasts · configured mode: {mode}</p><button disabled={busy || !incidentId} onClick={() => { void investigate(); }}>{busy ? "Investigating…" : "Investigate selected incident"}</button>{!incidentId && <p>Waiting for a recorded simulator anomaly.</p>}{error && <p role="alert" className="error">{error}</p>}
    {streamState && <p role="status">{streamState}</p>}{report && <div data-testid="investigation-report"><p className="manual-decision"><strong>{report.status === "running" ? "INVESTIGATION RUNNING" : "PAUSED - NO ACTION"}</strong> · {report.refusal}</p><p>{report.backend} · {report.iteration} investigation cycles · {report.live_gates}</p><p>Approval interrupt · independent WebAuthn and safety checks required. Conflicting manuals prohibit incident authorization.</p>{eligibility && <div data-testid="incident-recovery-eligibility"><strong>Incident recovery {eligibility.status}</strong><p>Meaningful hosted diagnosis: {eligibility.meaningful_hosted_diagnosis ? "yes" : "no"} · Grounded hosted plan: {eligibility.grounded_hosted_planning ? "yes" : "no"}</p><p>{eligibility.blockers.join("; ")}</p><p>Incident {eligibility.incident_id} · manual corpus {eligibility.manual_corpus_sha256} · no incident challenge or capability issued.</p></div>}<ul>{report.model_attributions?.map(model => <li key={model.role}>{model.role}: AMD {model.served_model} · requested {model.requested_model} · {model.latency_ms.toFixed(0)} ms · {model.prompt_tokens + model.completion_tokens} tokens · hardware unverified</li>)}</ul>{(report.provider_failures?.length ?? 0) > 0 && <p role="status">{report.provider_failures?.join("; ")}</p>}<details><summary>Verified source citations ({report.source_citations?.length ?? 0})</summary><ul>{report.source_citations?.map(source => <li key={source.reference_id}><strong>{source.title}</strong> · {source.synthetic ? "SYNTHETIC" : "External reference"} · {source.applicability}<p>{source.namespace} · {source.reference_id}</p><p>{source.source} · revision {source.revision} · SHA256 {source.source_sha256}</p><p>{source.license} · {source.attribution}</p></li>)}</ul></details><div className="causal-strip" aria-label="Actual graph transitions">{report.traces.slice(0, 18).map((trace, index) => <span key={index}><small>{trace.iteration} / {index + 1}</small>{trace.node.replaceAll("_", " ")}{index < Math.min(17, report.traces.length - 1) && <b aria-hidden="true">→</b>}</span>)}</div><div className="hypothesis-grid">{report.hypotheses.map((item) => <article key={item.cause}><strong>{item.cause.replaceAll("_", " ")}</strong><p>{item.explanation}</p><small>Heuristic support {item.support_score.toFixed(2)} · not a probability</small></article>)}</div><p>Actual unmitigated C++ forecast peak: {report.baseline_maximum_temperature_c?.toFixed(2) ?? "unavailable"} °C</p><ul>{report.candidates.map((candidate) => <li key={candidate.candidate_id}>{candidate.candidate_id} · load {Math.round(Math.max(0, ...candidate.controls.loads) * 100)}% · {candidate.red_accepted ? "retained for review" : "rejected by Red/Shield"} · C++ peak {candidate.maximum_temperature_c?.toFixed(2)} °C · execution closed</li>)}</ul><details><summary>Inspect causal and adversarial trace ({report.traces.length} steps)</summary><ol>{report.traces.map((trace, index) => <li key={index}><strong>{trace.node.replaceAll("_", " ")}</strong> · cycle {trace.iteration} · {trace.elapsed_ms.toFixed(2)} ms<p>{trace.detail}</p></li>)}</ol></details><p className="muted">Investigation {report.investigation_id} · independent emergency shield remains active.</p></div>}
  </div></section>;
}
