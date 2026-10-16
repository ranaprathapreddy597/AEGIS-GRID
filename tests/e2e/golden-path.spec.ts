import { readFileSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const token = readFileSync(".env", "utf8").split(/\r?\n/).find((line) => line.startsWith("AEGIS_VIEWER_TOKEN="))?.split("=")[1];
if (!token) throw new Error("Local viewer token unavailable; run python tools/dev.py start");

test("actual C++ telemetry reaches React, exports provenance, and remains accessible", async ({ page, request }) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Factory signal room." })).toBeVisible();
  const unauthorized = await request.get("/api/v1/telemetry/latest");
  expect(unauthorized.status()).toBe(401);
  await page.getByLabel("Local viewer token").fill(token);
  await page.getByRole("button", { name: "Connect to live stream" }).click();
  await expect(page.getByTestId("connection-status")).toHaveText("Live telemetry");
  const first = await page.getByTestId("temperature-0").innerText();
  await expect.poll(() => page.getByTestId("temperature-0").innerText(), { timeout: 20000 }).not.toBe(first);
  const sample = await request.get("/api/v1/telemetry/latest", { headers: { Authorization: `Bearer ${token}` } });
  const data = await sample.json();
  expect(data.source).toBe("local_cpp_simulator");
  const rendered = parseFloat(await page.getByTestId("temperature-0").innerText());
  expect(Math.abs(rendered - data.cells[0].temperature_c)).toBeLessThan(0.5);
  const downloadWait = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export frame" }).click();
  const download = await downloadWait;
  expect(download.suggestedFilename()).toMatch(/^aegis-frame-\d+\.json$/);
  const path = await download.path();
  expect(path).toBeTruthy();
  const exported = JSON.parse(readFileSync(path!, "utf8"));
  expect(exported.simulator_sha256).toMatch(/^[0-9a-f]{64}$/);
  expect(exported.run_id).toBe(data.run_id);
  await page.getByRole("button", { name: "Simulation ground truth" }).click();
  await expect(page.getByTestId("truth-0")).toContainText("Flow");
  expect(data.ground_truth.total_flow_kg_s).toBeGreaterThan(0);
  expect(data.scenario_sha256).toMatch(/^[0-9a-f]{64}$/);
  const accessibility = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
  expect(accessibility.violations.map((v) => ({ id: v.id, impact: v.impact, nodes: v.nodes.map((n) => n.target) }))).toEqual([]);
  await page.screenshot({ path: "docs/results/phase6-dashboard.png", fullPage: true });
  await page.getByRole("tab", { name: /Signal log/ }).click();
  await expect(page.getByRole("table")).toBeVisible();
  await page.getByRole("tab", { name: "Live overview" }).click();
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: "docs/results/phase6-mobile.png", fullPage: true });
  await page.getByRole("button", { name: "Disconnect" }).click();
  await expect(page.getByLabel("Local viewer token")).toHaveValue("");
  expect(errors).toEqual([]);
});

test("wrong viewer token fails visibly without telemetry", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Local viewer token").fill("invalid-local-token");
  await page.getByRole("button", { name: "Connect to live stream" }).click();
  await expect(page.getByRole("alert")).toHaveText("Access token rejected.");
  await expect(page.getByTestId("temperature-0")).toHaveCount(0);
});

test("memory calculator reports projected fit and blocked hardware honestly", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Local viewer token").fill(token);
  await page.getByRole("button", { name: "Connect to live stream" }).click();
  await expect(page.getByRole("heading", { name: "Cloud inference readiness" })).toBeVisible();
  await page.getByRole("button", { name: "Project 80 GiB budget" }).click();
  await expect(page.getByTestId("memory-budget")).toContainText("DOES NOT FIT");
  await expect(page.getByTestId("memory-budget")).toContainText("48.00 GiB");
  await page.getByRole("button", { name: "Project 192 GiB budget" }).click();
  await expect(page.getByTestId("memory-budget")).toContainText("PROJECTED HEADROOM");
  await expect(page.locator(".inference-panel")).toContainText("live gate blocked");
  await page.locator(".inference-panel").screenshot({ path: "docs/results/phase6-memory-panel.png" });
});

test("actual manual citations and contradictory bulletin block actions", async ({ page, request }) => {
  await page.goto("/");
  await page.getByLabel("Local viewer token").fill(token);
  await page.getByRole("button", { name: "Connect to live stream" }).click();
  await page.getByRole("button", { name: "Retrieve citations" }).click();
  const evidence = page.getByTestId("manual-evidence");
  await expect(evidence).toContainText("NO ACTION");
  await expect(evidence).toContainText("1000 cited limits");
  await expect(evidence).toContainText("SIM-BULLETIN / R2 / page 1");
  await expect(evidence).toContainText("LIMIT CELL-01 temperature degC 0 95");
  const downloadWait = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download cited source" }).first().click();
  const file = await downloadWait;
  expect(file.suggestedFilename()).toMatch(/^SIM-.*\.pdf$/);
  const path = await file.path();
  expect(readFileSync(path!).subarray(0, 5).toString()).toBe("%PDF-");
  const unauthorized = await request.get("/api/v1/manuals/SIM-MANUAL/source");
  expect(unauthorized.status()).toBe(401);
  const accessibility = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
  expect(accessibility.violations).toEqual([]);
  await page.getByRole("heading", { name: "Factory signal room." }).click();
  await page.screenshot({ path: "docs/results/phase6-manual-evidence.png", fullPage: true });
  await page.locator(".manual-evidence").screenshot({ path: "docs/results/phase6-manual-panel.png" });
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: "docs/results/phase6-manual-mobile.png", fullPage: true });
});

test("real edge outage becomes visible and reconnects to a new simulator run", async ({ page }) => {
  const compose = ["compose", "--env-file", ".env", "-f", "infra/local/compose.yaml"];
  await page.goto("/");
  await page.getByLabel("Local viewer token").fill(token);
  await page.getByRole("button", { name: "Connect to live stream" }).click();
  await expect(page.getByTestId("connection-status")).toHaveText("Live telemetry");
  execFileSync("docker", [...compose, "stop", "edge"], { stdio: "pipe", timeout: 15000 });
  try {
    await expect(page.getByTestId("connection-status")).toContainText(/unavailable|stale/);
    const staleValue = await page.getByTestId("temperature-0").innerText();
    await expect(page.getByTestId("temperature-0")).toHaveText(staleValue);
  } finally {
    execFileSync("docker", [...compose, "start", "edge"], { stdio: "pipe", timeout: 15000 });
  }
  await expect(page.getByTestId("connection-status")).toHaveText("Live telemetry", { timeout: 15000 });
  await expect.poll(async () => parseFloat(await page.getByTestId("temperature-0").innerText())).toBeLessThan(27);
});

test("actual injected fault hides overheat from observed sensors", async ({ page, request }) => {
  test.setTimeout(90000);
  const compose = ["compose", "--env-file", ".env", "-f", "infra/local/compose.yaml", "up", "-d", "--force-recreate", "edge"];
  execFileSync("docker", compose, { stdio: "pipe", timeout: 20000, env: { ...process.env, AEGIS_SCENARIO: "scenario-090", AEGIS_SEED: "42", AEGIS_TIME_SCALE: "20", AEGIS_SAFETY_MODE: "observe_only" } });
  try {
    await page.goto("/");
    await page.getByLabel("Local viewer token").fill(token);
    await page.getByRole("button", { name: "Connect to live stream" }).click();
    await page.getByRole("button", { name: "Simulation ground truth" }).click();
    await expect(page.getByTestId("connection-status")).toHaveText("Live telemetry", { timeout: 15000 });
    await expect.poll(async () => {
      const text = await page.getByTestId("truth-0").innerText();
      return parseFloat(text.replace("Truth ", ""));
    }, { timeout: 45000, intervals: [1000] }).toBeGreaterThan(80);
    const sample = await request.get("/api/v1/telemetry/latest", { headers: { Authorization: `Bearer ${token}` } });
    const data = await sample.json();
    expect(data.scenario_id).toBe("scenario-090");
    expect(data.ground_truth.cells[0].temperature_c).toBeGreaterThan(80);
    expect(Math.max(...data.cells.map((cell: { temperature_c: number }) => cell.temperature_c))).toBeLessThan(80);
    await expect(page.getByTestId("temperature-0")).toContainText(/3[78]\./);
    await page.screenshot({ path: "docs/results/phase6-observe-only-overheat.png", fullPage: true });
  } finally {
    execFileSync("docker", compose, { stdio: "pipe", timeout: 20000 });
  }
});


test("local safety stops deceptive fault while cloud is disabled", async ({ page, request }) => {
  test.setTimeout(60000);
  const compose = ["compose", "--env-file", ".env", "-f", "infra/local/compose.yaml", "up", "-d", "--force-recreate", "edge"];
  execFileSync("docker", compose, { stdio: "pipe", timeout: 20000, env: { ...process.env, AEGIS_SCENARIO: "scenario-090", AEGIS_SEED: "42", AEGIS_TIME_SCALE: "20", AEGIS_SAFETY_MODE: "enforce" } });
  try {
    await page.goto("/");
    await page.getByLabel("Local viewer token").fill(token);
    await page.getByRole("button", { name: "Connect to live stream" }).click();
    await expect(page.getByTestId("sentinel-state")).toHaveText("latched stop", { timeout: 30000 });
    await expect(page.getByTestId("safety-policy")).toContainText("local emergency stop");
    await expect(page.getByTestId("cloud-state")).toHaveText("Cloud disabled");
    await expect.poll(async () => {
      const response = await request.get("/api/v1/telemetry/latest", { headers: { Authorization: `Bearer ${token}` } });
      const data = await response.json();
      return Math.max(...data.cells.map((cell: { load_fraction: number }) => cell.load_fraction));
    }, { timeout: 10000, intervals: [1000] }).toBeLessThan(0.001);
    await page.getByRole("button", { name: "Simulation ground truth" }).click();
    await page.screenshot({ path: "docs/results/phase6-local-stop.png", fullPage: true });
  } finally {
    execFileSync("docker", compose, { stdio: "pipe", timeout: 20000 });
  }
});


test("native incident snapshot and journal survive an API restart", async ({ page, request }) => {
  test.setTimeout(60000);
  const headers = { Authorization: `Bearer ${token}` };
  let incidentId = "";
  await expect.poll(async () => {
    const response = await request.get("/api/v1/incidents", { headers });
    const data = await response.json();
    incidentId = data.items?.[0]?.incident_id ?? "";
    return incidentId.length;
  }, { timeout: 15000, intervals: [1000] }).toBe(64);
  await expect.poll(async () => {
    const response = await request.get(`/api/v1/incidents/${incidentId}/replay`, { headers });
    const data = await response.json();
    return data.events.length;
  }, { timeout: 10000, intervals: [1000] }).toBeGreaterThanOrEqual(2);
  const before = await (await request.get(`/api/v1/incidents/${incidentId}/replay`, { headers })).json();
  expect(before.snapshot_available).toBe(true);
  const snapshot = before.incident.event.snapshot;
  expect(JSON.parse(snapshot.payload_json).version).toBe(snapshot.state_version);
  expect(before.incident.event.origin).toBe("edge_observer");
  execFileSync("docker", ["compose", "--env-file", ".env", "-f", "infra/local/compose.yaml", "restart", "api"], { stdio: "pipe", timeout: 20000 });
  await expect.poll(async () => {
    try {
      const response = await request.get(`/api/v1/incidents/${incidentId}/replay`, { headers });
      return response.status();
    } catch { return 0; }
  }, { timeout: 20000, intervals: [1000] }).toBe(200);
  const after = await (await request.get(`/api/v1/incidents/${incidentId}/replay`, { headers })).json();
  expect(after.reproducibility_sha256).toBe(before.reproducibility_sha256);
  expect(after.incident.event.snapshot.sha256).toBe(snapshot.sha256);
  expect(after.events).toEqual(before.events);
  await page.goto("/");
  await page.getByLabel("Local viewer token").fill(token);
  await page.getByRole("button", { name: "Connect to live stream" }).click();
  await page.getByTestId(`incident-${incidentId}`).getByRole("button", { name: "Replay incident" }).click();
  await expect(page.getByTestId("incident-replay")).toContainText(before.reproducibility_sha256);
  const downloadWait = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download replay" }).click();
  expect((await downloadWait).suggestedFilename()).toMatch(/^aegis-incident-/);
  await page.getByRole("heading", { name: "Factory signal room." }).click();
  await page.screenshot({ path: "docs/results/phase6-restart-replay.png", fullPage: true });
});
