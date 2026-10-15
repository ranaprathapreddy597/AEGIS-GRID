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
  expect(Math.abs(rendered - data.cells[0].temperature_c)).toBeLessThan(0.1);
  const downloadWait = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export frame" }).click();
  const download = await downloadWait;
  expect(download.suggestedFilename()).toMatch(/^aegis-frame-\d+\.json$/);
  const path = await download.path();
  expect(path).toBeTruthy();
  const exported = JSON.parse(readFileSync(path!, "utf8"));
  expect(exported.simulator_sha256).toMatch(/^[0-9a-f]{64}$/);
  expect(exported.run_id).toBe(data.run_id);
  const accessibility = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
  expect(accessibility.violations.map((v) => ({ id: v.id, impact: v.impact, nodes: v.nodes.map((n) => n.target) }))).toEqual([]);
  await page.screenshot({ path: "docs/results/phase1-dashboard.png", fullPage: true });
  await page.getByRole("tab", { name: /Signal log/ }).click();
  await expect(page.getByRole("table")).toBeVisible();
  await page.getByRole("tab", { name: "Live overview" }).click();
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: "docs/results/phase1-mobile.png", fullPage: true });
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
