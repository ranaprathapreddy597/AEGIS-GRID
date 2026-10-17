import { readFileSync } from "node:fs";
import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const token = readFileSync(".env", "utf8").split(/\r?\n/).find(line => line.startsWith("AEGIS_VIEWER_TOKEN="))?.split("=")[1];
if (!token) throw new Error("Viewer token missing");

test("command center renders measured signals, observed-only forecasts and preserved experiment provenance", async ({ page }) => {
  test.setTimeout(60000);
  const forecastBodies: Record<string, unknown>[][] = [];
  page.on("request", request => {
    if (request.url().endsWith("/api/v1/analysis/forecast")) forecastBodies.push((request.postDataJSON() as { history: Record<string, unknown>[] }).history);
  });
  await page.goto("/");
  await page.getByLabel("Local viewer token").fill(token);
  await page.getByRole("button", { name: "Connect to live stream" }).click();
  await expect(page.getByTestId("connection-status")).toHaveText("Live telemetry");
  await expect(page.locator(".signal-cell")).toHaveCount(6);
  await expect(page.locator(".cell-sparkline")).toHaveCount(6);
  await expect(page.locator(".signal-cell").first()).toContainText("Observed flow");
  await expect(page.locator(".signal-cell").first()).toContainText("Synthetic guard 65 °C / hard limit 70 °C");
  await expect(page.getByRole("region", { name: "Data and authority boundaries" })).toContainText("Only verified executor receipts prove a write");
  await expect(page.getByTestId("thermal-forecast")).toBeVisible({ timeout: 20000 });
  // Require a sufficiently long real observation window, not just the initial abstention.
  // This also exercises requests beyond nginx's former 16 KiB default body limit.
  await expect(page.locator(".forecast-grid article")).toHaveCount(6, { timeout: 35000 });
  await expect(page.getByTestId("sprint-evidence")).toContainText("Recorded evaluation");
  await expect.poll(() => forecastBodies.length).toBeGreaterThan(0);
  expect(Object.keys(forecastBodies[0][0]).sort()).toEqual(["cells", "coolant_temperature_c", "loop_pressure_kpa", "measurement", "simulation_time_s", "state_version"]);
  const accessibility = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
  expect(accessibility.violations).toEqual([]);
  await page.locator(".dashboard-grid").screenshot({ path: "docs/results/sprint-live-twin.png" });
  await page.locator(".intelligence-panel").screenshot({ path: "docs/results/sprint-intelligence.png" });
  await page.screenshot({ path: "docs/results/sprint-command-center.png", fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: "docs/results/sprint-command-center-mobile.png", fullPage: true });
});

test("native explorer exposes unsafe strategy counterexamples without offering execution", async ({ page }) => {
  test.setTimeout(60000);
  await page.goto("/");
  await page.getByLabel("Local viewer token").fill(token);
  await page.getByRole("button", { name: "Connect to live stream" }).click();
  await expect(page.getByRole("button", { name: "Compare recovery futures" })).toBeEnabled();
  await page.getByRole("button", { name: "Compare recovery futures" }).click();
  await expect(page.getByTestId("recovery-report")).toContainText("NON-EXECUTABLE", { timeout: 20000 });
  await page.locator(".candidate-picker").getByRole("button", { name: /planted-unsafe/ }).click();
  const inspected = page.getByTestId("candidate-inspection");
  await expect(inspected).toContainText("INFEASIBLE");
  await expect(inspected).toContainText("Mean energy");
  await inspected.getByText(/Inspect native refusal evidence/).click();
  await expect(inspected.locator("pre")).toBeVisible();
  expect(await inspected.getByRole("button").count()).toBe(0);
  await expect(inspected).toContainText("other candidates expose aggregate outcomes only");
  await page.locator(".recovery-panel").screenshot({ path: "docs/results/sprint-native-explorer.png" });
});
