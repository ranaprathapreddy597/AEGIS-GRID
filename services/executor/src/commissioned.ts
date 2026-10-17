// Independent simulator-only policy. Never accepts original sandbox or enterprise scopes.
import { createHash, createPublicKey, verify } from "node:crypto";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { Ajv2020 } from "ajv/dist/2020.js";
import type { components } from "../../../packages/contracts/generated/api.js";
import type { Envelope } from "./capability.js";

type Plan = components["schemas"]["CommissionedPlan"];
type Capability = components["schemas"]["CommissionedCapability"];
type Receipt = components["schemas"]["CommissionedReceipt"];
const directory = process.env.AEGIS_CONTRACT_DIR ?? "../../packages/contracts/generated";
const ajv = new Ajv2020({ strict: true, allErrors: false });
const schema = (name: string) => ajv.compile(JSON.parse(readFileSync(resolve(directory, `${name}.schema.json`), "utf8")));
const validEnvelope = schema("execution-envelope");
const validPlan = schema("commissioned-plan");
const validCapability = schema("commissioned-capability");
const validReceipt = schema("commissioned-receipt");
export const commissionedRules = "a22dbd91274b67c8fd7f099a5f5a36ede6e8382967d5eca6b699e4b7d0fbe4e7";
function decode(value: string): Buffer {
  if (!/^[A-Za-z0-9_-]+$/.test(value)) throw new Error("Commissioned encoding refused");
  const data = Buffer.from(value, "base64url");
  if (data.toString("base64url") !== value) throw new Error("Commissioned canonical encoding refused");
  return data;
}
const hash = (data: string) => createHash("sha256").update(data).digest("hex");
function fields(envelope: Envelope): {plan: Plan; cap: Capability} {
  return { plan: JSON.parse(envelope.action_json) as Plan, cap: JSON.parse(decode(envelope.capability.split(".")[0]!).toString("utf8")) as Capability };
}
export function verifyCommissioned(input: unknown, publicKey: string): Envelope {
  if (!validEnvelope(input)) throw new Error("Commissioned envelope refused");
  const envelope = input as Envelope;
  const parts = envelope.capability.split(".");
  if (parts.length !== 2) throw new Error("Commissioned capability format refused");
  const payload = decode(parts[0]!); const signature = decode(parts[1]!);
  const key = createPublicKey({key: Buffer.from(publicKey, "base64"), format: "der", type: "spki"});
  if (key.asymmetricKeyType !== "ed25519" || signature.length !== 64 || !verify(null, payload, key, signature)) throw new Error("Commissioned signature refused");
  const {plan, cap} = fields(envelope);
  if (!validPlan(plan) || !validCapability(cap)) throw new Error("Commissioned schema refused");
  const now = Math.floor(Date.now() / 1000);
  const mirror = ["action_id", "plant_id", "resource_id", "scope", "incident_id", "rules_revision", "rules_sha256", "expected_database_version", "expected_state_version"] as const;
  if (cap.iat > now + 2 || now >= cap.exp || cap.exp > cap.iat + 60 || cap.exp > plan.expires_at || now >= plan.expires_at || hash(envelope.action_json) !== cap.plan_sha256 || cap.jti !== plan.nonce || mirror.some(k => cap[k] !== plan[k])) throw new Error("Commissioned action/nonce/state binding refused");
  if (plan.rules_sha256 !== commissionedRules || plan.controls.pump !== 1 || plan.controls.loads.length !== 6 || !plan.controls.loads.every(v => v === 0) || plan.controls.valves.length !== 6 || !plan.controls.valves.every(v => v === 1) || plan.duration_s !== 120) throw new Error("Commissioned shared six-cell interlock refused");
  return envelope;
}
export function commissionedReceiptHash(receipt: Receipt): string {
  const hex = (v: number) => { const b = Buffer.alloc(8); b.writeDoubleBE(v); return b.toString("hex"); };
  const content = {...receipt, temperatures_before_c: receipt.temperatures_before_c.map(hex), temperatures_after_c: receipt.temperatures_after_c.map(hex), maximum_temperature_c: hex(receipt.maximum_temperature_c)};
  return hash(JSON.stringify(Object.fromEntries(Object.entries(content).filter(([k]) => k !== "receipt_sha256").sort(([a], [b]) => a.localeCompare(b)))));
}
export function verifyCommissionedReceipt(input: unknown, envelope: Envelope): Receipt {
  if (!validReceipt(input)) throw new Error("Commissioned receipt schema refused");
  const receipt = input as Receipt;
  const {plan, cap} = fields(envelope);
  if (receipt.plant_id !== plan.plant_id || receipt.incident_id !== plan.incident_id || receipt.action_id !== cap.action_id || receipt.nonce !== cap.jti || receipt.plan_sha256 !== cap.plan_sha256 || receipt.rules_sha256 !== commissionedRules || receipt.rules_revision !== plan.rules_revision || receipt.snapshot_sha256_before !== plan.source_snapshot_sha256 || receipt.native_binary_sha256 !== plan.native_binary_sha256 || receipt.database_version_before !== plan.expected_database_version || receipt.database_version_after !== receipt.database_version_before + 1 || receipt.native_version_before !== plan.expected_state_version || receipt.native_version_after !== receipt.native_version_before + 120) throw new Error("Commissioned receipt action/state scope refused");
  if (receipt.maximum_temperature_c >= 70 || receipt.temperatures_after_c.some(v => v >= 70) || Math.max(...receipt.temperatures_after_c) >= Math.max(...receipt.temperatures_before_c) || commissionedReceiptHash(receipt) !== receipt.receipt_sha256) throw new Error("Commissioned recovery measurement/integrity refused");
  return receipt;
}
