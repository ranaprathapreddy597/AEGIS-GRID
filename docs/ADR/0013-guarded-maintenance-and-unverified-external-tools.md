# ADR 0013: explicit Mongo maintenance diffs and closed external publication

Accepted 2026-10-16, after Phase 9 local gate d8ed0bd. Continue local work without
waiving MI300X/Evolus/Pinecone live gates. No external write is authorized here.

## Real local operational mutation

Extend the immutable proposal with an explicit optional MaintenanceChange, allowed
only for `simulator.stop_and_record_maintenance`. It names the single fixed local
sandbox record, expected record version, before status and fixed after status
`safety_stop_verified`. Reason is a literal independent native stop verification;
there is no arbitrary field/path/query/text update. The UI shows this additional
semantic diff before the same real WebAuthn user-verification ceremony.

Node verifies the new action/diff relationship, schema and fixed stop controls.
The private gateway repeats current record/state/native/certificate checks and
requires the exact human-approved bytes. The maintenance record, native snapshot,
database version, one-use nonce and receipt commit in the **same Mongo document
CAS**. It is a true operational Mongo mutation using the actual local server,
not a provider fake or separate non-atomic second write. It is not a mutation of
a customer's external enterprise database. The record's name/status explicitly
describe the isolated sandbox; no physical maintenance completion is implied.

Failure before commit discards both effects. An uncertain response can reconcile
the durable receipt, and exact retry returns that receipt without another write.
New receipt-v2 binds the maintenance record hash and tool identity. Native stop
execution without a maintenance diff leaves the existing record unchanged.
Read verification checks receipt chain, native snapshot and record fingerprint.
Receipt-v1 hashes from Phase 9 are preserved by excluding the additive v2 fields
from their original digest; original records are never rewritten. Actual existing
Phase 9 Mongo data is read during the new browser gate, alongside a compatibility
unit test. Existing scoped runtime roles remain unchanged.

## Evolus facts, not invented MCP tools

The unchanged supplied OpenAPI hash is
`0af55c67c60d07dc35f37b70553f1a2a6b1cce76a3311d014c6be1473fadd4f8`.
Actual GET `/api/v1/agents` and `/api/v1/agents/{agentId}` inherit application
API-key/application-ID or personal-user/application-ID security. Agent includes
McpServerInfo: IDs, names, configured enabled/disabled tool names and flags.
The verified POST/DELETE `/api/v1/agents/{agentId}/mcpserver/{mcpServerId}` routes
attach/remove configuration, not an MCP tools/call invocation API.

The production read adapter validates the supplied schema and projects only
bounded identity/name/flag/tool-name metadata. It discards agent prompt,
configurationJson and secretScope. Configured tool names are **not verified input
schemas or an execution allowlist**. The supplied material does not establish
an Evolus invocation endpoint, transport/auth negotiation or tool schemas.
Invocation therefore refuses before any network call, even for a configured name
and plausible model-supplied capability. Generic MCP Streamable HTTP documentation
does not prove that Evolus exposes that transport. No adapter fabricates it.
Contract HTTP doubles are explicitly labeled and never count as live proof.

Presence-only probe: application scope exists, API key/document IDs/Pinecone/GitHub
tokens/inference endpoint absent. No credentialed integration call or external write was attempted.
An earlier key was supplied in chat but left unused; no claim that it was never
provided. A provisioned local key and verified live metadata/transport/tools are
still required for the corresponding provider gates.

## Concrete reviewed repair, not a fake PR

Actual Chromium reproduction showed browser reload lost the owner-session view
and paused proposal. A standalone patch against Phase 9 restores both from real
authenticated APIs, keeping only the non-secret active action ID in sessionStorage.
Viewer/owner bootstrap tokens are never stored there. A second actual browser
probe on the running patched UI verifies resume and binds its source hash.
The candidate is intentionally independent of the new maintenance UI feature.
The later full UI contains the identical restoration logic plus that feature.

`tools/prepare_repair.py` reads actual before/after proof, the exact candidate and
the real Git base. It applies/checks the unified diff in a private temporary
directory and compares exact resulting bytes. Git autocrlf is disabled only for
those subprocesses, avoiding Windows normalization falsely changing the digest.
The content-hashed bundle contains base/source/patch hashes, diff and proof. The
API/UI allow review and download only; missing or tampered evidence is unavailable.

GitHub direct preflight uses fixed HTTPS api.github.com, a scoped owner/repository,
documented ref GET and the pinned 2022-11-28 API header. A concrete publication
draft describes branch creation, exact file commit with expected blob SHA, required
CI/review on the resulting commit, and a draft PR with explicit approved base.
It does not execute these steps. Current capability policy has no GitHub write
scope, repository/credentials/required hosted checks are unverified, and `publish`
refuses before HTTP. There is no public remote mutation endpoint or fake PR URL.
Remote partial-failure/compensation/live acceptance remains BLOCKED, not passed.
The local atomic Mongo path has real success/failure/retry evidence independently.

A public GitHub versions metadata GET confirmed 2022-11-28 remains supported
alongside 2026-03-10. This is not authenticated repository integration evidence.

Primary references inspected:
[MCP transport specification](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports),
[GitHub refs](https://docs.github.com/en/rest/git/refs?apiVersion=2022-11-28),
[file contents](https://docs.github.com/en/rest/repos/contents?apiVersion=2022-11-28#create-or-update-file-contents),
[pull requests](https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28#create-a-pull-request).
The supplied Evolus specification is the authority for its actual routes/auth;
the standard MCP specification is not substituted for provider evidence.
