import { useState } from "react";
import type { FormEvent } from "react";
import type { components } from "../../../packages/contracts/generated/api";

type Evidence = components["schemas"]["ManualEvidence"];

export function ManualEvidencePanel({ token }: { token: string }) {
  const [query, setQuery] = useState("CELL-01 temperature");
  const [evidence, setEvidence] = useState<Evidence | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function search(event: FormEvent) {
    event.preventDefault(); setLoading(true); setError("");
    try {
      const response = await fetch(`/api/v1/manuals/evidence?query=${encodeURIComponent(query)}`, { headers: { Authorization: `Bearer ${token}` } });
      if (!response.ok) throw new Error(`Evidence unavailable (${response.status}).`);
      setEvidence(await response.json() as Evidence);
    } catch (problem) { setError(problem instanceof Error ? problem.message : "Evidence unavailable."); }
    finally { setLoading(false); }
  }

  async function download(documentId: string) {
    try {
      const response = await fetch(`/api/v1/manuals/${encodeURIComponent(documentId)}/source`, { headers: { Authorization: `Bearer ${token}` } });
      if (!response.ok) throw new Error(`Source unavailable (${response.status}).`);
      const url = URL.createObjectURL(await response.blob());
      const anchor = document.createElement("a"); anchor.href = url; anchor.download = `${documentId}.pdf`; anchor.click(); URL.revokeObjectURL(url);
    } catch (problem) { setError(problem instanceof Error ? problem.message : "Source unavailable."); }
  }

  return <section className="panel manual-evidence" aria-labelledby="manual-heading">
    <div className="panel-title"><span>05</span><h2 id="manual-heading">Manual evidence room</h2><small>SYNTHETIC CORPUS / 1,000 PAGES</small></div>
    <div className="manual-body"><p>Project-authored simulator references. Evolus and Pinecone live extraction remain unverified. Retrieved text cannot authorize an action.</p>
      <form onSubmit={(event) => { void search(event); }}><label htmlFor="manual-query">Search manual evidence</label><div className="manual-query"><input id="manual-query" value={query} maxLength={500} onChange={(event) => setQuery(event.target.value)} required/><button disabled={loading || !query.trim()}>{loading ? "Retrieving…" : "Retrieve citations"}</button></div></form>
      {error && <p role="alert" className="error">{error}</p>}
      {evidence && <div data-testid="manual-evidence"><div className="manual-decision" role="status"><strong>NO ACTION · unresolved contradiction</strong><p>{evidence.decision.checked_constraints} cited limits checked · {evidence.pages} pages · operational writes closed</p></div>
        {evidence.decision.flags.map((flag, index) => <div className="manual-conflict" key={index}><strong>{flag.reason.replaceAll("_", " ")}</strong>{flag.citations.map((citation) => <p key={citation.page_sha256}>{citation.document_id} / {citation.revision} / page {citation.page}: <q>{citation.quote}</q></p>)}</div>)}
        <ul className="manual-hits">{evidence.hits.map((hit) => <li key={hit.citation.page_sha256}><div><strong>{hit.citation.document_id} · {hit.citation.revision} · page {hit.citation.page}</strong><span>Lexical cosine {hit.score.toFixed(3)}</span></div><blockquote>{hit.citation.quote}</blockquote><p>Table row {hit.citation.table_row ?? "unmapped"} · <code>{hit.citation.page_sha256}</code></p><button onClick={() => { void download(hit.citation.document_id); }}>Download cited source</button></li>)}</ul>
        <p className="muted">Corpus SHA-256 <code>{evidence.corpus_sha256}</code></p>
      </div>}
    </div>
  </section>;
}
