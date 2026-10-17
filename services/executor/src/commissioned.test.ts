// Unit signatures only; these are not live provider or human approval evidence.
import { generateKeyPairSync, sign, createHash } from "node:crypto";
import { test } from "node:test";
import assert from "node:assert/strict";
import { commissionedRules, commissionedReceiptHash, verifyCommissioned, verifyCommissionedReceipt } from "./commissioned.js";
import { verifyEnvelope } from "./capability.js";
import type { components } from "../../../packages/contracts/generated/api.js";
const { privateKey, publicKey } = generateKeyPairSync("ed25519");
const key = publicKey.export({format: "der", type: "spki"}).toString("base64");
const uuid = "00000000-0000-0000-0000-000000000001";
const hash = (v: string) => createHash("sha256").update(v).digest("hex");
function fixture() {
  const now = Math.floor(Date.now() / 1000);
  const plan: components["schemas"]["CommissionedPlan"] = {action_id: uuid, tenant_id: "local", plant_id: "commissioned-simulator-01", resource_id: "commissioned-simulator-01", scope: "commissioned_six_cell_incident", action: "simulator.commissioned_stop", rules_revision: "commissioned-stop-v1", rules_sha256: commissionedRules, incident_id: "a".repeat(64), investigation_id: uuid, investigation_sha256: "b".repeat(64), nonce: uuid, expected_database_version: 1, expected_state_version: 30, source_snapshot_sha256: "c".repeat(64), native_binary_sha256: "d".repeat(64), safety_rollout_sha256: "e".repeat(64), controls: {pump: 1, loads: Array(6).fill(0), valves: Array(6).fill(1)}, duration_s: 120, expires_at: now + 600};
  const cap: components["schemas"]["CommissionedCapability"] = {iss: "aegis-commissioned-approver", aud: "aegis-commissioned-executor", sub: "local-owner", jti: uuid, action_id: uuid, plan_sha256: hash(JSON.stringify(plan)), plant_id: plan.plant_id, resource_id: plan.resource_id, scope: plan.scope, incident_id: plan.incident_id, rules_revision: plan.rules_revision, rules_sha256: plan.rules_sha256, expected_database_version: 1, expected_state_version: 30, iat: now, exp: now + 60, user_verification: true};
  return {plan, cap};
}
function envelope(plan: unknown, cap: unknown) {
  const payload = Buffer.from(JSON.stringify(cap));
  return {action_json: JSON.stringify(plan), capability: `${payload.toString("base64url")}.${sign(null, payload, privateKey).toString("base64url")}`};
}
test("commissioned signature policy accepts exact unit scope and original scope rejects it", () => {
  const {plan, cap} = fixture(); const env = envelope(plan, cap);
  assert.deepEqual(verifyCommissioned(env, key), env);
  assert.throws(() => verifyEnvelope(env, key));
});
for (const attack of ["plant", "scope", "action", "rules", "nonce", "incident", "state", "expiry", "future", "lifetime", "signature", ...Array.from({length: 6}, (_, i) => `cell-${i}`)]) {
  test(`commissioned independent policy rejects ${attack}`, () => {
    const {plan, cap} = fixture();
    if (attack === "plant") Object.assign(plan, {plant_id: "authorization-sandbox-01"});
    if (attack === "scope") Object.assign(plan, {scope: "isolated_authorization_sandbox"});
    if (attack === "action") Object.assign(plan, {action: "enterprise.write"});
    if (attack === "rules") { plan.rules_sha256 = "f".repeat(64); cap.rules_sha256 = plan.rules_sha256; }
    if (attack === "nonce") cap.jti = "00000000-0000-0000-0000-000000000002";
    if (attack === "incident") cap.incident_id = "f".repeat(64);
    if (attack === "state") cap.expected_state_version++;
    if (attack === "expiry") cap.exp = cap.iat - 1;
    if (attack === "future") cap.iat += 60;
    if (attack === "lifetime") cap.exp = cap.iat + 100;
    if (attack.startsWith("cell-")) plan.controls.loads[Number(attack.slice(5))] = 0.1;
    cap.plan_sha256 = hash(JSON.stringify(plan)); const env = envelope(plan, cap);
    if (attack === "signature") env.capability = env.capability.split(".")[0]! + "." + Buffer.alloc(64).toString("base64url");
    assert.throws(() => verifyCommissioned(env, key));
  });
}
test("commissioned receipt binds state, all six measurements and exact action", () => {
  const {plan, cap} = fixture(); const env = envelope(plan, cap);
  const r: components["schemas"]["CommissionedReceipt"] = {receipt_format: "commissioned-receipt-v1", plant_id: plan.plant_id, incident_id: plan.incident_id, action_id: uuid, nonce: uuid, plan_sha256: cap.plan_sha256, rules_sha256: commissionedRules, rules_revision: plan.rules_revision, previous_receipt_sha256: "0".repeat(64), receipt_sha256: "0".repeat(64), database_version_before: 1, database_version_after: 2, native_version_before: 30, native_version_after: 150, snapshot_sha256_before: plan.source_snapshot_sha256, snapshot_sha256_after: "f".repeat(64), native_binary_sha256: plan.native_binary_sha256, temperatures_before_c: Array(6).fill(40), temperatures_after_c: Array(6).fill(35), maximum_temperature_c: 40, duration_s: 120, fault_retained: true, physical_io: false, outcome: "simulated_safe_stop_cooldown", authorization: "WebAuthn_user_verified"};
  r.receipt_sha256 = commissionedReceiptHash(r);
  assert.deepEqual(verifyCommissionedReceipt(r, env), r);
  for (const changed of [{...r, incident_id: "f".repeat(64)}, {...r, native_version_after: 151}, {...r, temperatures_after_c: [35,35,35,35,35,71]}, {...r, snapshot_sha256_before: "f".repeat(64)}]) assert.throws(() => verifyCommissionedReceipt(changed, env));
});
