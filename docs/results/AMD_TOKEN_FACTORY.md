# AMD Token Factory routing — provisional, 2026-10-16

Keep DeepSeek-V4-Flash primary, GLM-5.3-Flash secondary and
Qwen3.8-Flash-Next fallback. This is a provisional operational order, not a
measured quality ranking. Official documentation and authenticated catalog reads
confirm all three names. DeepSeek omits reasoning_effort; GLM uses low; Qwen uses
none to bound latency. These settings may trade reasoning depth for speed.

The fixed-origin standalone adapter enforces bounded responses, exact observed
model aliases, strict local ModelOpinion validation, evidence-reference checks,
no tool calls, token accounting and a total deadline. Auth/shared quota failures
stop routing. Transport or validation failures may try the next reviewed model.
The probe batch now also stops after a shared 401/403/429; it does not retry.
It has no execution authority. LangGraph still uses the existing local backend;
this addition does not enable hosted graph reasoning automatically.

Actual evidence:

- Catalog HTTP 200; all three requested models listed.
- Separate tiny identity calls returned HTTP 200 for all three, using exact
  self-dploy/ aliases. Initial alias-related refusals are retained separately.
- Six structured-opinion smoke cases: two validated abstentions (DeepSeek and
  GLM), two sensor cases rejected by validation, one GLM timeout and one Qwen
  shared-quota 429. The original batch continued to its final case after 429;
  the probe is now corrected to stop. No rerun or concealed failures.
- Passing abstention latencies were 1760.8246 ms and 4916.9607 ms respectively;
  single observations do not establish comparative performance or reliability.
- Failure diagnostics do not establish which internal validation condition caused
  the two ValueErrors. Raw model reasoning and credentials are not recorded.

See amd-token-factory-catalog.json, amd-token-factory-model-identities.json,
amd-token-factory-smoke-initial-refusal.json and amd-token-factory-smoke.json.
No representative accuracy, long-context, GPU identity or MI300X benchmark was
performed. Hosted graph acceptance and MI300X acceptance remain BLOCKED. Evolus
and Pinecone full live acceptance also remain BLOCKED; verified read-only
metadata is recorded separately. No enterprise mutation or deployment occurred.

Validation: 25 focused Python tests passed; Ruff passed; mypy passed all 49
source files; generated contract schemas match. HTTP-double tests prove client
behavior, not provider reliability. No full-stack gate was rerun for this
isolated adapter/probe addition.

Official references:
- https://amd-aim.github.io/radeon-cloud-docs/guides/model-apis/
- https://amd-aim.github.io/radeon-cloud-docs/models/deepseek-v4-flash/
- https://amd-aim.github.io/radeon-cloud-docs/models/glm-5-3-flash/
- https://amd-aim.github.io/radeon-cloud-docs/models/qwen3-8-flash-next/
