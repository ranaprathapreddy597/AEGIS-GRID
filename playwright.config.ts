import { defineConfig, devices } from "@playwright/test";
import { readFileSync } from "node:fs";
const localPort = readFileSync(".env", "utf8").split(/\r?\n/).find((line) => line.startsWith("AEGIS_WEB_PORT="))?.split("=")[1] ?? "8080";
const port = process.env.AEGIS_WEB_PORT ?? localPort;
export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 30000,
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [["list"], ["json", { outputFile: "test-results/e2e-results.json" }]],
  use: { baseURL: `http://127.0.0.1:${port}`, trace: "off", screenshot: "only-on-failure" },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 1100 } } }],
});
