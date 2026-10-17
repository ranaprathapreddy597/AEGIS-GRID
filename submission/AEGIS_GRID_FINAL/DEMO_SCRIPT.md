# AEGIS//GRID 2.0 — Three-Minute Demonstration Script

> **Video File**: `submission/AEGIS_GRID_FINAL/DEMO_VIDEO.mp4`  
> **Target Duration**: Exactly 180 seconds (03:00)  
> **Environment**: Isolated clean-source container export, `http://localhost:8180`  
> **Execution Tool**: `tools/run_demo.mjs` (Automated Playwright Chromium capture)

---

## Scene-by-Scene Walkthrough & Narration

### Scene 1: Healthy Factory Baseline & Telemetry Ingestion (0:00 – 0:30)
- **Time**: 0:00 – 0:30 (30 seconds)
- **UI Route**: `/` (Industrial Command Center Overview)
- **Screen State**:
  - Live six-cell digital twin dashboard rendering operational temperatures (33°C – 41°C), coolant flow rates (~0.28 kg/s), and loop pressure (100 kPa).
  - Telemetry gauges updating via authenticated Server-Sent Events (SSE).
  - Observed-only 60-second thermal forecast charts displaying nominal trajectories with heuristic error bands.
- **Voiceover Narration**:
  > *"Welcome to AEGIS//GRID 2.0, the autonomous industrial immune system developed for AMD ACT III: Track 1 Intelligent Industry. Here in the live command center, we monitor a precision six-cell manufacturing plant with shared cooling and electrical loops, simulated by our deterministic C++ digital twin. Every cell's thermal state and fluid dynamics are governed by coupled conservation laws. Notice our predictive intelligence panel: using multi-telemetry energy estimation, we forecast temperatures 60 seconds into the future, distinguishing between simulated ground truth, observed sensors, and AI predictions."*
- **Provenance / Mode**: Genuinely Live C++ Twin Telemetry via SSE.

---

### Scene 2: Stealth Sensor Spoofing & Edge Physics Anomaly (0:30 – 1:15)
- **Time**: 0:30 – 1:15 (45 seconds)
- **UI Action**: Operator triggers injected catastrophic fault (`scenario-010`: Cell 3 coolant choke + sensor clamping).
- **Screen State**:
  - Cell 3 temperature sensor is clamped to `min(T, 38°C)`. Conventional SCADA dashboard shows green status.
  - Edge Physics Sentinel triggers: First-Law energy observer residual jumps from $0.05^\circ\text{C}$ to $14.2^\circ\text{C}$.
  - Alert banner turns Red: *"🚨 STEALTH ANOMALY DETECTED: Heat flux exceeds dissipation capacity. Possible sensor spoofing."*
  - Cyclic LangGraph activates in cloud intelligence panel; states transition: `Sentinel` $\to$ `Evidence Collection` $\to$ `Causal Detective`.
- **Voiceover Narration**:
  > *"Now, we inject a catastrophic stealth failure into Cell 3: a physical coolant restriction combined with a spoofed temperature sensor clamped at 38°C. A standard threshold alarm sees 38 degrees and stays completely silent while the machine physically burns. But AEGIS//GRID's edge sentinel, running on local AMD Ryzen AI, calculates physical energy residuals in real-time. Because thermal input cannot escape through the restricted flow, the physics residual trips an instant anomaly alert without needing any cloud latency."*
- **Provenance / Mode**: Live C++ Twin Injection + Live Edge Physics Sentinel.

---

### Scene 3: AMD Token Factory Reasoning & Pinecone Knowledge Retrieval (1:15 – 1:55)
- **Time**: 1:15 – 1:55 (40 seconds)
- **UI Route**: `/investigation` (LangGraph War Room)
- **Screen State**:
  - LangGraph node execution visualization: Causal Detective ranks hypotheses (78% degraded pump, 75% overload, 92% coolant restriction).
  - Pinecone Dual Retrieval pane displays cited OEM manuals and licensed NIST references with exact page and table hashes.
  - Contradictory manual conflict banner: *"OEM Bulletin B conflicts with Master Manual (70°C vs 95°C limit). Direct autonomous action blocked."*
  - Counterfactual Strategy Explorer compares 3 recovery candidates: Safe Stop (6-cell cooldown), Load Shedding, and Flow Boost.
- **Voiceover Narration**:
  > *"The incident routes to our cloud intelligence layer, powered by hosted AMD Token Factory vLLM inference and LangGraph. The Causal Detective ranks competing hypotheses against 1,235 synthetic plant vectors and 103 licensed OEM and NIST references in Pinecone. When an unverified manual asserts an unsafe 95°C limit, our grounding detects the contradiction and strictly refuses unverified execution. Our counterfactual explorer runs parallel rollouts in isolated C++ twin copies, showing the operator exact predicted cooling times, energy consumption, and lost production."*
- **Provenance / Mode**: Real LangGraph Checkpoint + Preserved Hosted AMD Proof Replay (labeled clearly).

---

### Scene 4: Cryptographic WebAuthn Ceremony & Independent Execution (1:55 – 2:35)
- **Time**: 1:55 – 2:35 (40 seconds)
- **UI Action**: Operator selects "Safe Stop Coordinated Cooldown" and initiates authorization ceremony.
- **Screen State**:
  - Immutable Action Proposal modal appears showing exact diff, action ID, and SHA-256 plan digest.
  - WebAuthn ceremony modal: Virtual CTAP2 authenticator generates ES256 hardware assertion over server challenge.
  - Server verifies assertion, issues short-lived Ed25519 single-use capability (60s TTL).
  - Independent executor verifies capability against hard safety shield limits, initiates coordinated valve and load shutdown.
- **Voiceover Narration**:
  > *"Because an AI model must never hold autonomous execution authority over industrial machinery, LangGraph halts at a durable checkpoint. To execute the recommended safe-stop, the human operator must complete a FIDO2 WebAuthn passkey ceremony. The hardware authenticator cryptographically signs a challenge bound directly to the SHA-256 digest of the proposed plan. If a malicious attacker tampered with a single parameter in transit, the signature would fail. The server issues a single-use Ed25519 token, and our air-gapped executor applies the coordinated cooldown."*
- **Provenance / Mode**: Live Server WebAuthn Verification + Chromium Virtual CTAP2 Passkey.

---

### Scene 5: Cooldown Verification, Audit Receipt & Closing Results (2:35 – 3:00)
- **Time**: 2:35 – 3:00 (25 seconds)
- **UI Route**: `/receipts` and `/benchmarks`
- **Screen State**:
  - Cell 3 temperature actively drops from 68.9°C to 33.4°C under coordinated coolant routing.
  - Immutable Audit Receipt displayed: SHA-256 digest binding pre/post cell temperatures, plant state version hash, user identity, and timestamp.
  - Final metrics pane: 73.0% held-out diagnosis recall, 100% precision, 0 confounder false alarms, 25-second forecast lead time.
- **Voiceover Narration**:
  > *"Within 120 simulated seconds, Cell 3 temperature drops safely back to 33 degrees. An immutable audit receipt is atomically sealed into MongoDB, binding pre- and post-temperatures, plant state hashes, and the operator's cryptographic signature. Across our held-out test suites, AEGIS//GRID delivers 73% diagnostic recall with 100% precision and zero false alarms on healthy operating variations. AEGIS//GRID: physics-first resilience, AMD hosted intelligence, and cryptographic safety for the future of intelligent industry."*
- **Provenance / Mode**: Live C++ Twin Cooldown + Verified Persistent Receipt Ledger.

---

## Contingency & Fallback Matrix for Live Demonstrators

| Scenario | Primary System | Fallback / Contingency |
|---|---|---|
| **Hosted AMD API Latency / Quota** | Live AMD Token Factory REST | Deterministic local reasoning adapter (100% contract-compliant offline replay) |
| **Pinecone Network Disconnection** | Live Pinecone vector index query | Local FAISS vector index with identical 1,235 + 103 embeddings |
| **Hardware Passkey Unavailable** | Physical USB FIDO2 Key | Built-in Chromium Virtual CTAP2 Authenticator (`approval.spec.ts`) |
| **Browser Video Playback** | Pre-rendered H.264 MP4 | Real-time Playwright automated replay via `pnpm exec playwright test` |
