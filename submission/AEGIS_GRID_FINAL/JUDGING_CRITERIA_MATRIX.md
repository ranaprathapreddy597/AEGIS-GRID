# AEGIS//GRID 2.0 — Judging Criteria Alignment Matrix

> **Event**: AMD Developer Hackathon ACT III — Track 1: Intelligent Industry  
> **Platform**: lablab.ai  
> **Date**: 2026-10-17

---

## Evaluation Criteria Mapping

| Evaluation Dimension | Weight / Focus | Implemented AEGIS//GRID Feature | Demo Scene | Evidence File | Measured Outcome | Known Weakness / Boundary | Verification Status |
|---|---|---|---|---|---|---|---|
| **1. Technical Application & Physics Coupling** | Critical (Track Core) | Native C++20 digital twin with coupled thermal and fluid ODEs; First-Law energy balance observer | Scene 1 (0:00–0:30) & Scene 2 (0:30–1:15) | `cpp/digital-twin/`, `services/edge/`, `docs/results/sprint-ai-optimized.json` | 3/3 CTests Pass; 100% anomaly detection on spoofed sensors; 73.0% diagnostic recall | Model calibrated to synthetic 6-cell line, not physical OEM hardware | **VERIFIED COMPLETE** |
| **2. AMD Technology Integration** | Critical (Sponsor Core) | AMD Token Factory hosted inference; ROCm/vLLM endpoint; MI300X 192GB memory profiling | Scene 3 (1:15–1:55) | `services/inference/`, `tools/gpu_memory_budget.py`, `docs/results/CLOUD_INTEGRATION.md` | 2,639 evaluated tokens; proven MI300X 87GB headroom at batch 2 (256K context) | Dedicated bare-metal MI300X instance blocked; hosted endpoint evaluated | **VERIFIED COMPLETE** |
| **3. Originality & Architectural Innovation** | High (Competitive Edge) | Asymmetric Zero-Trust control: LangGraph advisory reasoning decoupled from WebAuthn hardware passkeys | Scene 4 (1:55–2:35) | `services/executor/`, `apps/web/src/features/approval/`, `tests/e2e/approval.spec.ts` | AI cannot self-authorize; WebAuthn signs SHA-256 plan digest; single-use Ed25519 token | Evaluated with Chromium Virtual CTAP2 authenticator in automated gates | **VERIFIED COMPLETE** |
| **4. AI Quality & Grounding** | High (Safety Critical) | Grounded causal diagnosis; contradiction rejection; 1,235 + 103 Pinecone dual-vector retrieval | Scene 3 (1:15–1:55) | `services/agents/aegis_agents/quality.py`, `data/cloud-knowledge-manifest.json` | 100% precision on held-out cases; 0 false alarms on 30 healthy operating confounders | Honestly abstains on Family 1 unmanifested clamp (residual <= 0.07°C) | **VERIFIED COMPLETE** |
| **5. Predictive Forecasting Capability** | Medium (Industrial Impact) | Multi-telemetry energy estimation predicting thermal runaway 60s ahead | Scene 1 (0:00–0:30) & Scene 5 (2:35–3:00) | `services/agents/aegis_agents/forecasting.py`, `docs/results/sprint-forecast-optimized.json` | 70.0% hazard recall (+60 pp gain), F1 0.683 (4.1x gain), 25s median lead time | Clamped sensors require multi-second energy integration | **VERIFIED COMPLETE** |
| **6. Business Value & Industrial Feasibility** | High (Impact & Market) | High-value targeting (semiconductor, battery gigafactories); downtime economics ($22k/min) | Slide Deck (Slides 10 & 11) | `submission/AEGIS_GRID_FINAL/BUSINESS_CASE.md` | Actionable 25s lead time prevents catastrophic line trips; audit receipts satisfy insurance | Requires on-premise industrial calibration service during pilot rollout | **VERIFIED COMPLETE** |
| **7. Software Quality & Reproducibility** | High (Engineering Rigor) | Full regression gate: C++, Python, Node, Playwright; clean source export; zero secrets | All Scenes & Clean Script | `docs/results/sprint-optimized-clean-check-proof.json`, `tools/check_clean_source.py` | 453 checks pass (398 Py, 3 CTest, 35 Node, 17 Browser); 899 files scanned 0 secrets | High Docker build caching required for fast cold-export validation | **VERIFIED COMPLETE** |
| **8. Presentation & Delivery Completeness** | Medium (Submission Polish) | React command center, 3-minute video (H.264), 12-slide PDF pitch deck, 16:9 cover image | Entire Package | `submission/AEGIS_GRID_FINAL/` | 180.0125s demo video generated; 12-slide PDF created; 1920x1080 cover created | Real human voiceover optional; complete narration script provided | **VERIFIED COMPLETE** |

---

## Hackathon Platform Verification (lablab.ai Guidelines)

| Platform Requirement | Guideline Specification | AEGIS//GRID Implementation | Status |
|---|---|---|---|
| **Short Description Length** | Strictly $\le 255$ characters | 251 characters | **READY** |
| **Long Description Length** | Strictly $\ge 100$ words | 294 words | **READY** |
| **Cover Image Format** | PNG / JPG, recommended 16:9 | PNG, 1920x1080 (16:9 ratio) | **READY** |
| **Presentation File** | PDF format | `PITCH_DECK.pdf` (12 slides) | **READY** |
| **Demo Video** | MP4 format, $\le 5$ minutes | `DEMO_VIDEO.mp4` (H.264, 3:00 duration) | **READY** |
| **Working Prototype** | Reproducible application | Docker Compose stack (`tools/dev.py start`) | **READY** |
| **IBM Bob Tool Report** | *Checked for relevance* | Verified as non-mandatory for AMD ACT III; honestly marked NOT APPLICABLE | **NOT APPLICABLE** |
| **Team Registration** | User registration on platform | Requires user's personal lablab.ai account credentials | **REQUIRES USER ACTION** |
