import { useEffect, useState } from "react";
import type { components } from "../../../packages/contracts/generated/api";

type View = components["schemas"]["ApprovalView"];
type Session = components["schemas"]["ApprovalSession"];
type Challenge = components["schemas"]["ApprovalChallenge"];

function encode(value: ArrayBuffer): string {
  return btoa(String.fromCharCode(...new Uint8Array(value))).replaceAll("+", "-").replaceAll("/", "_").replaceAll("=", "");
}
function credentialJSON(value: PublicKeyCredential): Record<string, unknown> {
  const response = value.response;
  const common = { id: value.id, rawId: encode(value.rawId), type: value.type, clientExtensionResults: value.getClientExtensionResults() };
  if (response instanceof AuthenticatorAttestationResponse) return { ...common, response: { clientDataJSON: encode(response.clientDataJSON), attestationObject: encode(response.attestationObject), transports: response.getTransports() } };
  if (response instanceof AuthenticatorAssertionResponse) return { ...common, response: { clientDataJSON: encode(response.clientDataJSON), authenticatorData: encode(response.authenticatorData), signature: encode(response.signature), userHandle: response.userHandle ? encode(response.userHandle) : null } };
  throw new Error("Unsupported authenticator response.");
}

export function ApprovalPanel() {
  const [ownerToken, setOwnerToken] = useState("");
  const [session, setSession] = useState<Session | null>(null);
  const [view, setView] = useState<View | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const supported = window.location.hostname === "localhost" && window.isSecureContext && !!window.PublicKeyCredential;
  function rememberView(value: View) {
    setView(value);
    try { sessionStorage.setItem("aegis-active-approval", value.action_id); } catch { /* Non-secret UI restore is optional when browser storage is unavailable. */ }
  }
  useEffect(() => {
    if (!supported) return;
    let active = true;
    void (async () => {
      try {
        const response = await fetch("/api/v1/approval/session", { credentials: "same-origin" });
        if (!response.ok || !active) return;
        setSession(await response.json() as Session);
        const id = sessionStorage.getItem("aegis-active-approval");
        if (!id || !/^[0-9a-f-]{36}$/.test(id)) return;
        const saved = await fetch(`/api/v1/approval/proposals/${id}`, { credentials: "same-origin" });
        if (saved.ok && active) setView(await saved.json() as View);
      } catch { if (active) setError("Saved approval could not be restored. Reconnect or start a new owner session."); }
    })();
    return () => { active = false; };
  }, [supported]);
  async function request<T>(path: string, body?: unknown, authorization?: string, method = "POST"): Promise<T> {
    const response = await fetch(`/api/v1/approval/${path}`, { method, credentials: "same-origin", headers: { ...(body === undefined ? {} : { "Content-Type": "application/json" }), ...(authorization ? { Authorization: `Bearer ${authorization}` } : {}) }, ...(body === undefined ? {} : { body: JSON.stringify(body) }) });
    if (!response.ok) throw new Error(`Approval refused (${response.status}). Check session, passkey and current state.`);
    return await response.json() as T;
  }
  async function run(action: () => Promise<void>) {
    setBusy(true); setError(""); setMessage("");
    try { await action(); } catch (problem) { setError(problem instanceof Error ? problem.message : "Approval unavailable."); }
    finally { setBusy(false); }
  }
  async function login() {
    const secret = ownerToken; setOwnerToken("");
    setSession(await request<Session>("session", undefined, secret));
    setMessage("Owner session established. Passkey verification is still required for every action.");
  }
  async function enroll() {
    const challenge = await request<Challenge>("registration/options");
    const api = PublicKeyCredential as typeof PublicKeyCredential & { parseCreationOptionsFromJSON: (options: unknown) => PublicKeyCredentialCreationOptions };
    const value = await navigator.credentials.create({ publicKey: api.parseCreationOptionsFromJSON(challenge.options) });
    if (!(value instanceof PublicKeyCredential)) throw new Error("Passkey enrollment cancelled.");
    setSession(await request<Session>("registration/verify", { ceremony_id: challenge.ceremony_id, credential: credentialJSON(value) }));
    setMessage("Passkey enrolled with user verification. Hardware attestation is not claimed.");
  }
  async function approve() {
    if (!view) return;
    const challenge = await request<Challenge>(`proposals/${view.action_id}/options`);
    if (challenge.bound_plan_sha256 !== view.plan_sha256) throw new Error("Challenge does not match the reviewed action.");
    const api = PublicKeyCredential as typeof PublicKeyCredential & { parseRequestOptionsFromJSON: (options: unknown) => PublicKeyCredentialRequestOptions };
    const value = await navigator.credentials.get({ publicKey: api.parseRequestOptionsFromJSON(challenge.options) });
    if (!(value instanceof PublicKeyCredential)) throw new Error("Passkey approval cancelled.");
    rememberView(await request<View>(`proposals/${view.action_id}/verify`, { ceremony_id: challenge.ceremony_id, credential: credentialJSON(value) }));
    setMessage("Exact action approved. The independent executor will check signature, state and safety again.");
  }
  const plan = view ? JSON.parse(view.action_json) as components["schemas"]["ProposedPlan"] : null;
  return <section className="panel approval-panel" aria-labelledby="approval-heading"><div className="manual-body"><h2 id="approval-heading">Ask first. Verify again.</h2><p>Real WebAuthn · immutable action digest · independent Node executor</p><p className="manual-decision">Authorization test sandbox only. The incident manual conflict remains BLOCKED; the running edge and external systems are outside this action scope.</p>
    {!supported ? <p>Open <a href={`http://localhost:${window.location.port}/`}>the canonical localhost command center</a> in a passkey-capable browser to approve simulator actions.</p> : <>
      {!session ? <form onSubmit={(event) => { event.preventDefault(); void run(login); }}><label htmlFor="owner-token">Local approval owner token</label><input id="owner-token" type="password" value={ownerToken} onChange={(event) => setOwnerToken(event.target.value)} autoComplete="off" required /><p className="muted">Obtain it in your own terminal: <code>python tools/dev.py owner-token</code>. The viewer token cannot enroll or approve.</p><button disabled={busy} type="submit">Start approval session</button></form> : <><p data-testid="approval-session">Owner session · {session.enrolled_credentials} enrolled passkeys · expires {new Date(session.expires_at * 1000).toLocaleTimeString()}</p><div className="actions"><button disabled={busy} onClick={() => { void run(enroll); }}>Enroll passkey</button><button disabled={busy || !session.enrolled_credentials} onClick={() => { void run(async () => { rememberView(await request<View>("proposals")); }); }}>Prepare sandbox stop</button><button disabled={busy} onClick={() => { void run(async () => { const result = await fetch("/api/v1/approval/session", { method: "DELETE", credentials: "same-origin" }); if (!result.ok) throw new Error("Approval session could not be ended."); setSession(null); setView(null); sessionStorage.removeItem("aegis-active-approval"); }); }}>End approval session</button></div></>}
      {view && plan && <article data-testid="approval-proposal"><h3>{view.status.replaceAll("_", " ")}</h3><p>Resource: {plan.resource_id} · database version {plan.expected_database_version} · native version {plan.expected_state_version}</p><dl><dt>Pump target</dt><dd>{plan.before_controls.pump.toFixed(2)} → 1.00</dd><dt>Six load targets</dt><dd>{plan.before_controls.loads.map((v) => v.toFixed(2)).join(" / ")} → all 0.00</dd><dt>Valve targets</dt><dd>all 1.00 · bounded native ramps</dd></dl><p>Scope: isolated stationary authorization sandbox. Compensation retains committed state or emergency stop. Approval expires {new Date(plan.expires_at * 1000).toLocaleTimeString()}.</p><p className="fingerprint">Reviewed digest {view.plan_sha256}</p><details><summary>Inspect exact immutable action and safety artifact</summary><pre tabIndex={0} aria-label="Exact immutable action JSON">{JSON.stringify(plan, null, 2)}</pre></details><div className="actions"><button disabled={busy || view.status !== "waiting_for_passkey"} onClick={() => { void run(approve); }}>Approve exact action with passkey</button><button disabled={busy || view.status !== "approved"} onClick={() => { void run(async () => { rememberView(await request<View>(`proposals/${view.action_id}/execute`, { plan_sha256: view.plan_sha256 })); }); }}>Execute approved sandbox stop</button></div>{view.receipt && <div data-testid="approval-receipt"><h3>Verified simulator receipt</h3><p>Database {view.receipt.database_version_before} → {view.receipt.database_version_after} · native {view.receipt.native_version_before} → {view.receipt.native_version_after}</p><p className="fingerprint">{view.receipt.receipt_sha256}</p><p>Atomic snapshot + nonce + receipt commit · {view.receipt.authorization}</p></div>}</article>}
    </>}{busy && <p role="status">Waiting for verification…</p>}{message && <p role="status">{message}</p>}{error && <p role="alert" className="error">{error}</p>}<p className="muted">Local HTTP owner session, no enterprise identity/TLS claim. CI uses a labeled browser virtual authenticator; physical passkey verification remains unverified.</p></div></section>;
}
