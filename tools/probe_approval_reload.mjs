// Actual browser regression probe. No token/header/credential is printed.
import { chromium } from "@playwright/test";
import { readFileSync, writeFileSync } from "node:fs";
import { createHash } from "node:crypto";
const args = process.argv.slice(2);
const output = args[args.indexOf("--output") + 1];
const expected = args[args.indexOf("--expect") + 1];
if (!output || !["missing", "resumed"].includes(expected)) throw new Error("Explicit output and expected behavior required");
const env = Object.fromEntries(readFileSync(".env", "utf8").split(/\r?\n/).filter((line) => line && !line.startsWith("#")).map((line) => { const index = line.indexOf("="); return [line.slice(0, index), line.slice(index + 1)]; }));
const browser = await chromium.launch();
try {
  const page = await browser.newPage();
  await page.goto(`http://localhost:${env.AEGIS_WEB_PORT ?? "8080"}`);
  const connect = async () => { await page.getByLabel("Local viewer token").fill(env.AEGIS_VIEWER_TOKEN); await page.getByRole("button", { name: "Connect to live stream" }).click(); };
  await connect();
  await page.getByLabel("Local approval owner token").fill(env.AEGIS_APPROVER_TOKEN);
  await page.getByRole("button", { name: "Start approval session" }).click();
  await page.getByTestId("approval-session").waitFor();
  await page.getByRole("button", { name: "Prepare sandbox stop", exact: true }).click();
  await page.getByTestId("approval-proposal").waitFor();
  await page.reload();
  await connect();
  // Await the server session restore when implemented; baseline has no restore request.
  let resumed = false;
  try { await page.getByTestId("approval-proposal").waitFor({ timeout: 4000 }); resumed = true; } catch {}
  const source_sha256 = createHash("sha256").update(readFileSync("apps/web/src/ApprovalPanel.tsx")).digest("hex");
  const result = { probe: "actual_Chromium_owner_session_and_paused_proposal_reload", resumed, expected, operational_write: false, source: "running_local_stack", source_sha256, observed_at: new Date().toISOString() };
  writeFileSync(output, JSON.stringify(result, null, 2) + "\n");
  if (resumed !== (expected === "resumed")) throw new Error("Observed behavior differs from expected regression state");
  console.log(JSON.stringify(result));
} finally { await browser.close(); }
