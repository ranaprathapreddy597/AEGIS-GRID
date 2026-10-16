// Actual 180-second browser capture. CI virtual authenticator, never physical-key proof.
import { chromium, expect } from "@playwright/test";
import { readFileSync, writeFileSync, existsSync, mkdirSync } from "node:fs";
import { resolve, join } from "node:path";
import { performance } from "node:perf_hooks";

const args = process.argv.slice(2);
const argument = (name, fallback) => args.includes(name) ? args[args.indexOf(name)+1] : fallback;
const workspace = resolve(argument("--workspace", process.cwd()));
const output = resolve(argument("--output", join(workspace, "docs/results/phase12-demo")));
const env = Object.fromEntries(readFileSync(join(workspace, ".env"), "utf8").split(/\r?\n/).filter((line) => line && !line.startsWith("#")).map((line) => { const i=line.indexOf("="); return [line.slice(0,i),line.slice(i+1)]; }));
const origin = `http://localhost:${env.AEGIS_WEB_PORT ?? "8080"}`;
mkdirSync(output, { recursive: true });
const fixture = join(workspace, ".run/webauthn-ci.json");
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 960 }, recordVideo: { dir: output, size: { width: 1440, height: 960 } } });
const page = await context.newPage();
const video = page.video();
const cdp = await context.newCDPSession(page);
await cdp.send("WebAuthn.enable");
const { authenticatorId } = await cdp.send("WebAuthn.addVirtualAuthenticator", { options: { protocol: "ctap2", transport: "internal", hasResidentKey: true, hasUserVerification: true, isUserVerified: true, automaticPresenceSimulation: true } });
let reused = existsSync(fixture);
if (reused) { const value=JSON.parse(readFileSync(fixture,"utf8")); value.signCount+=100; await cdp.send("WebAuthn.addCredential", { authenticatorId, credential:value }); }
const started = performance.now();
const cues=[];
let current="initialization";
let result;
async function cue(second, name, action) {
  current=name;
  const wait=second*1000-(performance.now()-started);
  if(wait>0) await new Promise((done)=>setTimeout(done,wait));
  await action();
  cues.push({ target_s:second, completed_s:(performance.now()-started)/1000, name });
  console.log(`Actual demo cue completed: ${name}`);
}
async function capture(name, locator) {
  await locator.scrollIntoViewIfNeeded();
  await page.screenshot({path:join(output,name+".png")});
}
try {
  await cue(0,"live native telemetry", async()=>{
    await page.goto(origin);
    await page.getByLabel("Local viewer token").fill(env.AEGIS_VIEWER_TOKEN);
    await page.getByRole("button",{name:"Connect to live stream"}).click();
    await expect(page.getByTestId("connection-status")).toHaveText("Live telemetry");
    await capture("01-live-twin",page.locator("#live-twin"));
  });
  await cue(15,"observed and truth overlay", async()=>{
    await page.getByRole("button",{name:"Simulation ground truth"}).click();
    await expect(page.getByTestId("truth-0")).toBeVisible();
    await capture("02-observed-truth",page.locator(".topology"));
  });
  await cue(30,"seeded isolated deceptive fault", async()=>{
    await page.getByLabel("Replay seed").fill("42");
    await page.getByRole("button",{name:"Run isolated fault"}).click();
    await expect(page.getByTestId("laboratory-replay")).toBeVisible();
    await page.getByRole("button",{name:"Pause replay"}).click();
    await page.getByRole("slider",{name:"Analysis replay position"}).fill("59");
    await capture("03-private-fault",page.getByTestId("laboratory-replay"));
  });
  await cue(50,"real persistent cyclic reasoning and adversarial search", async()=>{
    await page.getByRole("button",{name:"Investigate selected fault"}).click();
    await expect(page.getByTestId("laboratory-investigation")).toContainText("409 actual rollouts",{timeout:20000});
    await expect(page.getByTestId("laboratory-investigation")).toContainText("paused_no_action");
    await capture("04-real-langgraph",page.getByTestId("laboratory-investigation"));
  });
  await cue(75,"cited contradiction blocks incident action", async()=>{
    await page.getByRole("button",{name:"Retrieve citations"}).click();
    await expect(page.getByTestId("manual-evidence")).toContainText("NO ACTION");
    await capture("05-manual-no-action",page.getByTestId("manual-evidence"));
  });
  await cue(95,"measured ten thousand CPU futures", async()=>{
    await page.getByRole("button",{name:"Inspect 10,000 actual futures"}).click();
    await expect(page.getByTestId("futures-ensemble")).toContainText("120,000,000 native substeps");
    await capture("06-measured-futures",page.getByTestId("futures-ensemble"));
  });
  await cue(115,"virtual passkey approved local Mongo and native stop", async()=>{
    await page.getByLabel("Local approval owner token").fill(env.AEGIS_APPROVER_TOKEN);
    await page.getByRole("button",{name:"Start approval session"}).click();
    await expect(page.getByTestId("approval-session")).toBeVisible();
    const session=await (await context.request.get(origin+"/api/v1/approval/session")).json();
    if(!session.enrolled_credentials && reused) { await cdp.send("WebAuthn.clearCredentials",{authenticatorId}); reused=false; }
    if(!reused) { await page.getByRole("button",{name:"Enroll passkey"}).click(); await expect(page.locator(".approval-panel").getByRole("status")).toContainText("Passkey enrolled"); }
    const prepared=page.waitForResponse((response)=>response.url().endsWith("/api/v1/approval/maintenance-proposals"));
    await page.getByRole("button",{name:"Prepare maintenance record + stop"}).click();
    const proposal=await (await prepared).json();
    const path=origin+"/api/v1/approval/proposals/"+proposal.action_id;
    const headers={Origin:origin};
    expect((await context.request.post(path+"/execute",{headers,data:{plan_sha256:proposal.plan_sha256}})).status()).toBe(403);
    await page.getByRole("button",{name:"Approve exact action with passkey"}).click();
    await expect(page.getByTestId("approval-proposal").getByRole("heading",{name:"approved",exact:true})).toBeVisible();
    await page.getByRole("button",{name:"Execute approved sandbox stop"}).click();
    await expect(page.getByTestId("approval-receipt")).toContainText("local_mongo_and_simulator");
    result=await (await context.request.get(path)).json();
    expect(result.receipt.database_version_after).toBe(result.receipt.database_version_before+1);
    const retry=await (await context.request.post(path+"/execute",{headers,data:{plan_sha256:proposal.plan_sha256}})).json();
    expect(retry.receipt).toEqual(result.receipt);
    await capture("07-actual-authorized-receipt",page.getByTestId("approval-receipt"));
  });
  await cue(140,"verified repair diff and honest blocked connectors", async()=>{
    await page.getByRole("button",{name:"Inspect connector gates"}).click();
    await expect(page.getByTestId("connector-gates")).toContainText("Evolus MCP · BLOCKED");
    await page.getByText("Review the exact standalone patch",{exact:true}).click();
    await capture("08-connector-gates",page.locator(".integration-panel"));
  });
  await cue(160,"reproducible analysis export", async()=>{
    const waiting=page.waitForEvent("download");
    await page.getByRole("button",{name:"Download analysis replay"}).click();
    await (await waiting).saveAs(join(output,"analysis-replay.json"));
    await capture("09-provenance",page.getByTestId("laboratory-replay"));
  });
  await cue(180,"local demonstration complete; release blocked", async()=>{});
  writeFileSync(join(output,"proof.json"),JSON.stringify({result:"PASS",mode:"actual_180_second_local_browser_demo",passkey:"Chromium virtual CTAP2; real server ES256 verification; NOT physical key",duration_s:(performance.now()-started)/1000,cues,receipt:result.receipt,external_live_gates:"MI300X/Evolus/Pinecone/GitHub BLOCKED",incident_authorization:"BLOCKED by manual; demonstrated action only stationary local sandbox"},null,2)+"\n");
} catch {
  writeFileSync(join(output,"failure.json"),JSON.stringify({result:"FAIL",stage:current,elapsed_s:(performance.now()-started)/1000,detail:"Inspect running stack and rerun; credentials and browser assertion data intentionally omitted."},null,2)+"\n");
  console.error(`Demo failed at stage: ${current}`);
  process.exitCode=1;
} finally {
  const {credentials}=await cdp.send("WebAuthn.getCredentials",{authenticatorId});
  if(credentials.length) { mkdirSync(join(workspace,".run"),{recursive:true}); writeFileSync(fixture,JSON.stringify(credentials[0]),{mode:0o600}); }
  await context.close();
  await video.saveAs(join(output,"demo.webm"));
  await video.delete();
  await browser.close();
}
