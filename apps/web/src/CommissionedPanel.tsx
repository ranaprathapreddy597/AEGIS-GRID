import { useEffect, useRef, useState } from "react";
import type { components } from "../../../packages/contracts/generated/api";

type Status = components["schemas"]["CommissionedStatus"];
type Report = components["schemas"]["CommissionedReport"];
type View = components["schemas"]["CommissionedView"];
type Challenge = components["schemas"]["ApprovalChallenge"];

export function CommissionedPanel({token}: {token: string}) {
  const [status, setStatus] = useState<Status | null>(null);
  const [report, setReport] = useState<Report | null>(null);
  const [view, setView] = useState<View | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const key = useRef(crypto.randomUUID());
  async function request<T>(path: string, method = "GET", body?: unknown): Promise<T> {
    const response = await fetch(path, {method, credentials: "same-origin", headers: {Authorization: `Bearer ${token}`, ...(body === undefined ? {} : {"Content-Type": "application/json"}), "Idempotency-Key": key.current}, ...(body === undefined ? {} : {body: JSON.stringify(body)})});
    if (!response.ok) throw new Error(`Commissioned operation refused (${response.status}). Start an owner approval session and check evidence, passkey and state.`);
    return await response.json() as T;
  }
  useEffect(() => { let active = true; void (async () => {
    try {
      const response = await fetch("/api/v1/commissioned/status", {headers: {Authorization: `Bearer ${token}`}});
      if (response.ok && active) setStatus(await response.json() as Status);
    } catch { if (active) setError("Commissioned fixture unavailable."); }
  })(); return () => { active = false; }; }, [token]);
  async function run(action: () => Promise<void>) {
    setBusy(true); setError("");
    try { await action(); } catch (problem) { setError(problem instanceof Error ? problem.message : "Commissioned operation unavailable."); }
    finally { setBusy(false); }
  }
  async function approve() {
    if (!view) return;
    const challenge = await request<Challenge>(`/api/v1/approval/commissioned/proposals/${view.action_id}/options`, "POST");
    if (challenge.bound_plan_sha256 !== view.plan_sha256) throw new Error("Commissioned reviewed digest differs from challenge.");
    const api = PublicKeyCredential as typeof PublicKeyCredential & {parseRequestOptionsFromJSON: (options: unknown) => PublicKeyCredentialRequestOptions};
    const credential = await navigator.credentials.get({publicKey: api.parseRequestOptionsFromJSON(challenge.options)});
    if (!(credential instanceof PublicKeyCredential) || !(credential.response instanceof AuthenticatorAssertionResponse)) throw new Error("Commissioned passkey cancelled.");
    const response = credential.response;
    const encode = (v: ArrayBuffer) => btoa(String.fromCharCode(...new Uint8Array(v))).replaceAll("+", "-").replaceAll("/", "_").replaceAll("=", "");
    setView(await request<View>(`/api/v1/approval/commissioned/proposals/${view.action_id}/verify`, "POST", {ceremony_id: challenge.ceremony_id, credential: {id: credential.id, rawId: encode(credential.rawId), type: credential.type, clientExtensionResults: credential.getClientExtensionResults(), response: {authenticatorData: encode(response.authenticatorData), clientDataJSON: encode(response.clientDataJSON), signature: encode(response.signature), userHandle: response.userHandle ? encode(response.userHandle) : null}}}));
  }
  return <section className="panel commissioned-panel" aria-labelledby="commissioned-heading"><div className="manual-body">
    <h2 id="commissioned-heading">Commissioned simulator recovery</h2>
    <p>Separate frozen incident replay · safe-stop containment and cooldown · no physical I/O, fault repair or production restart.</p>
    <p>Use the owner session and enrolled passkey in “Ask first. Verify again.” Original contradictory-manual incidents remain blocked.</p>
    {status && <><p data-testid="commissioned-identity">{status.plant_id} · {status.rules_revision} · incident {status.incident_id}</p><p>Authenticated rule package SHA256 {status.rules_sha256}. Origin: repository engineering fixture. Automated review; no OEM approval.</p><p>Shared loop: pump 1.00 · all six loads 0.00 · all six valves 1.00 · 120 simulated seconds. Hard limit 70°C; independent 65°C operating guard retained.</p><details><summary>Inspect signed rule origin, review status and applicability</summary><pre>{JSON.stringify(status.rule_package, null, 2)}</pre></details></>}
    {status && !status.enabled && <p>Commissioned execution is explicitly disabled in this configuration.</p>}
    <button disabled={busy || !status || !status.enabled || !!status.receipts.length} onClick={() => { void run(async () => { setReport(await request<Report>("/api/v1/approval/commissioned/investigate", "POST")); }); }}>Investigate commissioned incident</button>
    {report && <article data-testid="commissioned-report"><h3>{report.status.replaceAll("_", " ")}</h3><p>Meaningful hosted diagnosis: {report.meaningful_diagnosis ? "yes" : "no"} · Grounded planning: {report.grounded_planning ? "yes" : "no"}</p><p>Diagnosis: {report.diagnosis?.assessment ?? "unavailable"} · {report.diagnosis?.hypotheses.join(", ")}. Plan: {report.planning?.recommendation ?? "unavailable"}.</p><p>{report.blockers.join("; ")}</p><p>Native rollouts: {report.assessment?.total_rollouts ?? 0} · unsafe challenger {report.unsafe_challenger_rejected ? "rejected" : "unverified"} · exact-stop peak {report.certificate?.maximum_temperature_c.toFixed(3)}°C.</p><p>Investigation {report.investigation_id} · report SHA256 {report.report_sha256}</p><ul>{report.model_attributions.map(a => <li key={a.role}>{a.role}: {a.served_model} · {a.latency_ms.toFixed(0)} ms · hardware unverified</li>)}</ul><details><summary>Commissioned source context ({report.source_citations.length})</summary><ul>{report.source_citations.map(c => <li key={c.reference_id}>{c.title} · {c.reference_id} · {c.namespace} · {c.license} · original plant {c.plant_id} · context only; no commissioned equipment authority</li>)}</ul></details><p>{report.traces.join(" → ")}</p><button disabled={busy || report.status !== "awaiting_approval" || !!view} onClick={() => { void run(async () => { setView(await request<View>(`/api/v1/approval/commissioned/investigations/${report.investigation_id}/proposal`, "POST")); }); }}>Prepare incident-bound recovery</button></article>}
    {view && <article data-testid="commissioned-proposal"><h3>{view.status}</h3><p>Reviewed incident action digest {view.plan_sha256}</p><details><summary>Inspect exact commissioned incident action</summary><pre>{JSON.stringify(JSON.parse(view.action_json), null, 2)}</pre></details><button disabled={busy || view.status !== "waiting_for_passkey"} onClick={() => { void run(approve); }}>Approve commissioned action with passkey</button><button disabled={busy || view.status !== "approved"} onClick={() => { void run(async () => { setView(await request<View>(`/api/v1/approval/commissioned/proposals/${view.action_id}/execute`, "POST", {plan_sha256: view.plan_sha256})); setStatus(await request<Status>("/api/v1/commissioned/status")); }); }}>Execute approved incident recovery</button>{view.receipt && <div data-testid="commissioned-receipt"><p>{view.receipt.outcome} · {view.receipt.authorization} · receipt {view.receipt.receipt_sha256}</p><p>Maximum cell temperature {Math.max(...view.receipt.temperatures_before_c).toFixed(3)} → {Math.max(...view.receipt.temperatures_after_c).toFixed(3)}°C. Fault retained; production restart disabled.</p></div>}</article>}
    {status && status.receipts.length > 0 && !view && <p>Commissioned incident already contained. Persistent receipt {status.receipts[0]?.receipt_sha256}. No repeat execution or public reset.</p>}
    {busy && <p role="status">Commissioned operation in progress…</p>}{error && <p role="alert" className="error">{error}</p>}
  </div></section>;
}
