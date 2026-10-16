# ADR 0009: hardware proof is separate from deployable configuration

Accepted 2026-10-16. Phase 5 local gate commit `5513a27`; provider gates remain blocked.

Use Qwen/Qwen3-Coder-30B-A3B-Instruct, Apache-2.0, pinned upstream revision
`b2cff646eb4bb1d68355c01b18ae02e7cf42d120`. Public upstream API metadata reports
30,532,122,624 BF16 parameters. Config has 48 layers, four KV heads, head dimension
128, 32 query heads, full attention with no sliding window and native context
262,144. The model is MoE; all experts' weights reside in this BF16 budget,
regardless of the smaller per-token active parameter count. Metadata/config were
actually fetched from upstream and the config is hash-checked. No weights were
downloaded and no local/cloud inference was performed for that metadata check.

`budget.py` computes weights + dense GQA KV + explicit assumed runtime reserve,
temporary activations, fragmentation and other buffers. It supports BF16/FP8 KV
projections; FP8 kernel compatibility, quality and scale overhead are unverified.
Weights stay BF16 in both cases. No quantized model is substituted silently.

The CLI defaults to 192,000,000,000 bytes as a conservative decimal interpretation
of advertised 192 GB. The UI explicitly compares 80 GiB and 192 GiB. These are
different capacities; actual usable memory must come from device telemetry.
Single-sequence 262,144-token BF16 weights+KV exceed 80 GiB even before overhead.
Two sequences need 48 GiB KV plus all resident weights and runtime overhead.
Projected headroom is not an observed deployment success or OOM experiment.
This does not prove that every 200K workload needs 192 GB: quantization, CPU
offload, multiple GPUs, alternative models and shorter batches change the budget.

AMD's published ROCm 7.0/vLLM 0.11.2 image was inspected through registry metadata.
Its digest is pinned in `infra/cloud/mi300x.compose.yaml`. Tag and registry digest
are real; installed versions and compatibility on a provisioned GPU are not yet
observed. The image is not downloaded onto this laptop. Host driver, device nodes,
video/render groups, shared memory and container compatibility need actual probing.
The entrypoint refuses observed non-MI300X/non-ROCm-7.0/non-vLLM-0.11.2 execution.

Cloud Compose is a render-tested deployment recipe only. It publishes serving
on loopback and requires a distinct strong VLLM_API_KEY from environment. It does
not put the key in arguments, enable remote model code, grant privileged mode,
mount Docker sockets or publish an unauthenticated public service. A separately
provisioned TLS gateway/firewall is required before laptop access. No deployment,
gateway provisioning or external write has occurred. Image/runtime supply-chain
and security posture must be reviewed before deployment; old compatibility pins
are not a claim of current production hardening.

The serving client accepts only an authorized HTTPS origin, disables redirects
and proxy inheritance, bounds response size and timeouts, validates model identity,
structured opinion and token accounting, and rejects tool calls/truncation/commands.
There is no automatic paid retry. Model opinions have zero execution authority.
The offline backend is a deterministic abstention template, not an LLM or GPU
simulation. Token counts and latency are null when not measured.

The benchmark collector targets exact input-token counts at 8K, 32K, 128K, 204,800
and 262,016 (leaving 128 output tokens in the native context). It uses the pinned
tokenizer and the documented serving completion/SSE API, records actual usage,
network TTFT and end-to-end throughput, and keeps engine prefill/decode and peak
HBM null pending device metrics. Repetitive synthetic prompts are not evidence of
long-context reasoning quality. A successful HTTP request alone cannot attest
MI300X hardware. Do not label these missing metrics measured or the live gate passed.

Primary sources inspected:

- [Upstream model config](https://huggingface.co/Qwen/Qwen3-Coder-30B-A3B-Instruct/blob/b2cff646eb4bb1d68355c01b18ae02e7cf42d120/config.json)
- [Model card](https://huggingface.co/Qwen/Qwen3-Coder-30B-A3B-Instruct)
- [vLLM 0.11.2 GPU installation](https://docs.vllm.ai/en/v0.11.2/getting_started/installation/gpu/)
- [Serving API](https://docs.vllm.ai/en/v0.11.2/serving/openai_compatible_server/)
- [API key environment variable](https://docs.vllm.ai/en/v0.11.2/configuration/env_vars/)
- [AMD published image matrix](https://www.amd.com/en/developer/resources/rocm-hub/ai-cloud-development/performance-results.html)
