# Benchmark boundary

Phase 2 executes CPU physics rollouts for all 100 synthetic fixtures. See
`tools/profile_twin.py`, `docs/results/phase2-profile.json` and the sampled
observed/ground-truth trajectories. This measures local simulator cost and
reproducibility, with a simple threshold-deception check. No diagnosis/recovery
system or inference benchmark exists yet.

Phase 6 measures cloud inference if provisioned. Phase 12 evaluates detection,
diagnosis and recovery with held-out scenarios and uncertainty. Build duration
and screenshots are not inference performance evidence.
