import { readFileSync, writeFileSync, existsSync, mkdirSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const env = Object.fromEntries(readFileSync(".env", "utf8").split(/\r?\n/).filter((line) => line && !line.startsWith("#")).map((line) => line.split("=")));
const origin = `http://localhost:${env.AEGIS_WEB_PORT ?? "8080"}`;

test("real WebAuthn virtual authenticator binds approval and independent execution", async ({ page, context }) => {
  test.setTimeout(90000);
  page.on("requestfailed", (request) => { console.log("Browser transport refusal:", request.method(), new URL(request.url()).pathname, request.failure()?.errorText); });
  const cdp = await context.newCDPSession(page);
  await cdp.send("WebAuthn.enable");
  const { authenticatorId } = await cdp.send("WebAuthn.addVirtualAuthenticator", { options: { protocol: "ctap2", transport: "internal", hasResidentKey: true, hasUserVerification: true, isUserVerified: true, automaticPresenceSimulation: true } });
  // This ignored local file contains ONLY a generated CI virtual-authenticator key.
  // It avoids registering eight throwaway keys across repeated checks. Never log it.
  const fixturePath = ".run/webauthn-ci.json";
  let reused = existsSync(fixturePath);
  if (reused) {
    const credential = JSON.parse(readFileSync(fixturePath, "utf8"));
    credential.signCount += 100;
    await cdp.send("WebAuthn.addCredential", { authenticatorId, credential });
  }
  try {
    const client = context.request;
    const headers = { Origin: origin };
    expect((await client.post(`${origin}/api/v1/approval/proposals`, { headers })).status()).toBe(401);
    expect((await client.post(`${origin}/api/v1/approval/session`, { headers: { ...headers, Authorization: `Bearer ${env.AEGIS_VIEWER_TOKEN}` } })).status()).toBe(401);
    expect((await client.post(`${origin}/api/v1/approval/session`, { headers: { Origin: "http://untrusted.invalid", Authorization: `Bearer ${env.AEGIS_APPROVER_TOKEN}` } })).status()).toBe(403);
    expect((await client.post(`${origin}/internal/v1/sandbox/execute`, { data: {} })).status()).toBe(404);
    await page.goto(origin);
    await page.getByLabel("Local viewer token").fill(env.AEGIS_VIEWER_TOKEN!);
    await page.getByRole("button", { name: "Connect to live stream" }).click();
    await page.getByLabel("Local approval owner token").fill(env.AEGIS_APPROVER_TOKEN!);
    await page.getByRole("button", { name: "Start approval session" }).click();
    await expect(page.getByTestId("approval-session")).toContainText("Owner session");
    const cookie = (await context.cookies(`${origin}/api/v1/approval/session`)).find((item) => item.name === "aegis_owner");
    expect(cookie?.httpOnly).toBe(true);
    expect(cookie?.sameSite).toBe("Strict");
    const sessionInfo = await (await client.get(`${origin}/api/v1/approval/session`)).json();
    if (!sessionInfo.enrolled_credentials && reused) {
      await cdp.send("WebAuthn.clearCredentials", { authenticatorId });
      reused = false;
    }
    if (!reused) {
      await page.getByRole("button", { name: "Enroll passkey" }).click();
      await expect(page.locator(".approval-panel").getByRole("status")).toContainText("Passkey enrolled");
    }
    await page.getByRole("button", { name: "Prepare sandbox stop" }).click();
    await expect(page.getByTestId("approval-proposal")).toContainText("waiting for passkey");
    const proposed = await client.get(`${origin}/api/v1/approval/session`);
    expect(proposed.status()).toBe(200);
    // Read the exact displayed digest/id, not a capability or private key.
    const text = await page.getByTestId("approval-proposal").innerText();
    const digest = text.match(/Reviewed digest ([0-9a-f]{64})/)![1]!;
    await page.getByText("Inspect exact immutable action and safety artifact", { exact: true }).click();
    const plan = JSON.parse(await page.locator(".approval-panel pre").innerText());
    const path = `${origin}/api/v1/approval/proposals/${plan.action_id}`;
    expect((await client.post(`${path}/execute`, { headers, data: { plan_sha256: digest } })).status()).toBe(403);
    const assertionRequest = page.waitForRequest((request) => request.url() === `${path}/verify`);
    await page.getByRole("button", { name: "Approve exact action with passkey" }).click();
    const assertion = (await assertionRequest).postDataJSON();
    await expect(page.getByTestId("approval-proposal").getByRole("heading", { name: "approved", exact: true })).toBeVisible();
    expect((await client.post(`${path}/verify`, { headers, data: assertion })).status()).toBe(403);
    expect((await client.post(`${path}/execute`, { headers, data: { plan_sha256: "f".repeat(64) } })).status()).toBe(403);
    expect((await client.post(`${path}/execute`, { headers, data: { plan_sha256: digest, action_json: "modified" } })).status()).toBe(422);

    // Approve a second proposal against the SAME initial state; it must become stale.
    const second = await (await client.post(`${origin}/api/v1/approval/proposals`, { headers })).json();
    const secondPath = `${origin}/api/v1/approval/proposals/${second.action_id}`;
    const challenge = await (await client.post(`${secondPath}/options`, { headers })).json();
    const credential = await page.evaluate(async (options) => {
      const api = PublicKeyCredential as typeof PublicKeyCredential & { parseRequestOptionsFromJSON: (value: unknown) => PublicKeyCredentialRequestOptions };
      const value = await navigator.credentials.get({ publicKey: api.parseRequestOptionsFromJSON(options) }) as PublicKeyCredential;
      const response = value.response as AuthenticatorAssertionResponse;
      const encode = (bytes: ArrayBuffer) => btoa(String.fromCharCode(...new Uint8Array(bytes))).replaceAll("+", "-").replaceAll("/", "_").replaceAll("=", "");
      return { id: value.id, rawId: encode(value.rawId), type: value.type, response: { authenticatorData: encode(response.authenticatorData), clientDataJSON: encode(response.clientDataJSON), signature: encode(response.signature), userHandle: response.userHandle ? encode(response.userHandle) : null }, clientExtensionResults: {} };
    }, challenge.options);
    expect((await client.post(`${secondPath}/verify`, { headers, data: { ceremony_id: challenge.ceremony_id, credential } })).status()).toBe(200);
    execFileSync("docker", ["compose", "--env-file", ".env", "-f", "infra/local/compose.yaml", "restart", "api"], { stdio: "pipe", timeout: 20000 });
    await expect.poll(async () => {
      try { return (await client.get(path)).status(); } catch { return 0; }
    }, { timeout: 20000, intervals: [1000] }).toBe(200);
    await page.getByRole("button", { name: "Execute approved sandbox stop" }).click();
    await expect(page.getByTestId("approval-receipt")).toContainText("WebAuthn_user_verified", { timeout: 15000 });
    const executed = await (await client.get(path)).json();
    expect(executed.status).toBe("executed");
    expect(executed.receipt.database_version_after).toBe(executed.receipt.database_version_before + 1);
    expect(executed.receipt.native_version_after).toBe(executed.receipt.native_version_before + 60);
    const retry = await (await client.post(`${path}/execute`, { headers, data: { plan_sha256: digest } })).json();
    expect(retry.receipt).toEqual(executed.receipt);
    expect((await client.post(`${secondPath}/execute`, { headers, data: { plan_sha256: second.plan_sha256 } })).status()).toBe(403);
    expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
    await page.locator(".approval-panel").screenshot({ path: "docs/results/phase9-approval.png" });
    writeFileSync("docs/results/phase9-webauthn-browser.json", JSON.stringify({ mode: "actual_Chromium_WebAuthn_virtual_authenticator_NOT_physical_key", proof: "real server cryptographic verification; persistent approval interrupt; real Node gateway and Mongo CAS", receipt: executed.receipt, no_approval: "denied", changed_digest: "denied", assertion_replay: "denied", stale_approved_state: "denied", retry: "same receipt, no second mutation" }, null, 2) + "\n");
  } finally {
    const { credentials } = await cdp.send("WebAuthn.getCredentials", { authenticatorId });
    if (credentials.length) { mkdirSync(".run", { recursive: true }); writeFileSync(fixturePath, JSON.stringify(credentials[0]), { mode: 0o600 }); }
    await cdp.send("WebAuthn.removeVirtualAuthenticator", { authenticatorId });
  }
});
