# Phase 6 execution report — 2026-10-16, Asia/Calcutta

Status: **local automated gate PASS**. **MI300X live acceptance gate BLOCKED**.
Phase 5 local baseline: `5513a27`; Evolus/Pinecone live gates remain blocked too.

## Implemented and inspected

| Source | Result |
|---|---|
| `services/inference/aegis_inference/model-*.json` | Actual upstream config/metadata, pinned revision and config SHA; no weight download |
| `budget.py`, `tools/gpu_memory_budget.py` | Full resident BF16 weights, dense GQA BF16/FP8 KV projections, concurrency/context/reserve calculations and invalid configuration refusals |
| `client.py` | Authenticated HTTPS serving client, bounded response/deadline, strict structured non-command opinions, model/token checks and labeled offline abstention backend |
| `infra/cloud/mi300x.compose.yaml`, `serve.py` | Digest/model pinned recipe, loopback port, environment authentication, no remote code/privileged mode, device/runtime refusal checks |
| `probe_device.py`, probe/benchmark tools | Actual device/version collector and network SSE collector; unavailable access yields blocked and empty measurements |
| API, generated contracts, React | Authenticated projected budget/status endpoints and working comparison controls; hardware remains visibly blocked |
| Unit/integration/browser tests | Real arithmetic and read boundaries; explicit HTTP doubles for malformed/injected serving output and SSE parsing, never represented as GPU evidence |

Public upstream API metadata reports **30,532,122,624 BF16 parameters** at revision
`b2cff646eb4bb1d68355c01b18ae02e7cf42d120`. The hash-checked config reports 48 layers,
4 KV heads, head dimension 128 and native 262,144 context, without sliding attention
or RoPE extension. Apache-2.0 model card/license was inspected. All experts remain
resident in this budget. See ADR 0009 and source URLs in model metadata.

The real registry lookup resolved AMD's published
`rocm7.0.0_vllm_0.11.2_20251210` tag to
`sha256:e7f02dd2ce3824959658bc0391296f6158638e3ebce164f6c019c4eca8150ec7`.
`phase6-image-metadata.txt` preserves actual registry output. This confirms image
availability/identity, not installed runtime versions or execution compatibility.
No multi-gigabyte GPU image, model weights or GPU runtime was installed locally.

## Executed commands and evidence

```powershell
.venv/Scripts/python -m pytest -q tests/unit/test_inference_budget.py tests/integration/test_inference_client.py tests/integration/test_inference_benchmark.py tests/integration/test_api.py
.venv/Scripts/python tools/check_cloud_manifest.py
.venv/Scripts/python tools/gpu_memory_budget.py
.venv/Scripts/python tools/probe_inference.py
.venv/Scripts/python tools/benchmark_inference.py
.venv/Scripts/python tools/dev.py start
docker compose --env-file .env -f infra/local/compose.yaml up --detach --wait --wait-timeout 180
.venv/Scripts/python tools/dev.py check
```

Focused suite passed **29 tests** (`phase6-focused-tests.txt`). The final full
gate passed **203 Python / 3 CTest / 8 Chromium**, two Node tests, lints/types,
contract/fixture drift, dependency/secret audits, manifest render and actual local
storage/HTTP/SSE/cross-language checks (`phase6-checks.txt`). Browser axe and
mobile checks passed; the memory projection panel was visually inspected. Cloud Compose render
and policy checks passed with a non-secret fixture, without deployment or image
pull. The local startup encountered a dependency wait timeout while edge became
healthy; the subsequent up/wait command confirmed all six services healthy.
The first full gate caught a missing cloud launcher in the QA image (202 passed,
one failed). Adding the cloud source to QA repaired it; the failed log is retained
as `phase6-initial-gate-failure.txt`. After the benchmark environment/profile
addition, manifest rendering and the stream-collector regression passed again.

Memory projections, not measured HBM:

| BF16, native context | Weights | KV | Base before overhead |
|---|---:|---:|---:|
| 1 sequence | 56.8705 GiB | 24 GiB | 80.8705 GiB |
| 2 sequences | 56.8705 GiB | 48 GiB | 104.8705 GiB |

Both defined unquantized cases exceed an 80-GiB capacity before overhead.
The default assumptions add 12 GiB runtime, 4 GiB temporary activations, 8 GiB
fragmentation and 4 GiB other buffers. Batch two total is **132.8705 GiB**.
Against a conservative 192,000,000,000-byte capacity (178.8139 GiB), projected
headroom is 45.9434 GiB. No real OOM or successful MI300X allocation was performed.
The UI separately labels its 192-GiB comparison; decimal GB and binary GiB differ.
FP8 halves projected KV bytes only; runtime compatibility and scale overhead are
not verified, and weights are not silently quantized.

## Required live gates — not passed

The user will provide MI300X access later. `phase6-inference-probe.json` and
`phase6-inference-benchmark.json` report blocked; the latter has an empty measured
rows array. There are **no invented driver versions, GPU timings, HBM peaks,
prefill/decode rates or true 200K successes**. An offline template returns null
token/latency fields and has no model/executor authority.

Still required: authorized provisioned host, observed MI300X device/usable memory,
ROCm/driver/vLLM versions, runtime/image security review, compatible device groups,
actual model load, wrong/missing-key denial, verified TLS ingress, authenticated
laptop request/response, 8K/32K/128K/200K+ runs where supported, and device/engine
metrics including prefill, decode and peak HBM. Network TTFT/wall time are separate
from engine-only metrics. Repetitive long input is not reasoning-quality proof.

No remote resource, deployment, enterprise mutation, passkey or release gate has
been waived. Subsequent phases and final release remain incomplete. The current
ordered external gate must stay visible until real access/evidence arrives.
