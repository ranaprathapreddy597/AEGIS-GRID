// Explicit live acceptance only. No provider writes, simulator controls or approval clicks.
import { chromium } from "@playwright/test";
import { readFileSync, writeFileSync } from "node:fs";
import { performance } from "node:perf_hooks";

const env = Object.fromEntries(readFileSync(".env", "utf8").split(/\r?\n/).filter(l => l && !l.startsWith("#")).map(l => { const i = l.indexOf("="); return [l.slice(0, i), l.slice(i + 1)]; }));
const origin = `http://localhost:${env.AEGIS_WEB_PORT ?? "8080"}`;
const browser = await chromium.launch({headless: true});
const page = await browser.newPage({viewport: {width: 1440, height: 1100}});
const errors = [];
page.on("pageerror", e => errors.push(e.message));
const started = performance.now();
const proof = {status: "BLOCKED", physical_io: false, provider_writes: 0};
try {
  await page.goto(origin);
  await page.getByLabel("Local viewer token").fill(env.AEGIS_VIEWER_TOKEN);
  await page.getByRole("button", {name: "Connect to live stream"}).click();
  await page.getByText("configured mode: amd_hosted", {exact: false}).waitFor();
  const button = page.getByRole("button", {name: "Investigate selected incident"});
  await button.waitFor();
  const stream = page.waitForResponse(r => /\/investigations\/[^/]+\/events$/.test(new URL(r.url()).pathname));
  const final = page.waitForResponse(r => r.request().method() === "POST" && r.url().endsWith("/investigate"), {timeout: 230000});
  await button.click();
  proof.sse_http_status = (await stream).status();
  const response = await final;
  proof.api_http_status = response.status();
  const report = await response.json();
  proof.investigation = report;
  await page.getByTestId("investigation-report").getByText("PAUSED - NO ACTION", {exact: true}).waitFor();
  proof.ui_stream_received = await page.getByText("Live graph checkpoints received", {exact: true}).isVisible();
  await page.getByText(/^Verified source citations/).click();
  await page.locator(".investigation-panel").screenshot({path: "docs/results/cloud-dashboard.png"});
  const headers = {Authorization: `Bearer ${env.AEGIS_VIEWER_TOKEN}`};
  const persisted = await page.request.get(`${origin}/api/v1/investigations/${report.investigation_id}`, {headers});
  proof.persisted_report_identical = JSON.stringify(await persisted.json()) === JSON.stringify(report);
  proof.ui_model_attribution = await page.locator(".investigation-panel").innerText();
  const namespaces = new Set(report.source_citations.map(c => c.namespace));
  proof.status = proof.api_http_status === 200 && proof.sse_http_status === 200 && proof.ui_stream_received && proof.persisted_report_identical && namespaces.size === 2 && report.hosted_diagnosis && report.hosted_planning && report.model_attributions.length === 2 && report.recovery_assessment?.total_rollouts === 409 && report.status === "paused_no_action" && report.manual_decision === "no_action" && report.operational_write_allowed === false && errors.length === 0 ? "PASS" : "PARTIAL";
  proof.remaining_gates = "MI300X/Evolus/physical plant BLOCKED; conflicting manual prohibits incident execution; passkey execution remains an independent stationary sandbox demo";
} catch (error) {
  proof.failure_class = error.constructor.name;
  proof.failure = "Live UI/API acceptance failed; provider results are recorded only if actually received";
  console.error(error.message.replaceAll(env.AEGIS_VIEWER_TOKEN, "<redacted>"));
} finally {
  proof.browser_errors = errors;
  proof.elapsed_s = (performance.now() - started) / 1000;
  writeFileSync("docs/results/cloud-ui-live.json", JSON.stringify(proof, null, 2) + "\n");
  await browser.close();
}
console.log(JSON.stringify({status: proof.status, elapsed_s: proof.elapsed_s, amd_attempts: proof.investigation?.amd_request_attempts, pinecone_queries: proof.investigation?.pinecone_query_attempts}));
if (proof.status !== "PASS") process.exitCode = 1;
