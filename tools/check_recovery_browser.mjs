// Actual API/SSE and browser replay of the two persisted hosted investigations.
// Reuses exact idempotency keys. No extra inference, approval or execution.
import { chromium } from "@playwright/test";
import { readFileSync, writeFileSync } from "node:fs";

const env = Object.fromEntries(readFileSync(".env", "utf8").split(/\r?\n/).filter(l => l && !l.startsWith("#")).map(l => { const i = l.indexOf("="); return [l.slice(0,i), l.slice(i+1)]; }));
const evidence = JSON.parse(readFileSync("docs/results/recovery-scenarios-live.json", "utf8"));
const origin = `http://localhost:${env.AEGIS_WEB_PORT ?? "8080"}`;
const browser = await chromium.launch();
const proof = {status: "BLOCKED", mode: "actual persisted hosted incident replay", additional_provider_requests: 0, passkey_ceremony_performed: false, rows: []};
try {
  for (const [name, scenario] of Object.entries(evidence.scenarios)) {
    const report = scenario.investigation;
    const page = await browser.newPage({viewport: {width: 1440, height: 1100}});
    await page.addInitScript(id => { crypto.randomUUID = () => id; }, report.investigation_id);
    const headers = {Authorization: `Bearer ${env.AEGIS_VIEWER_TOKEN}`};
    const gate = await page.request.get(`${origin}/api/v1/investigations/${report.investigation_id}/recovery-eligibility`, {headers});
    const eligibility = await gate.json();
    const denied = await page.request.post(`${origin}/api/v1/investigations/${report.investigation_id}/recovery-eligibility`, {headers, data: {eligible: true}});
    const stream = await page.request.get(`${origin}/api/v1/investigations/${report.investigation_id}/events`, {headers});
    const text = await stream.text();
    await page.goto(origin);
    await page.getByLabel("Local viewer token").fill(env.AEGIS_VIEWER_TOKEN);
    await page.getByRole("button", {name: "Connect to live stream"}).click();
    await page.getByTestId(`incident-${report.incident_id}`).getByRole("button", {name: "Replay incident"}).click();
    const post = page.waitForResponse(r => r.request().method() === "POST" && r.url().endsWith("/investigate"));
    await page.getByRole("button", {name: "Investigate selected incident"}).click();
    const response = await post;
    const replayed = await response.json();
    await page.getByTestId("incident-recovery-eligibility").waitFor();
    await page.locator(".investigation-panel").screenshot({path: `docs/results/recovery-scenario-${name}.png`});
    const row = {scenario: name, incident_id: report.incident_id, investigation_id: report.investigation_id,
      eligibility_http: gate.status(), mutation_http: denied.status(), sse_http: stream.status(),
      sse_report_frame: text.includes("event: investigation"), sse_complete: text.includes("event: complete"),
      api_post_http: response.status(), identical_report: JSON.stringify(replayed) === JSON.stringify(report),
      eligibility, ui_gate: await page.getByTestId("incident-recovery-eligibility").innerText()};
    row.status = row.eligibility_http === 200 && row.mutation_http === 405 && row.api_post_http === 200 && row.identical_report && row.sse_http === 200 && row.sse_report_frame && row.sse_complete && eligibility.eligible === false && eligibility.capability_issued === false ? "PASS" : "FAIL";
    proof.rows.push(row);
    await page.close();
  }
  proof.status = proof.rows.length === 2 && proof.rows.every(r => r.status === "PASS") ? "PASS" : "PARTIAL";
} catch (error) {
  proof.failure_class = error.constructor.name;
  console.error(error.message.replaceAll(env.AEGIS_VIEWER_TOKEN, "<redacted>"));
} finally {
  await browser.close();
  writeFileSync("docs/results/recovery-browser.json", JSON.stringify(proof, null, 2) + "\n");
}
console.log(JSON.stringify({status: proof.status, rows: proof.rows.length}));
if (proof.status !== "PASS") process.exitCode = 1;
