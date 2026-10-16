# Inference boundary

Current hosted integration: the bounded AMD Token Factory client supplies strict
diagnostic and planning opinions to the real LangGraph via explicit adapter
injection. Route order is DeepSeek, GLM, Qwen. Auth/quota stops routing; timeout or
validation failures fall back or abstain. It never has execution authority.
See [live knowledge workflow](../../docs/LIVE_KNOWLEDGE.md) and
[actual results](../../docs/results/LIVE_INTEGRATION.md).
Dedicated MI300X hardware acceptance remains blocked.

Not implemented in Phase 1. Phase 6 requires device/version probing, verified model
metadata, authenticated TLS connectivity and real benchmark evidence. No model
endpoint or MI300X telemetry is fabricated.
