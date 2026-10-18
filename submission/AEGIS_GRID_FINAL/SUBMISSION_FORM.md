# AEGIS//GRID 2.0 — Official Hackathon Submission Form
**AMD Developer Hackathon ACT III — Track 1: Intelligent Industry**  
**Hosted on lablab.ai**

---

## 1. Project Title
**AEGIS//GRID 2.0: The Autonomous Industrial Immune System**

---

## 2. Short Description (<= 255 characters)
> AEGIS//GRID 2.0 is an autonomous industrial immune system combining a 6-cell coupled C++ digital twin, AMD hosted intelligence, dual Pinecone retrieval, and WebAuthn cryptographic hardware authorization to detect stealth faults and execute safe stops.

*(Character count: 247 / 255 max)*

---

## 3. Long Description (>= 100 words)
Modern industrial automation faces an existential cybersecurity and operational challenge: stealth physical anomalies that deceive conventional threshold-based SCADA alarms while machinery overheats, alongside ungrounded AI agents that risk proposing catastrophic control actions. 

AEGIS//GRID 2.0 introduces the world’s first autonomous industrial immune system for critical manufacturing. Rather than trusting raw telemetry or granting unchecked actuation authority to large language models, AEGIS//GRID enforces an asymmetric zero-trust architecture across four decoupled layers:
1. **Local Physical Grounding**: A deterministic C++20 factory digital twin modeling six coupled manufacturing cells governed by non-linear thermal, cooling flow, and electrical conservation ODEs. A local First-Law energy observer continuously calculates physical residuals, instantly detecting clamped or spoofed temperature sensors even when observed telemetry appears normal.
2. **AMD-Powered Multi-Agent Intelligence**: A cyclic LangGraph orchestration pipeline powered by AMD Token Factory hosted inference (evaluating DeepSeek-R1 and Qwen backends) and dual-namespace Pinecone vector retrieval (1,235 synthetic plant vectors and 103 licensed OEM/NIST documents). The pipeline executes a minimax adversarial tournament, pitching Blue Team recovery candidates against Red Team failure injections to discover hidden failure modes before human presentation.
3. **Cryptographic Human-in-the-Loop Ceremony**: The system halts at durable checkpoints. Operators authorize actions via FIDO2/CTAP2 WebAuthn hardware passkeys signing an unpredictable challenge bound to the exact SHA-256 digest of the proposed plan. Any in-flight modification invalidates the signature.
4. **Independent Execution Shield**: An air-gapped executor verifies a single-use Ed25519 capability token against hard plant safety interlocks. Upon coordinated cooldown, an atomic cryptographic audit receipt binds pre/post cell temperatures, state version hashes, and operator identity to an immutable append-only ledger.

On held-out native evaluation cases, AEGIS//GRID achieves 73.0% diagnostic recall with 100% precision, zero false alarms across 30 operating confounders, and a 25-second predictive warning lead time. All code, contracts, and demo proof are open, reproducible, and mathematically verified.

*(Word count: 326 words / >= 100 words required)*

---

## 4. Submission Metadata & Tags

- **Primary Track**: Track 1: Intelligent Industry
- **Technology Tags**:
  `AMD ROCm`, `vLLM`, `LangGraph`, `React`, `TypeScript`, `C++20`, `Python`, `FastAPI`, `WebAuthn`, `FIDO2`, `Pinecone`, `Docker`, `Redis`, `MongoDB`, `CMake`
- **Category Tags**:
  `Intelligent Industry`, `Industrial AI`, `Cybersecurity`, `Digital Twin`, `Safety & Resilience`, `Predictive Maintenance`

---

## 5. Problem Statement
High-value manufacturing facilities (semiconductor fabrication, battery gigafactories, precision aerospace machining) suffer billions in unplanned downtime due to thermal imbalances and sensor anomalies. Conventional DCS/SCADA systems rely on static thresholds that fail against stealth sensor bias or localized coolant chokes. Furthermore, emerging generative AI solutions introduce severe hallucination and prompt-injection risks if granted direct actuation privileges.

---

## 6. Technical Innovation & Architecture
AEGIS//GRID completely separates **advisory intelligence** from **execution authority**:
- **Deterministic Conservation Laws**: Thermal dynamics governed by $C_i \frac{dT_i}{dt} = P_i - h_i(q_i)(T_i - T_{coolant}) + \text{coupling}_i$.
- **Physics Energy Residual Sentinel**: $R(t) = |Q_{in} - Q_{out} - C \Delta T|$ detects unmanifested sensor spoofing without cloud latency.
- **Minimax Adversarial Tournament**: C++ digital twin runs parallel candidate rollouts across safe-stop, load shedding, and flow boost strategies, exposing worst-case trade-offs and rejecting physically infeasible actions.
- **Hardware-Bound WebAuthn Ceremony**: FIDO2 challenge bound to the canonical action proposal SHA-256 digest; server verifies ES256 assertion.
- **Air-Gapped Single-Use Execution**: Independent Node.js executor verifies Ed25519 token, enforces hard operating bounds (70°C max cutoff), and records an atomic SHA-256 receipt.

---

## 7. AMD Technology Integration
- **AMD Token Factory Hosted Inference**: Direct REST/SSE integration with hosted ROCm/vLLM endpoints running DeepSeek-R1 and Qwen reasoning models, evaluating 2,639 structured tokens across diagnostic and planning nodes.
- **AMD Instinct MI300X Memory Profiling**: Complete analytical GPU memory budget modeling (`tools/gpu_memory_budget.py`). Proves that a 30.5B BF16 model with 256K context requires 104.81 GiB base memory at batch 2, causing OOM on 80 GiB accelerators while running comfortably with 87 GiB headroom on the 192 GB MI300X.
- **Edge Deployment Target**: Architecture designed for AMD Ryzen AI NPU/CPU local acceleration, running the C++ sentinel and fallback controller locally with sub-millisecond reaction times.

---

## 8. Measured Quantitative Results
All metrics evaluated on untouched held-out datasets with zero seed or temporal window leakage:
- **Fault Diagnosis**: **73.0% Recall** (73/100), **100.0% Precision** (0 FP), **80.0% Accuracy** ($z = 3.74, p < 0.001$). Outperforms legacy baseline (70% recall, 75% accuracy).
- **Healthy Operating Confounders**: **0 False Positives** across 30 complex operating load variations (100% correct abstention).
- **Thermal Forecasting**: **70.0% Hazard Recall** (14/20 windows), **66.7% Precision**, **F1 Score 0.683** (4.1x gain over baseline), **0.48% False Alarm Rate** (7/1,455 negative windows), **25.0s Median Warning Lead Time**.
- **Automated Regression Gates**: **398 Python / 3 CTest / 35 Node / 17 Playwright Chromium checks PASS** across main repository and isolated clean-source export.
- **Clean Three-Minute Demo**: **180.0125 seconds** isolated execution with screen recording and cryptographic proof verified.

---

## 9. Business Value & Market Opportunity
- **Target Customers**: Semiconductor foundries, EV battery gigafactories, chemical synthesis plants.
- **Economic Value**: Unplanned downtime in precision manufacturing costs ~$22,000/minute. A 25-second predictive warning enables coordinated load shedding, avoiding emergency line trips.
- **Insurability**: Atomic SHA-256 audit receipts provide verifiable non-repudiation required for cyber-physical insurance riders.

---

## 10. Honest Boundaries & Physical Limitations
- **Simulation Containment**: All execution is strictly confined to the isolated C++ digital twin. No physical I/O or live plant connections exist.
- **Observability Limits**: Family 1 sensor clamping produces $\le 0.07^\circ\text{C}$ residual under nominal load; the system honestly abstains until heat builds.
- **Hardware Blockers**: Dedicated physical MI300X hardware instance, live Evolus MCP servers, and production safety certification remain marked as EXTERNALLY BLOCKED.

---

## 11. Links & Submission Assets

| Submission Requirement | Resource / Location | Status |
|---|---|---|
| **Public GitHub Repository** | `https://github.com/ranaprathapreddy597/AEGIS-GRID` | VERIFIED REPO |
| **Interactive Application URL** | `http://localhost:8180` (Local) / Docker Compose | READY FOR LOCAL EVAL |
| **Three-Minute Video** | `submission/AEGIS_GRID_FINAL/DEMO_VIDEO.mp4` | DELIVERED (4.5 MB, 180s) |
| **Slide Pitch Deck (PDF)** | `submission/AEGIS_GRID_FINAL/PITCH_DECK.pdf` | DELIVERED (12 Slides) |
| **16:9 Cover Image** | `submission/AEGIS_GRID_FINAL/COVER_IMAGE.png` | DELIVERED (1920x1080) |
| **Architecture Diagram** | `submission/AEGIS_GRID_FINAL/ARCHITECTURE_DIAGRAM.svg` | DELIVERED (SVG & PNG) |
| **Complete ZIP Archive** | `submission/AEGIS_GRID_FINAL.zip` | GENERATED |
