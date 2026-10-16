import { test } from "node:test";
import assert from "node:assert/strict";
import type { AddressInfo } from "node:net";
import { createExecutor } from "./server.js";
import { createHash, generateKeyPairSync, randomUUID, sign } from "node:crypto";
import { verifyEnvelope } from "./capability.js";

function signedFixture(change: { cap?: Record<string, unknown>; controls?: Record<string, unknown>; plan?: Record<string, unknown> } = {}) {
  const { privateKey, publicKey } = generateKeyPairSync("ed25519");
  const now = Math.floor(Date.now() / 1000);
  const actionId = randomUUID();
  const action = { action_id: actionId, tenant_id: "local", resource_id: "authorization-sandbox-01", action: "simulator.emergency_stop", scope: "isolated_authorization_sandbox", risk: "simulator_only", evidence_policy: "authorization-test-sandbox-v1", expected_database_version: 1, expected_state_version: 30, source_snapshot_sha256: "a".repeat(64), native_binary_sha256: "b".repeat(64), safety_rollout_sha256: "c".repeat(64), before_controls: { pump: 0.85, loads: Array(6).fill(0.7), valves: Array(6).fill(1) }, controls: { pump: 1, loads: Array(6).fill(0), valves: Array(6).fill(1), ...change.controls }, compensation: "retain_committed_state_or_emergency_stop", expires_at: now + 600, ...change.plan };
  const action_json = JSON.stringify(action);
  const cap = { iss: "aegis-local-approver", aud: "aegis-independent-executor", sub: "local-owner", jti: randomUUID(), action_id: actionId, plan_sha256: createHash("sha256").update(action_json).digest("hex"), resource_id: "authorization-sandbox-01", scope: "isolated_authorization_sandbox", expected_database_version: 1, expected_state_version: 30, iat: now, exp: now + 60, user_verification: true, ...change.cap };
  const data = Buffer.from(JSON.stringify(cap));
  return { publicKey: publicKey.export({ format: "der", type: "spki" }).toString("base64"), envelope: { action_json, capability: `${data.toString("base64url")}.${sign(null, data, privateKey).toString("base64url")}` } };
}

test("executor fails closed without a token", () => {
  assert.throws(() => createExecutor(""));
});

test("authenticated and unauthenticated mutations both fail closed", async () => {
  const token = "isolated-test-token-".repeat(3);
  const server = createExecutor(token);
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  const base = `http://127.0.0.1:${(server.address() as AddressInfo).port}`;
  try {
    const health = await fetch(`${base}/healthz`);
    assert.equal(health.status, 200);
    assert.match((await health.json()).detail, /mutations disabled/);
    for (const method of ["POST", "PUT", "DELETE", "PATCH"]) {
      const anonymous = await fetch(`${base}/execute`, { method });
      assert.equal(anonymous.status, 401);
      const authenticated = await fetch(`${base}/execute`, { method, headers: { Authorization: `Bearer ${token}` } });
      assert.equal(authenticated.status, 403);
      assert.equal((await authenticated.json()).code, "MUTATIONS_DISABLED");
    }
  } finally {
    await new Promise<void>((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));
  }
});

test("independent verifier accepts only a fixed signed simulator scope", () => {
  const fixture = signedFixture();
  assert.deepEqual(verifyEnvelope(fixture.envelope, fixture.publicKey), fixture.envelope);
  assert.throws(() => verifyEnvelope({ ...fixture.envelope, action_json: fixture.envelope.action_json + " " }, fixture.publicKey));
  assert.throws(() => verifyEnvelope({ ...fixture.envelope, capability: "unsigned" }, fixture.publicKey));
  assert.throws(() => verifyEnvelope(fixture.envelope, signedFixture().publicKey));
});

for (const cap of [{ sub: "wrong-user" }, { aud: "github" }, { iss: "model" }, { exp: 1 }, { iat: 1 }, { user_verification: false }, { expected_database_version: 99 }, { expected_state_version: 999 }, { plan_sha256: "f".repeat(64) }, { resource_id: "live-edge" }, { extra: true }]) {
  test(`independent verifier refuses signed violation ${JSON.stringify(cap)}`, () => {
    const fixture = signedFixture({ cap });
    assert.throws(() => verifyEnvelope(fixture.envelope, fixture.publicKey));
  });
}

test("a valid issuer signature never overrides the independent actuator interlock", () => {
  for (const controls of [{ pump: 0 }, { loads: Array(6).fill(1) }, { valves: Array(6).fill(0) }]) {
    const fixture = signedFixture({ controls });
    assert.throws(() => verifyEnvelope(fixture.envelope, fixture.publicKey));
  }
});

test("an operational Mongo diff must be explicit, fixed and schema-valid", () => {
  for (const plan of [{ action: "simulator.stop_and_record_maintenance" }, { maintenance: { expected_record_version: 0, status_before: "not_recorded" } }, { action: "simulator.stop_and_record_maintenance", maintenance: { record_id: "unapproved", expected_record_version: 0, status_before: "not_recorded" } }]) {
    const fixture = signedFixture({ plan });
    assert.throws(() => verifyEnvelope(fixture.envelope, fixture.publicKey));
  }
});
