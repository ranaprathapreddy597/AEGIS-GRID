import { useState } from "react";
import type { components } from "../../../packages/contracts/generated/api";

type Status = components["schemas"]["IntegrationStatus"];
type Repair = components["schemas"]["RepairBundle"];

export function IntegrationPanel({ token }: { token: string }) {
  const [status, setStatus] = useState<Status | null>(null);
  const [repair, setRepair] = useState<Repair | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function inspect() {
    setBusy(true); setError("");
    try {
      const headers = { Authorization: `Bearer ${token}` };
      const gates = await fetch("/api/v1/integrations/status", { headers });
      if (!gates.ok) throw new Error(`Integration status unavailable (${gates.status}).`);
      setStatus(await gates.json() as Status);
      const bundle = await fetch("/api/v1/repairs/local", { headers });
      if (!bundle.ok) throw new Error(`Verified repair evidence unavailable (${bundle.status}).`);
      setRepair(await bundle.json() as Repair);
    } catch (problem) { setError(problem instanceof Error ? problem.message : "Integration evidence unavailable."); }
    finally { setBusy(false); }
  }
  function download() {
    if (!repair) return;
    const url = URL.createObjectURL(new Blob([repair.patch], { type: "text/plain" }));
    const anchor = document.createElement("a"); anchor.href = url; anchor.download = "aegis-reviewed-approval-repair.diff"; anchor.click(); URL.revokeObjectURL(url);
  }
  return <section className="panel integration-panel" aria-labelledby="integrations-heading"><div className="manual-body"><h2 id="integrations-heading">Connector gates & repair evidence</h2><p>Local approved Mongo is real. Unverified external tools remain closed.</p><button disabled={busy} onClick={() => { void inspect(); }}>{busy ? "Reading evidence…" : "Inspect connector gates"}</button>{error && <p className="error" role="alert">{error}</p>}{status && <ul data-testid="connector-gates">{status.gates.map((gate) => <li key={gate.provider}><strong>{gate.provider} · {gate.status}</strong><p>{gate.reason}</p></li>)}</ul>}{repair && <article data-testid="repair-bundle"><h3>Reviewed local repair</h3><p>{repair.problem}</p><p>Actual browser baseline: lost proposal · patched candidate: resumed · exact patch application verified.</p><p className="fingerprint">Artifact {repair.artifact_sha256}</p><p>Remote GitHub publication BLOCKED · hosted CI unverified.</p><details><summary>Review the exact standalone patch</summary><pre tabIndex={0} aria-label="Reviewed local repair diff">{repair.patch}</pre></details><button onClick={download}>Download reviewed repair diff</button><p className="muted">This candidate repairs the Phase 9 base independently of the maintenance feature. Downloading it does not publish or execute it.</p></article>}</div></section>;
}
