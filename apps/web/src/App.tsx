import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { IntelligencePanel } from "./IntelligencePanel";
import { CellSignal } from "./CellSignal";
import { LaboratoryPanel } from "./LaboratoryPanel";
import { InferencePanel } from "./InferencePanel";
import { InvestigationPanel } from "./InvestigationPanel";
import { RecoveryPanel } from "./RecoveryPanel";
import { ApprovalPanel } from "./ApprovalPanel";
import { CommissionedPanel } from "./CommissionedPanel";
import { IntegrationPanel } from "./IntegrationPanel";
import { ManualEvidencePanel } from "./ManualEvidencePanel";
import { streamTelemetry } from "./stream";
import type { Capabilities, EdgeStatus, IncidentPage, IncidentReplay, StorageStatus, Telemetry } from "./stream";

const colors = ["#77dfc4", "#85aef4", "#bda3ed", "#f4c780", "#f29898", "#a6d5e3"];

export function App() {
  const [token, setToken] = useState("");
  const [input, setInput] = useState("");
  const [authError, setAuthError] = useState("");
  const [loading, setLoading] = useState(false);
  const [capabilities, setCapabilities] = useState<Capabilities | null>(null);
  const [history, setHistory] = useState<Telemetry[]>([]);
  const [status, setStatus] = useState("Waiting for local access");
  const [tab, setTab] = useState<"overview" | "log">("overview");
  const [showTruth, setShowTruth] = useState(false);
  const [edgeStatus, setEdgeStatus] = useState<EdgeStatus | null>(null);
  const [incidents, setIncidents] = useState<IncidentPage | null>(null);
  const [storageStatus, setStorageStatus] = useState<StorageStatus | null>(null);
  const [replay, setReplay] = useState<IncidentReplay | null>(null);
  const [journalError, setJournalError] = useState("");
  const lastFrame = useRef(0);
  const latest = history.at(-1);
  const live = status === "Live telemetry";
  const plotted = history.flatMap((frame) => [...frame.cells.map((cell) => cell.temperature_c), ...(showTruth ? frame.ground_truth.cells.map((cell) => cell.temperature_c) : [])]);
  const chartMin = Math.floor(Math.min(24, ...plotted) / 10) * 10;
  const chartMax = Math.ceil(Math.max(75, ...plotted) / 10) * 10;
  const chartY = (value: number) => 205 - (value - chartMin) / (chartMax - chartMin) * 180;
  const ticks = Array.from({ length: 4 }, (_, i) => chartMin + i * (chartMax - chartMin) / 3);

  async function connect(event: FormEvent) {
    event.preventDefault(); setAuthError(""); setLoading(true);
    try {
      const response = await fetch("/api/v1/capabilities", { headers: { Authorization: `Bearer ${input}` } });
      if (!response.ok) throw new Error(response.status === 401 ? "Access token rejected." : `Local API unavailable (${response.status}).`);
      setCapabilities(await response.json() as Capabilities);
      setToken(input); setInput("");
    } catch (error) { setAuthError(error instanceof Error ? error.message : "Unable to connect"); }
    finally { setLoading(false); }
  }

  useEffect(() => {
    if (!token) return;
    const controller = new AbortController();
    let retry: ReturnType<typeof setTimeout> | undefined;
    let attempts = 0;
    const run = async () => {
      setStatus("Connecting to edge…");
      try {
        await streamTelemetry(token, controller.signal, (frame) => {
          lastFrame.current = Date.now(); attempts = 0;
          setHistory((previous) => {
            const sameRun = previous.at(-1)?.run_id === frame.run_id;
            return [...(sameRun ? previous.slice(-119) : []), frame];
          });
          setStatus("Live telemetry");
        }, setStatus);
      } catch (error) {
        if (!controller.signal.aborted) {
          setStatus(error instanceof Error ? error.message : "Connection lost");
          retry = setTimeout(() => { void run(); }, Math.min(1000 * 2 ** attempts++, 10000));
        }
      }
    };
    void run();
    const staleCheck = setInterval(() => {
      if (lastFrame.current && Date.now() - lastFrame.current > 3500) setStatus("Signal stale · last received values shown");
    }, 1000);
    return () => { controller.abort(); clearTimeout(retry); clearInterval(staleCheck); };
  }, [token]);

  useEffect(() => {
    if (!token) return;
    const controller = new AbortController();
    const readStatus = async () => {
      try {
        const response = await fetch("/api/v1/edge/status", { headers: { Authorization: `Bearer ${token}` }, signal: controller.signal });
        if (response.ok) setEdgeStatus(await response.json() as EdgeStatus);
        const journal = await fetch("/api/v1/incidents", { headers: { Authorization: `Bearer ${token}` }, signal: controller.signal });
        if (journal.ok) { setIncidents(await journal.json() as IncidentPage); setJournalError(""); }
        else setJournalError(`Incident journal unavailable (${journal.status}).`);
        const storage = await fetch("/api/v1/storage/status", { headers: { Authorization: `Bearer ${token}` }, signal: controller.signal });
        if (storage.ok) setStorageStatus(await storage.json() as StorageStatus);
      } catch { /* The telemetry status separately reports edge availability. */ }
    };
    void readStatus();
    const timer = setInterval(() => { void readStatus(); }, 5000);
    return () => { controller.abort(); clearInterval(timer); };
  }, [token]);

  function disconnect() { setEdgeStatus(null); setIncidents(null); setStorageStatus(null); setReplay(null); setJournalError(""); setToken(""); setHistory([]); setCapabilities(null); setStatus("Disconnected"); lastFrame.current = 0; }
  function download() {
    if (!latest) return;
    const url = URL.createObjectURL(new Blob([JSON.stringify(latest, null, 2)], { type: "application/json" }));
    const anchor = document.createElement("a"); anchor.href = url; anchor.download = `aegis-frame-${latest.state_version}.json`; anchor.click(); URL.revokeObjectURL(url);
  }

  async function loadReplay(incidentId: string) {
    try {
      const response = await fetch(`/api/v1/incidents/${encodeURIComponent(incidentId)}/replay`, { headers: { Authorization: `Bearer ${token}` } });
      if (!response.ok) throw new Error(`Replay unavailable (${response.status}).`);
      setReplay(await response.json() as IncidentReplay); setJournalError("");
    } catch (error) { setJournalError(error instanceof Error ? error.message : "Replay unavailable."); }
  }
  function downloadReplay() {
    if (!replay) return;
    const url = URL.createObjectURL(new Blob([JSON.stringify(replay, null, 2)], { type: "application/json" }));
    const anchor = document.createElement("a"); anchor.href = url; anchor.download = `aegis-incident-${replay.incident.incident_id.slice(0, 12)}.json`; anchor.click(); URL.revokeObjectURL(url);
  }

  return <div className="app-shell">
    <a className="skip-link" href="#main">Skip to main content</a>
    <aside className="rail"><a className="brand-icon" href="#main" aria-label="AEGIS GRID home">A<span>Ⅱ</span></a><span className="rail-label">AEGIS / SYSTEMS</span><span className="rail-bottom">01</span></aside>
    <div className="workspace">
      <header className="topbar"><a className="wordmark" href="#main">AEGIS<span>//</span>GRID <small>2.0</small></a><div className="topbar-right"><span className="environment">LOCAL SIMULATION</span><span className="phase">COMMAND CENTER</span></div></header>
      <main id="main">
        <div className="page-heading"><div><div className="eyebrow"><span className="tiny-square"/> INDUSTRIAL OBSERVABILITY / EDGE 01</div><h1>Factory signal room<span>.</span></h1><p>A live view into the local thermal twin. Every reading starts in C++.</p></div><div className="connection"><span className={`status-dot ${live ? "live" : ""}`}/><span role="status" data-testid="connection-status">{status}</span></div></div>
        <div className="disclosure"><span>SIMULATED PLANT</span><p>Six cells · shared coolant loop · electrical feeder. Synthetic physics and sensor faults; ground truth is available for simulator inspection.</p><span className="lock-label">INCIDENT WRITES CLOSED</span></div>
        {!token ? <section className="access-panel" aria-labelledby="access-heading"><div className="access-copy"><div className="eyebrow">ESTABLISH LOCAL SESSION</div><h2 id="access-heading">Connect to your factory twin.</h2><p>The simulator runs locally. Use the viewer token generated during startup to open the authenticated telemetry stream.</p><div className="terminal-hint"><span>YOUR TERMINAL</span><code>python tools/dev.py token</code></div><p className="muted">Access stays in memory and is cleared on disconnect or reload.</p></div><form onSubmit={(event) => { void connect(event); }}><label htmlFor="token">Local viewer token</label><input id="token" type="password" value={input} onChange={(event) => setInput(event.target.value)} required autoComplete="off" placeholder="Paste your local access token"/><button className="primary" disabled={loading || !input}>{loading ? "Connecting…" : "Connect to live stream"}<span>↗</span></button>{authError && <p role="alert" className="error">{authError}</p>}<p className="form-note">No cloud connection or external account required.</p></form></section> : <>
          <div className="metric-row"><Metric label="INSTRUMENTED CELLS" value={latest ? "06 / 06" : "—"} note="Shared coolant + ring heat transfer"/><Metric label="SIMULATION CLOCK" value={latest ? `${latest.simulation_time_s.toFixed(1)} s` : "—"} note={`Fixed step · 0.5 s · seed ${latest?.seed ?? "—"}`}/><Metric label="CURRENT FRAME" value={latest ? `#${latest.state_version.toString().padStart(5, "0")}` : "—"} note="Versioned at source"/><Metric label="COOLANT RESERVOIR" value={latest ? `${latest.coolant_temperature_c.toFixed(1)} °C` : "—"} note="Finite 20 kg reservoir"/></div>
          {latest && <section className="plant-strip" aria-label="Shared resource simulation ground truth"><div><span>LOOP PRESSURE</span><strong>{latest.ground_truth.pressure_kpa.toFixed(1)} kPa</strong></div><div><span>TOTAL FLOW</span><strong>{latest.ground_truth.total_flow_kg_s.toFixed(3)} kg/s</strong></div><div><span>ELECTRICAL FEEDER</span><strong>{(latest.ground_truth.feeder_power_w / 1000).toFixed(2)} / 14.5 kW</strong></div><div><span>SCENARIO / INJECTED MASK</span><strong>{latest.scenario_id} / {latest.injected_fault_mask}</strong></div><div><span>SENSOR AGE / DROPPED</span><strong>{latest.measurement.age_s.toFixed(1)} s / {latest.measurement.dropped_packets}</strong></div></section>}
          {latest && <section className={`sentinel-panel ${latest.sentinel.latched ? "triggered" : ""}`} aria-label="Independent edge sentinel"><div><span className="eyebrow">SENSOR-ONLY EDGE SENTINEL</span><h2 data-testid="sentinel-state">{latest.sentinel.state.replaceAll("_", " ")}</h2><p data-testid="safety-policy">{latest.sentinel.applied_policy.replaceAll("_", " ")} · {latest.sentinel.policy_revision}</p></div><div><strong>{latest.sentinel.latency_ms.toFixed(3)} ms</strong><span>last detector + FAISS step</span><strong>{latest.sentinel.memory_entries} / 256</strong><span>bounded local FAISS memory</span></div><div><strong data-testid="cloud-state">Cloud {edgeStatus?.cloud ?? "unavailable"}</strong><span>{edgeStatus?.queued_events ?? "—"} queued · {edgeStatus?.dropped_events ?? "—"} evicted</span><strong>CPU fallback active</strong><span>NPU workload unverified</span></div>{latest.sentinel.evidence.length > 0 && <ul>{latest.sentinel.evidence.slice(0, 3).map((item) => <li key={`${item.cell_id}-${item.reason}`}>{item.cell_id} · {item.reason.replaceAll("_", " ")} · residual {item.residual_c.toFixed(2)} °C</li>)}</ul>}</section>}
          <nav className="workflow-nav" aria-label="Command center workflow">{[["live-twin", "01", "Live twin"], ["fault-lab", "02", "Fault laboratory"], ["forensics", "03", "Investigate"], ["recovery", "04", "Red / Blue"], ["authorization", "05", "Ask first"], ["connectors", "06", "Receipts"]].map(([id, number, title]) => <a href={`#${id}`} key={id}><span>{number}</span>{title}</a>)}</nav>
          <section className="authority-legend" aria-label="Data and authority boundaries"><div><span className="boundary-tag observed">MEASURED</span><p>Delivered simulator sensors · may contain faults</p></div><div><span className="boundary-tag predicted">PREDICTED</span><p>Private native futures · synthetic assumptions</p></div><div><span className="boundary-tag approved">APPROVED ACTION</span><p>Only verified executor receipts prove a write</p></div></section>
          <div id="live-twin" className="section-anchor"/>
          <div className="section-toolbar"><div className="tabs" role="tablist" aria-label="Telemetry view"><button role="tab" aria-selected={tab === "overview"} onClick={() => setTab("overview")}>Live overview</button><button role="tab" aria-selected={tab === "log"} onClick={() => setTab("log")}>Signal log <span>{history.length}</span></button></div><div className="actions"><button aria-pressed={showTruth} onClick={() => setShowTruth(!showTruth)}>Simulation ground truth</button><button onClick={download} disabled={!latest}>Export frame ↓</button><button onClick={disconnect}>Disconnect</button></div></div>
          {tab === "overview" ? <div className="dashboard-grid"><section className="panel topology"><PanelTitle number="01" title="Shared-loop cell topology" detail="C++20 / SYNTHETIC"/><div className="coolant-line"><span>SHARED COOLANT</span><div/><strong>{latest?.coolant_temperature_c.toFixed(1) ?? "—"} °C</strong></div><svg className="loop-schematic" viewBox="0 0 620 105" role="img" aria-label="Shared hydraulic topology: pump feeds six parallel cell branches and a common coolant return"><path d="M40 35H580V85H40Z" fill="none" stroke="#37675d" strokeWidth="2"/>{colors.map((color, index) => <g key={color}><path d={`M${105+index*80} 35V85`} stroke={color} strokeWidth="2"/><circle cx={105+index*80} cy="60" r="11" fill="#14242b" stroke={color}/><text x={105+index*80} y="20" textAnchor="middle">C0{index+1}</text></g>)}<circle cx="40" cy="60" r="15" fill="#14242b" stroke="#77dfc4"/><path d="M35 53L47 60L35 67Z" fill="#77dfc4"/><text x="25" y="103">PUMP</text></svg><div className="cell-grid">{colors.map((color, index) => <CellSignal key={color} history={history} index={index} color={color} live={live} showTruth={showTruth}/>)}</div><div className="panel-foot"><span className="status-dot live"/> Direct simulator output <span>NO PHYSICAL I/O</span></div></section>
            <section className="panel trace"><PanelTitle number="02" title="Temperature traces" detail={showTruth ? "SOLID: OBSERVED / DASHED: TRUTH" : "LAST 120 RECEIVED FRAMES"}/><div className="chart"><svg viewBox="0 0 560 225" role="img" aria-label="Live temperature history for six cells in degrees Celsius">{ticks.map((temperature) => <g key={temperature}><line x1="38" x2="548" y1={chartY(temperature)} y2={chartY(temperature)} stroke="#273139" strokeDasharray="3 5"/><text x="4" y={chartY(temperature) + 4} fill="#8d9ba4" fontSize="11">{temperature.toFixed(0)}°</text></g>)}<line x1="38" x2="548" y1={chartY(70)} y2={chartY(70)} stroke="#df9d83" strokeDasharray="5 4"/><text x="390" y={chartY(70) - 6} fill="#edb39c" fontSize="10">70 °C synthetic hard limit</text>{colors.map((color, index) => <polyline key={color} points={history.map((frame, x) => `${38 + x / 119 * 510},${chartY(frame.cells[index]?.temperature_c ?? 24)}`).join(" ")} fill="none" stroke={color} strokeWidth="2"/>)}{showTruth && colors.map((color, index) => <polyline key={`truth-${color}`} points={history.map((frame, x) => `${38 + x / 119 * 510},${chartY(frame.ground_truth.cells[index]?.temperature_c ?? 24)}`).join(" ")} fill="none" stroke={color} strokeWidth="2" strokeDasharray="5 4"/>)}</svg></div><div className="legend">{colors.map((color, i) => <span key={color}><i style={{ background: color }}/> C0{i + 1}</span>)}</div><div className="panel-foot">{showTruth ? "Truth is simulator-only; unavailable to real sensors" : "Sensor noise bound ±0.1 °C; excludes spoof bias"}<span>°C</span></div></section></div> : <section className="panel log-panel"><PanelTitle number="02" title="Received signal frames" detail="BOUNDED TO 120 FRAMES"/><div className="table-scroll"><table><thead><tr><th>Frame</th><th>Simulation time</th><th>Cell 01</th><th>Received (UTC)</th><th>Source</th></tr></thead><tbody>{history.slice().reverse().map((frame) => <tr key={`${frame.run_id}-${frame.state_version}`}><td>#{frame.state_version}</td><td>{frame.simulation_time_s.toFixed(1)} s</td><td>{frame.cells[0]?.temperature_c.toFixed(3)} °C</td><td>{frame.observed_at.slice(11, 23)}</td><td>C++ simulator</td></tr>)}</tbody></table></div></section>}
          <IntelligencePanel token={token} history={history} live={live}/>
          <div id="fault-lab" className="section-anchor"><LaboratoryPanel token={token}/></div>
          <div className="workflow-heading" id="forensics"><span>03 / FORENSIC WORKSPACE</span><h2>Evidence before intervention.</h2><p>The recorded incident feeds numerical agents, cited manuals and independent native rollouts.</p></div>
          <InvestigationPanel token={token} incidentId={replay?.incident.incident_id ?? incidents?.items[0]?.incident_id}/>
          <ManualEvidencePanel token={token}/>
          <div id="recovery" className="section-anchor"><RecoveryPanel token={token} incidentId={replay?.incident.incident_id ?? incidents?.items[0]?.incident_id}/></div>
          <div id="authorization" className="section-anchor"><ApprovalPanel/></div>
          <CommissionedPanel token={token}/>
          <div id="connectors" className="section-anchor"><IntegrationPanel token={token}/></div>
          <InferencePanel token={token}/>
          <section className="panel pathway"><PanelTitle number="03" title="Signal provenance" detail="LOCAL GOLDEN PATH"/><div className="path-nodes">{["C++ thermal twin", "Python edge", "FastAPI stream", "React control room"].map((name, i) => <div className="path-node" key={name}><span>0{i + 1}</span><strong>{name}</strong><small>{["Deterministic · seed-controlled", "Strict schema validation", "Authenticated · SSE", "Actual streamed values"][i]}</small></div>)}</div><div className="fingerprint">BINARY SHA-256 <code>{latest?.simulator_sha256 ?? "Awaiting first frame"}</code></div><div className="fingerprint">SCENARIO SHA-256 <code>{latest?.scenario_sha256 ?? "Awaiting first frame"}</code></div></section>
          <section className="panel journal" aria-label="Persistent incident journal"><PanelTitle number="04" title="Persistent incident journal" detail={`MONGO ${storageStatus?.mongo ?? "unavailable"} / REDIS ${storageStatus?.redis ?? "unavailable"}`}/>{journalError && <p role="alert" className="error">{journalError}</p>}<div className="incident-rows incident-timeline">{incidents?.items.length === 0 && <p>No recorded incidents yet. Detection events will persist here.</p>}{incidents?.items.slice(0, 8).map((item) => <article key={item.incident_id} data-testid={`incident-${item.incident_id}`}><div><strong>{item.event.kind} · frame {item.event.state_version}</strong><p>{item.ingested_at} · {item.event.snapshot ? "Native snapshot available" : "Evidence only"}</p><code>{item.incident_id.slice(0, 20)}</code></div><button onClick={() => { void loadReplay(item.incident_id); }}>Replay incident</button></article>)}</div>{replay && <div className="replay-detail" data-testid="incident-replay"><h3>Recorded incident replay</h3><p>{replay.events.length} immutable events · {replay.snapshot_available ? "Native state captured before local policy" : "No native snapshot"}</p><code>{replay.reproducibility_sha256}</code><button onClick={downloadReplay}>Download replay</button></div>}</section>
          <section className="integration-grid" aria-label="Capability status">{capabilities?.capabilities.filter((item) => ["blocked", "not_implemented"].includes(item.status)).map((item) => <article key={item.name}><div><span className="capability-state">{item.status.replaceAll("_", " ")}</span><h3>{item.name}</h3></div><p>{item.detail}</p></article>)}</section>
        </>}
      </main><footer><span>AEGIS//GRID <b>LOCAL DEVELOPMENT</b></span><span>Local validation · required live acceptance gates BLOCKED.</span></footer>
    </div>
  </div>;
}
function Metric({ label, value, note }: { label: string; value: string; note: string }) { return <article className="metric"><span>{label}</span><strong>{value}</strong><p>{note}</p></article>; }
function PanelTitle({ number, title, detail }: { number: string; title: string; detail: string }) { return <div className="panel-title"><h2><span>{number}</span>{title}</h2><small>{detail}</small></div>; }
