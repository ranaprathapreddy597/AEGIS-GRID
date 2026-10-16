# Provisioned MI300X path — not deployed or verified here

The user will provide MI300X access later. Do not run these deployment steps on
the laptop or claim the image has been validated on a GPU. See ADR 0009.

Before launch, obtain an expressly authorized Linux MI300X host with compatible
ROCm 7.0 driver/device nodes and image/runtime support. Configure a distinct
INFERENCE_API_KEY in a protected local environment; do not share it in chat.
Confirm video/render group mapping on the actual host. Repository instructions
currently prohibit external deployments/writes; obtain authorization for an actual
cloud deployment before executing a deployment command there.

The recipe is `mi300x.compose.yaml`. It pins both image and model revision, starts
at 8K / one sequence, and binds host loopback. `serve.py` refuses device/runtime
mismatches. Render without deployment using `python tools/check_cloud_manifest.py`.
The render check passes a non-secret test fixture, never displays actual config,
does not pull the image and cannot prove runtime compatibility.

Once provisioned and deployment is authorized:

1. Inspect the actual driver and provisioned service compatibility. Use the supplied
   `probe_device.py` in the selected image/host, preserving actual observed output.
2. Start the serving recipe on the authorized host at 8K first. Confirm its API
   rejects missing/wrong authentication. Confirm no bearer key appears in process
   arguments, access logs or saved reports.
3. Configure a verified HTTPS ingress and firewall to host loopback. Do not expose
   port 8000 publicly. Keep credentials separate from the simulator/monitoring keys.
4. Set `INFERENCE_BASE_URL` and `INFERENCE_API_KEY` in the laptop's ignored `.env`.
   Run `python tools/probe_inference.py`; a successful serving path is still not
   hardware attestation. Pair it with the device/runtime and image/model logs.
5. After measuring an 8K baseline, test increasing context/concurrency. Run
   `tools/benchmark_inference.py` in a configured environment with the pinned
   tokenizer available (the selected cloud image contains Transformers; it is not
   installed as a heavyweight laptop dependency). The opt-in `benchmark` Compose
   profile mounts only tools/inference/contracts read-only, not the repo .env,
   and takes inference settings from environment. Its actual image/package
   compatibility remains part of the pending provisioned-host check. Record device-wide HBM samples
   and engine metrics separately. Do not infer engine prefill/decode from HTTP wall
   time. Preserve OOM/unsupported failures rather than manufacturing success rows.

The default memory projection assumes 12 GiB runtime + 4 GiB activations + 8 GiB
fragmentation + 4 GiB other buffers. These reserves are assumptions, not measured
workspace sizes. Actual available KV blocks, dtype support and admission control
must be observed before enabling 200K+ contexts or multiple concurrent sequences.
No deployment automatically expands context, retries charges or changes safety.
