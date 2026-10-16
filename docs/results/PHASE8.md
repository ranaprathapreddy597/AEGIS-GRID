# Phase 8 report — 2026-10-16, Asia/Calcutta

Status: local gate PASS. MI300X/Evolus/Pinecone live gates remain BLOCKED.
Previous local phase commit: e3251d0.

Implemented real finite minimax recovery optimization over eleven control vectors
and 37 complete native-state priors. C++ rollout evaluates all substeps on a private
copy, enforces hard constraints before economic weights, and records actual
production/energy/downtime/wear. Artifacts bind policy, uncertainty seeds/hashes,
native binary, source state and deterministic results. Authenticated analysis and
content-hash replay use append-only scoped Mongo storage. LangGraph consumes the
search and independent shield feedback; React shows actual tournament/timelines.
No protected operational write or physical I/O was added. See ADR 0011 for bounds.

The first real optimizer test passed native nonmutation/replay and OOD tests, but
found every stop incorrectly failed flow settling. Inspection exposed a native
off-by-one: checking during the tenth frame began at elapsed 9.05 s. The condition
now checks elapsed time ≥10 seconds, matching the preregistered ramp interval.
The failure is retained in phase8-initial-failure.txt; no thermal/flow bound was
relaxed. Every productive severe-blockage candidate and the planted unsafe plan
had actual counterexamples. The repaired native tests pass, including identical
optimizer replay and rejection of a tampered artifact or hot out-of-domain state.

Actual network-none profile (`phase8-profile.json`), 2-CPU/512-MiB container:
409 rollouts / 4,908,000 native physics substeps in **1.4994 s**, 272.78 rollouts/s,
86.05 MiB peak process RSS. This is one development incident, excluding Docker,
WSL and other services; no GPU/NPU/model inference performance is implied.
Selected zero-load/pump-.7 is feasible in all 37 cases. The planted unsafe vector
fails all 37, despite lower objective than stop. All productive grid controls fail
at least one severe branch case. Hard constraints take precedence over cost.

Paired actual 600-second snapshot futures: unmitigated peak **92.8155 °C**,
2.1386 kWh, 47.0720 synthetic production units, thermal+flow violations;
intervention peak **41.1321 °C**, .30345 kWh, .46874 units, **591 s downtime**,
no violations. Most production is deliberately lost to preserve the finite robust
envelope. This is model counterfactual evidence, not measured plant recovery or
real economic savings. The independent edge policy additionally requires pump 1
and rejects the optimum in the graph; another cycle preserves the emergency vector.

Final full gate: **212 Python / 3 CTest / 10 Chromium / 2 Node tests passed**.
Types, lints, generated schemas/TypeScript, fixtures, manifest, dependency/secret
audits, actual HTTP/SSE/cross-language boundaries and scoped storage checks pass.
Browser proof includes three graph cycles, an actual API restart with unchanged
analysis artifact, Red refusal, desktop/mobile recovery captures and zero axe
violations. The two recovery captures were visually inspected. The image source
and profiled native binary match the recorded content hash. Historical Phase 7
integration documentation was normalized to UTF-8 after Windows encoded two new
dashes differently; authoritative supplied prompts are unchanged.

Commands:

```powershell
.venv/Scripts/python tools/dev.py start
.venv/Scripts/python tools/dev.py check
# CPU-only / network-none QA container, 2 CPUs, 512 MiB:
# python tools/profile_optimization.py --output /out/phase8-profile.json
```

Next gate: Phase 9 full cryptographic authorization, only after this local phase
is tested and committed. No approval, live provider success or release is claimed.
