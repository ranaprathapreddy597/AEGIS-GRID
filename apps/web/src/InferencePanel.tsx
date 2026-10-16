import { useState } from "react";
import type { components } from "../../../packages/contracts/generated/api";

type Budget = components["schemas"]["MemoryBudget"];

export function InferencePanel({ token }: { token: string }) {
  const [budget, setBudget] = useState<Budget | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function calculate(capacity: number) {
    setBusy(true); setError("");
    try {
      const response = await fetch(`/api/v1/inference/memory?capacity_gib=${capacity}`, { headers: { Authorization: `Bearer ${token}` } });
      if (!response.ok) throw new Error(`Budget unavailable (${response.status}).`);
      setBudget(await response.json() as Budget);
    } catch (problem) { setError(problem instanceof Error ? problem.message : "Budget unavailable."); }
    finally { setBusy(false); }
  }
  return <section className="panel inference-panel" aria-labelledby="inference-heading"><div className="manual-body"><h2 id="inference-heading">Cloud inference readiness</h2><p>MI300X live gate blocked · no hardware timings or 200K success verified.</p><p>Qwen3-Coder-30B-A3B-Instruct · upstream native context 262,144 · full BF16 weights</p><div className="actions"><button disabled={busy} onClick={() => { void calculate(80); }}>Project 80 GiB budget</button><button disabled={busy} onClick={() => { void calculate(192); }}>Project 192 GiB budget</button></div>{error && <p role="alert" className="error">{error}</p>}{budget && <div data-testid="memory-budget"><p><strong>{budget.projected_fits ? "PROJECTED HEADROOM" : "DOES NOT FIT"}</strong> · 2 sequences × 262,144 tokens · BF16 KV</p><dl><dt>Resident weights</dt><dd>{budget.weight_gib.toFixed(2)} GiB</dd><dt>KV cache</dt><dd>{budget.kv_gib.toFixed(2)} GiB</dd><dt>Total with assumed overhead</dt><dd>{budget.total_gib.toFixed(2)} / {budget.capacity_gib} GiB</dd></dl><p>Projection only. Driver compatibility, usable HBM, kernel workspaces and runtime performance require device measurements. Advertised 192 GB and 192 GiB differ; the CLI also reports a conservative decimal-GB case.</p></div>}</div></section>;
}
