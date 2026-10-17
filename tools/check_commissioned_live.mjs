// Real hosted UI -> incident-bound CTAP2 -> independent Node/native gateway proof.
// Never substitutes an opinion or signature. Reuses a saved investigation key on retry.
import { chromium } from "@playwright/test";
import { readFileSync, writeFileSync, existsSync, mkdirSync } from "node:fs";
import { randomUUID } from "node:crypto";
import assert from "node:assert/strict";

const env = Object.fromEntries(readFileSync(".env", "utf8").split(/\r?\n/).filter(l => l && !l.startsWith("#")).map(l => {const i=l.indexOf("="); return [l.slice(0,i),l.slice(i+1)];}));
const origin = `http://localhost:${env.AEGIS_WEB_PORT ?? "8080"}`;
const path = "docs/results/commissioned-live.json";
const previous = existsSync(path) ? JSON.parse(readFileSync(path,"utf8")) : null;
if (previous?.result === "PASS") throw new Error("Preserve the successful one-shot proof; use read-back, not another execution.");
const identifier = previous?.investigation_id ?? randomUUID();
const proof = {result: "BLOCKED", mode: "actual_AMD_dual_Pinecone_Chromium_virtual_CTAP2_native_replay", investigation_id: identifier, physical_io: false, checks: {}};
const save = () => writeFileSync(path, JSON.stringify(proof,null,2)+"\n");
save();
const browser = await chromium.launch();
const state = ".run/commissioned-browser-state.json";
const context = await browser.newContext({viewport:{width:1440,height:1100}, ...(existsSync(state) ? {storageState:state} : {})});
const page = await context.newPage();
await page.addInitScript(id => {crypto.randomUUID = () => id;}, identifier);
const cdp = await context.newCDPSession(page);
await cdp.send("WebAuthn.enable");
const {authenticatorId} = await cdp.send("WebAuthn.addVirtualAuthenticator",{options:{protocol:"ctap2",transport:"internal",hasResidentKey:true,hasUserVerification:true,isUserVerified:true,automaticPresenceSimulation:true}});
const fixture = ".run/webauthn-ci.json";
let reused = existsSync(fixture);
if (reused) { const credential=JSON.parse(readFileSync(fixture,"utf8"));credential.signCount+=100;await cdp.send("WebAuthn.addCredential",{authenticatorId,credential}); }
const client=context.request;
const headers={Origin:origin};
const viewer={Authorization:`Bearer ${env.AEGIS_VIEWER_TOKEN}`};
const started=performance.now();
async function assertion(options) {
  return await page.evaluate(async options => {
    const value=await navigator.credentials.get({publicKey:PublicKeyCredential.parseRequestOptionsFromJSON(options)});
    const response=value.response;
    const enc=v=>btoa(String.fromCharCode(...new Uint8Array(v))).replaceAll("+","-").replaceAll("/","_").replaceAll("=","");
    return {id:value.id,rawId:enc(value.rawId),type:value.type,clientExtensionResults:value.getClientExtensionResults(),response:{authenticatorData:enc(response.authenticatorData),clientDataJSON:enc(response.clientDataJSON),signature:enc(response.signature),userHandle:response.userHandle?enc(response.userHandle):null}};
  },options);
}
try {
  proof.before=await (await client.get(`${origin}/api/v1/commissioned/status`,{headers:viewer})).json();save();
  assert.equal(proof.before.enabled,true,"Explicit commissioned mode is required");
  assert.equal(proof.before.receipts.length,0,"Commissioned resource is one-shot; no reset or overwrite");
  await page.goto(origin);
  await page.getByLabel("Local viewer token").fill(env.AEGIS_VIEWER_TOKEN);
  await page.getByRole("button",{name:"Connect to live stream"}).click();
  if (!(await client.get(`${origin}/api/v1/approval/session`)).ok()) {
    await page.getByLabel("Local approval owner token").fill(env.AEGIS_APPROVER_TOKEN);
    await page.getByRole("button",{name:"Start approval session"}).click();
  }
  await page.getByTestId("approval-session").waitFor();
  const session=await (await client.get(`${origin}/api/v1/approval/session`)).json();
  if (!session.enrolled_credentials && reused) {await cdp.send("WebAuthn.clearCredentials",{authenticatorId});reused=false;}
  if (!reused) {
    await page.getByRole("button",{name:"Enroll passkey",exact:true}).click();
    await page.locator(".approval-panel").getByRole("status").filter({hasText:"Passkey enrolled"}).waitFor();
  }
  const reportResponse=page.waitForResponse(r=>r.request().method()==="POST"&&r.url().endsWith("/approval/commissioned/investigate"),{timeout:180000});
  await page.getByRole("button",{name:"Investigate commissioned incident",exact:true}).click();
  const response=await reportResponse;
  proof.investigation_http=response.status();
  proof.investigation=await response.json();save();
  assert.equal(response.status(),200,"Hosted investigation HTTP refusal");
  await page.getByTestId("commissioned-report").waitFor();
  await page.locator(".commissioned-panel").screenshot({path:"docs/results/commissioned-investigation.png"});
  if (proof.investigation.status!=="awaiting_approval" || !proof.investigation.meaningful_diagnosis || !proof.investigation.grounded_planning) {
    proof.blocker="Actual hosted diagnosis/planning or independent evidence did not qualify; no approval requested";save();
  } else {
    const original=JSON.parse(readFileSync("docs/results/recovery-scenarios-live.json","utf8")).scenarios.A.investigation;
    proof.checks.original_report_not_commissionable=(await client.post(`${origin}/api/v1/approval/commissioned/investigations/${original.investigation_id}/proposal`,{headers})).status();
    assert.equal(proof.checks.original_report_not_commissionable,403);
    const prepared=page.waitForResponse(r=>r.request().method()==="POST"&&r.url().endsWith(`/investigations/${identifier}/proposal`));
    await page.getByRole("button",{name:"Prepare incident-bound recovery"}).click();
    const preparedResponse=await prepared;assert.equal(preparedResponse.status(),200);
    proof.proposal=await preparedResponse.json();save();
    const plan=JSON.parse(proof.proposal.action_json);
    assert.equal(plan.plant_id,proof.before.plant_id);assert.equal(plan.incident_id,proof.before.incident_id);
    assert.equal(plan.rules_sha256,proof.before.rules_sha256);assert.equal(plan.duration_s,120);
    const actionPath=`${origin}/api/v1/approval/commissioned/proposals/${plan.action_id}`;
    proof.checks.no_approval=(await client.post(`${actionPath}/execute`,{headers,data:{plan_sha256:proof.proposal.plan_sha256}})).status();
    assert.equal(proof.checks.no_approval,403);
    proof.checks.wrong_origin=(await client.post(`${actionPath}/options`,{headers:{Origin:"http://untrusted.invalid"}})).status();
    assert.equal(proof.checks.wrong_origin,403);
    const optionsResponse=page.waitForResponse(r=>r.request().method()==="POST"&&r.url()===`${actionPath}/options`);
    const verifyRequest=page.waitForRequest(r=>r.method()==="POST"&&r.url()===`${actionPath}/verify`);
    const verifyResponse=page.waitForResponse(r=>r.request().method()==="POST"&&r.url()===`${actionPath}/verify`);
    await page.getByRole("button",{name:"Approve commissioned action with passkey"}).click();
    proof.challenge=await (await optionsResponse).json();
    proof.public_virtual_authenticator_assertion=(await verifyRequest).postDataJSON();
    const verified=await verifyResponse;proof.verification_http=verified.status();proof.approved=await verified.json();save();
    assert.equal(verified.status(),200,"Actual server-side WebAuthn verification required");
    assert.equal(proof.approved.status,"approved");
    const challengeBytes=Buffer.from(proof.challenge.options.challenge,"base64url");
    assert.equal(challengeBytes.subarray(32).toString("hex"),proof.proposal.plan_sha256);
    proof.checks.assertion_replay=(await client.post(`${actionPath}/verify`,{headers,data:proof.public_virtual_authenticator_assertion})).status();
    assert.equal(proof.checks.assertion_replay,403);
    proof.checks.changed_digest=(await client.post(`${actionPath}/execute`,{headers,data:{plan_sha256:"f".repeat(64)}})).status();
    assert.equal(proof.checks.changed_digest,403);
    // A second genuinely approved action against the same state must become stale.
    const secondResponse=await client.post(`${origin}/api/v1/approval/commissioned/investigations/${identifier}/proposal`,{headers});
    assert.equal(secondResponse.status(),200);const second=await secondResponse.json();
    const secondPath=`${origin}/api/v1/approval/commissioned/proposals/${second.action_id}`;
    const secondOptions=await (await client.post(`${secondPath}/options`,{headers})).json();
    const secondCredential=await assertion(secondOptions.options);
    const secondApproved=await client.post(`${secondPath}/verify`,{headers,data:{ceremony_id:secondOptions.ceremony_id,credential:secondCredential}});
    assert.equal(secondApproved.status(),200);proof.stale_proposal={action_id:second.action_id,plan_sha256:second.plan_sha256};save();
    const executedResponse=page.waitForResponse(r=>r.request().method()==="POST"&&r.url()===`${actionPath}/execute`);
    await page.getByRole("button",{name:"Execute approved incident recovery"}).click();
    const executed=await executedResponse;proof.execution_http=executed.status();proof.execution=await executed.json();save();
    assert.equal(executed.status(),200);assert.equal(proof.execution.status,"executed");
    const receipt=proof.execution.receipt;
    assert.equal(receipt.authorization,"WebAuthn_user_verified");assert.equal(receipt.plant_id,plan.plant_id);
    assert.equal(receipt.incident_id,plan.incident_id);assert.equal(receipt.plan_sha256,proof.proposal.plan_sha256);
    assert.equal(receipt.native_version_after,receipt.native_version_before+120);
    assert.ok(receipt.maximum_temperature_c<70);assert.ok(Math.max(...receipt.temperatures_after_c)<Math.max(...receipt.temperatures_before_c));
    assert.equal(receipt.fault_retained,true);assert.equal(receipt.physical_io,false);
    proof.checks.execution_replay=(await client.post(`${actionPath}/execute`,{headers,data:{plan_sha256:proof.proposal.plan_sha256}})).status();
    proof.checks.stale_approved_state=(await client.post(`${secondPath}/execute`,{headers,data:{plan_sha256:second.plan_sha256}})).status();
    assert.equal(proof.checks.execution_replay,403);assert.equal(proof.checks.stale_approved_state,403);
    proof.persisted=await (await client.get(actionPath)).json();assert.deepEqual(proof.persisted.receipt,receipt);
    proof.after=await (await client.get(`${origin}/api/v1/commissioned/status`,{headers:viewer})).json();
    assert.equal(proof.after.receipts.length,1);assert.equal(proof.after.database_version,proof.before.database_version+1);
    const originalGate=await client.get(`${origin}/api/v1/investigations/${original.investigation_id}/recovery-eligibility`,{headers:viewer});
    proof.original_refusal=await originalGate.json();assert.equal(proof.original_refusal.eligible,false);
    assert.ok(proof.original_refusal.blockers.includes("unresolved_manual_evidence"));
    await page.getByTestId("commissioned-receipt").waitFor();
    await page.locator(".commissioned-panel").screenshot({path:"docs/results/commissioned-authorized-recovery.png"});
    proof.result="PASS";save();
  }
} catch(error) {
  proof.failure_class=error.constructor.name;
  proof.failure=String(error.message).replaceAll(env.AEGIS_APPROVER_TOKEN,"<redacted>").replaceAll(env.AEGIS_VIEWER_TOKEN,"<redacted>").slice(0,2000);
} finally {
  proof.elapsed_s=(performance.now()-started)/1000;save();
  const {credentials}=await cdp.send("WebAuthn.getCredentials",{authenticatorId});
  mkdirSync(".run",{recursive:true});if(credentials.length)writeFileSync(fixture,JSON.stringify(credentials[0]),{mode:0o600});
  await context.storageState({path:state});
  await cdp.send("WebAuthn.removeVirtualAuthenticator",{authenticatorId});
  await browser.close();
}
console.log(JSON.stringify({result:proof.result,amd_attempts:proof.investigation?.amd_request_attempts,execution_http:proof.execution_http,blocker:proof.blocker,failure:proof.failure_class}));
if(proof.result!=="PASS")process.exitCode=1;
