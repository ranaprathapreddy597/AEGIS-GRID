import { test } from "node:test";
import assert from "node:assert/strict";
import type { AddressInfo } from "node:net";
import { createExecutor } from "./server.js";

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
