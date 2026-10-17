import type { Telemetry } from "./stream";

/** Rendering uses delivered observations only; truth stays behind the inspection toggle. */
export function CellSignal({ history, index, color, live, showTruth }: { history: Telemetry[]; index: number; color: string; live: boolean; showTruth: boolean }) {
  const latest = history.at(-1);
  const cell = latest?.cells[index];
  const readings = history.map(frame => frame.cells[index]?.temperature_c).filter((value): value is number => value !== undefined);
  const low = Math.min(24, ...readings) - 1;
  const high = Math.max(low + 5, ...readings) + 1;
  const evidence = latest?.sentinel.evidence.filter(item => item.cell_id === cell?.cell_id) ?? [];
  const state = !live ? "Signal stale" : latest?.sentinel.latched ? "Shield latched" : evidence.length ? "Anomaly evidence" : (cell?.load_fraction ?? 0) === 0 ? "Idle" : "Operating";
  return <article className={`cell signal-cell ${evidence.length ? "has-anomaly" : ""}`} style={{ borderTopColor: color }} aria-label={`${cell?.cell_id ?? `CELL-0${index + 1}`} observed simulator measurements`}>
    <div className="cell-name"><span>{cell?.cell_id ?? `CELL-0${index + 1}`}</span><span className={`status-dot ${live ? "live" : ""}`}/></div>
    <div className="temperature" data-testid={`temperature-${index}`}>{cell?.temperature_c.toFixed(3) ?? "—"}<small>°C</small></div>
    <svg className="cell-sparkline" viewBox="0 0 180 35" role="img" aria-label={`Observed temperature trend for cell ${index + 1}`}><polyline points={readings.map((value, x) => `${x / Math.max(1, readings.length - 1) * 180},${32 - (value - low) / (high - low) * 29}`).join(" ")} fill="none" stroke={color} strokeWidth="2"/></svg>
    <span className="cell-equipment">{state}</span>
    <div className="load-track"><div style={{ width: `${(cell?.load_fraction ?? 0) * 100}%`, background: color }}/></div>
    <div className="cell-detail"><span>Load {cell ? Math.round(cell.load_fraction * 100) : "—"}%</span><span>{cell?.heat_input_w.toFixed(0) ?? "—"} W</span></div>
    <dl className="cell-instruments"><div><dt>Observed flow</dt><dd>{cell?.flow_kg_s.toFixed(3) ?? "—"} kg/s</dd></div><div><dt>Loop pressure</dt><dd>{latest?.loop_pressure_kpa.toFixed(1) ?? "—"} kPa</dd></div></dl>
    <p className="cell-limit">Synthetic guard 65 °C / hard limit 70 °C</p>
    {evidence.length > 0 && <p className="cell-warning">{evidence.map(item => item.reason.replaceAll("_", " ")).join(" · ")}</p>}
    {showTruth && latest && <div className="truth-detail" data-testid={`truth-${index}`}><span>Truth {latest.ground_truth.cells[index]?.temperature_c.toFixed(2)} °C</span><span>Flow {latest.ground_truth.cells[index]?.flow_kg_s.toFixed(3)} kg/s</span></div>}
  </article>;
}
