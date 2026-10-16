import { createHash, createPublicKey, verify } from "node:crypto";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { Ajv2020 } from "ajv/dist/2020.js";
import type { components } from "../../../packages/contracts/generated/api.js";

export type Envelope = components["schemas"]["ExecutionEnvelope"];
export type Receipt = components["schemas"]["MutationReceipt"];
const ajv = new Ajv2020({ strict: true, allErrors: false });
const directory = process.env.AEGIS_CONTRACT_DIR ?? "../../packages/contracts/generated";
function validator(name: string) {
  return ajv.compile(JSON.parse(readFileSync(resolve(directory, `${name}.schema.json`), "utf8")));
}
const validEnvelope = validator("execution-envelope");
const validPlan = validator("proposed-plan");
const validCapability = validator("verified-capability");
const validReceipt = validator("mutation-receipt");
function decode(value: string): Buffer {
  if (!/^[A-Za-z0-9_-]+$/.test(value)) throw new Error("Invalid encoding");
  const data = Buffer.from(value, "base64url");
  if (data.toString("base64url") !== value) throw new Error("Noncanonical encoding");
  return data;
}
export function verifyEnvelope(input: unknown, publicKey: string): Envelope {
  if (!validEnvelope(input)) throw new Error("Envelope schema refused");
  const envelope = input as Envelope;
  const parts = envelope.capability.split(".");
  if (parts.length !== 2) throw new Error("Capability format refused");
  const payload = decode(parts[0]!);
  const signature = decode(parts[1]!);
  const key = createPublicKey({ key: Buffer.from(publicKey, "base64"), format: "der", type: "spki" });
  if (key.asymmetricKeyType !== "ed25519" || signature.length !== 64 || !verify(null, payload, key, signature)) throw new Error("Signature refused");
  const cap: components["schemas"]["VerifiedCapability"] = JSON.parse(payload.toString("utf8"));
  const plan: components["schemas"]["ProposedPlan"] = JSON.parse(envelope.action_json);
  if (!validCapability(cap) || !validPlan(plan)) throw new Error("Typed action/capability refused");
  const now = Math.floor(Date.now() / 1000);
  const hash = createHash("sha256").update(envelope.action_json).digest("hex");
  if (cap.iat > now + 2 || now >= cap.exp || cap.exp > cap.iat + 60 || cap.exp > plan.expires_at || now >= plan.expires_at || hash !== cap.plan_sha256 || cap.action_id !== plan.action_id || cap.resource_id !== plan.resource_id || cap.scope !== plan.scope || cap.expected_database_version !== plan.expected_database_version || cap.expected_state_version !== plan.expected_state_version) throw new Error("Scope, digest, expiry or expected state refused");
  if (plan.controls.pump !== 1 || !plan.controls.loads.every((v) => v === 0) || !plan.controls.valves.every((v) => v === 1)) throw new Error("Independent stop interlock refused");
  if ((plan.action === "simulator.stop_and_record_maintenance") !== !!plan.maintenance) throw new Error("Operational diff must be explicit in the signed action");
  return envelope;
}
export function verifyReceipt(input: unknown, envelope: Envelope): Receipt {
  if (!validReceipt(input)) throw new Error("Receipt schema refused");
  const receipt = input as Receipt;
  const cap = JSON.parse(decode(envelope.capability.split(".")[0]!).toString("utf8")) as components["schemas"]["VerifiedCapability"];
  const plan = JSON.parse(envelope.action_json) as components["schemas"]["ProposedPlan"];
  if (plan.maintenance && (receipt.tool !== "local_mongo_and_simulator" || receipt.receipt_format !== "sandbox-receipt-v2" || !receipt.maintenance_record_sha256)) throw new Error("Operational Mongo receipt missing");
  if (receipt.action_id !== cap.action_id || receipt.plan_sha256 !== cap.plan_sha256 || receipt.nonce !== cap.jti || receipt.database_version_after !== receipt.database_version_before + 1 || receipt.native_version_after !== receipt.native_version_before + 60) throw new Error("Receipt scope refused");
  const omitted = receipt.receipt_format === "sandbox-receipt-v2" ? ["receipt_sha256"] : ["receipt_sha256", "receipt_format", "maintenance_record_sha256", "tool"];
  const content = Object.fromEntries(Object.entries(receipt).filter(([key]) => !omitted.includes(key)).sort(([a], [b]) => a.localeCompare(b)));
  if (createHash("sha256").update(JSON.stringify(content)).digest("hex") !== receipt.receipt_sha256) throw new Error("Receipt integrity refused");
  return receipt;
}
