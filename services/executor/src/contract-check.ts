import { readFileSync } from "node:fs";
import { Ajv2020 } from "ajv/dist/2020.js";
import type { components } from "../../../packages/contracts/generated/api.js";

type Telemetry = components["schemas"]["PlantTelemetry"];

try {
  const schemaPath = process.argv[2];
  const framePath = process.argv[3];
  if (!schemaPath || !framePath) throw new Error("Missing contract input");
  const schema = JSON.parse(readFileSync(schemaPath, "utf8")) as object;
  const data: unknown = JSON.parse(readFileSync(framePath, "utf8"));
  const validator = new Ajv2020({ strict: true, allErrors: false, coerceTypes: false }).compile<Telemetry>(schema);
  if (!validator(data)) throw new Error("Schema rejected");
  if (data.cells.some((cell, i) => cell.cell_id !== `CELL-0${i + 1}`)) throw new Error("Cell order rejected");
  if (data.ground_truth.cells.some((cell, i) => cell.cell_id !== data.cells[i]?.cell_id)) throw new Error("Truth order rejected");
  if (Math.abs(data.ground_truth.cells.reduce((total, cell) => total + cell.flow_kg_s, 0) - data.ground_truth.total_flow_kg_s) > 1e-6) throw new Error("Flow balance rejected");
  if (data.measurement.sampled_version > data.state_version || Math.abs(data.simulation_time_s - data.measurement.sampled_time_s - data.measurement.age_s) > 1e-6) throw new Error("Measurement age rejected");
  process.stdout.write(JSON.stringify({ result: "PASS", schema_version: data.schema_version, model_version: data.model_version }) + "\n");
} catch {
  // Validation diagnostics never echo input data, credentials or untrusted fields.
  process.stdout.write('{"result":"FAIL","reason":"contract_or_semantics"}\n');
  process.exitCode = 1;
}
