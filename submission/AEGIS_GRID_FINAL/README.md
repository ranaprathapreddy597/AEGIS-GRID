# AEGIS//GRID 2.0: The Autonomous Industrial Immune System

> **AMD Developer Hackathon ACT III — Track 1: Intelligent Industry**  
> *A Physically Grounded, Asymmetric Zero-Trust Industrial AI Platform with C++ Digital Twins, AMD Hosted Reasoning, and Cryptographic WebAuthn Authorization.*

[![Full Regression Gate](https://img.shields.io/badge/Full%20Gate-398%20Python%20%7C%203%20CTest%20%7C%2035%20Node%20%7C%2017%20Playwright-00E676.svg)]()
[![Clean Demo Proof](https://img.shields.io/badge/Demo%20Duration-180.0125s%20PASS-00E5FF.svg)]()
[![Held-Out Diagnosis](https://img.shields.io/badge/Diagnosis-73.0%25%20Recall%20%7C%20100%25%20Precision-ED1C24.svg)]()
[![WebAuthn Security](https://img.shields.io/badge/Authorization-FIDO2%20%2F%20CTAP2%20ES256-FFB300.svg)]()

---

## 1. Executive Summary

In high-consequence precision manufacturing—from semiconductor lithography to EV battery cell formation—unplanned thermal failures cost tens of thousands of dollars per minute. Traditional SCADA/DCS systems rely on static thresholds that remain completely blind to **stealth sensor drift or spoofing**. Conversely, naive implementations of generative AI introduce catastrophic safety risks by granting large language models direct actuation privileges.

**AEGIS//GRID 2.0** solves this paradox by decoupling **advisory intelligence** from **execution authority**:
1. **Physical First Principles**: A deterministic C++20 six-cell factory digital twin models coupled non-linear heat flux and branch flows. A First-Law energy observer calculates physical residuals in real-time, catching clamped or spoofed sensors without relying on cloud models.
2. **AMD Token Factory Hosted Reasoning**: When an incident occurs, a cyclic LangGraph pipeline queries hosted AMD ROCm/vLLM endpoints (evaluating DeepSeek-R1 and Qwen) alongside dual-namespace Pinecone vector retrieval (1,235 synthetic plant vectors + 103 licensed OEM/NIST manuals).
3. **Adversarial Minimax Tournament**: Blue Team recovery candidates and Red Team failure injections are simulated inside parallel C++ twin copies, calculating exact predicted temperatures, downtime, and energy trade-offs.
4. **Asymmetric Cryptographic Gate**: AI models cannot self-authorize actions. The operator must complete an in-person FIDO2/CTAP2 WebAuthn ceremony signing a challenge bound to the exact SHA-256 digest of the proposed plan.
5. **Air-Gapped Independent Execution**: An isolated executor verifies an Ed25519 single-use capability token, enforces hard operating limits (70°C cutoff), and writes an atomic SHA-256 audit receipt binding state, temperatures, and operator identity to an immutable ledger.

---

## 2. System Architecture

```
+---------------------------------------------------------------------------------------------------+
|                                   AEGIS//GRID 2.0 ARCHITECTURE                                    |
+------------------------------------+--------------------------------------------------------------+
| 1. LOCAL FACTORY & EDGE TWIN       | 2. CLOUD INTELLIGENCE (AMD & GRAPH)                          |
|                                    |                                                              |
|   +----------------------------+   |   +------------------------------------------------------+   |
|   |  C++20 Digital Twin        |   |   |  Cyclic LangGraph Orchestrator                       |   |
|   |  • 6 Coupled Factory Cells |   |   |  • Causal Detective (Grounded Hypothesis Ranking)    |   |
|   |  • Thermal & Flow ODEs     |===|==>|  • Multi-Telemetry Energy-Balance Forecasting       |   |
|   |  • Injected Sensor Faults  |   |   |  • Blue Planner (Safe Counterfactuals)               |   |
|   +--------------+-------------+   |   |  • Red Adversary (Minimax Fault Tournament)          |   |
|                  |                 |   |  • Durable State Interrupt                           |   |
|                  v                 |   +--------------------------+---------------------------+   |
|   +----------------------------+   |                              |                               |
|   |  Edge Physics Sentinel     |   |          +-------------------+-------------------+           |
|   |  • Energy Balance Observer |   |          v                                       v           |
|   |  • Detects Clamped Sensors |   |   +----------------------+   +-------------------------------+   |
|   |  • Bounded Local Fallback  |   |   | AMD Token Factory    |   | Pinecone Dual-Vector DB       |   |
|   +----------------------------+   |   | • Hosted vLLM Model  |   | • 1,235 Plant Vectors         |   |
|                                    |   | • Strict Schemas     |   | • 103 Licensed OEM/NIST Refs  |   |
|                                    |   +----------------------+   +-------------------------------+   |
+------------------------------------+--------------------------------------------------------------+
                                     |
                                     | Action Proposal & Digest (SHA-256)
                                     v
+------------------------------------+--------------------------------------------------------------+
| 3. CRYPTOGRAPHIC HITL CEREMONY     | 4. AIR-GAPPED INDEPENDENT EXECUTOR                           |
|                                    |                                                              |
|   +----------------------------+   |   +------------------------------------------------------+   |
|   | React Industrial Command   |   |   | Independent Executor Gateway                         |   |
|   | • 6 Live Cell Trends       |   |   | • Verifies Ed25519 Single-Use Capability             |   |
|   | • Strategy Explorer        |   |   | • Enforces Hard Safety Interlocks (70°C Cutoff)      |   |
|   +--------------+-------------+   |   | • Air-Gapped from Physical Plant I/O                 |   |
|                  |                 |   +--------------------------+---------------------------+   |
|                  v                 |                              |                               |
|   +----------------------------+   |                              v                               |
|   | WebAuthn FIDO2 / CTAP2     |   |   +------------------------------------------------------+   |
|   | • ES256 Passkey Assertion  |===|==>| Cryptographic Audit Receipt                          |   |
|   | • Challenge Bound to Hash  |   |   | • Binds Pre/Post Temperatures & State Version Hash   |   |
|   | • Issues Ed25519 Token     |   |   | • Immutable Append-Only MongoDB Ledger               |   |
|   +----------------------------+   |   +------------------------------------------------------+   |
+------------------------------------+--------------------------------------------------------------+
```

---

## 3. Key Differentiators & Empirical Results

Evaluated against strict held-out synthetic and physical datasets with zero data leakage:

| Capability | Conventional SCADA | Generic LLM Agents | AEGIS//GRID 2.0 | Measured Evidence |
|---|---|---|---|---|
| **Fault Diagnosis Recall** | ~35% (static threshold) | ~50% (hallucinatory) | **73.0%** (73/100) | $z = 3.74, p < 0.001$ held-out gain |
| **Fault Diagnosis Precision** | High false alarms | Low (hallucinates) | **100.0%** (0 FP) | Zero ungrounded cause assertions |
| **Healthy Confounders** | Alarms on burst load | Alarms on burst load | **0 False Alarms** | 100% abstention across 30 cases |
| **Forecasting Hazard Recall** | 0% (reactive only) | Untrained on ODEs | **70.0%** (14/20) | Multi-telemetry energy estimation |
| **Warning Lead Time** | 0 seconds | Unbounded latency | **25.0s Median** | Actionable pre-trip intervention |
| **Actuation Authority** | Static relays | Unconstrained API | **Zero-Trust Gate** | WebAuthn + Ed25519 capability |
| **Audit Verification** | Plain text logs | No audit binding | **Atomic SHA-256** | Bound pre/post state hash |

---

## 4. Technology Stack

- **Physics Digital Twin**: C++20, CMake, Eigen, deterministic ODE numerical integrator.
- **AI Orchestration**: Python 3.12, LangGraph (cyclic state routing, durable checkpoints), FastAPI, Pydantic v2.
- **Hardware Acceleration**: AMD ROCm, vLLM, AMD Token Factory hosted endpoints.
- **Vector Retrieval**: Pinecone (1,235 synthetic + 103 licensed real-world OEM/NIST vectors), FAISS local index.
- **Human-in-the-Loop**: WebAuthn, FIDO2, Chromium Virtual CTAP2 authenticator, ES256 / Ed25519.
- **Independent Execution & Storage**: Node.js 24, TypeScript, MongoDB (least-privilege replica set), Redis Streams.
- **User Interface**: React 18, Vite, TypeScript, Tailwind CSS, Recharts.

---

## 5. Quick-Start Guide (Local Reproducibility)

### Prerequisites
- Docker Desktop (Linux container engine enabled).
- Python 3.12+ with `uv`.
- Node.js 22+ with `pnpm`.

### Installation & Startup
```powershell
# 1. Clone the repository
git clone https://github.com/aegis-grid/aegis-grid-2.0.git
cd aegis-grid-2.0

# 2. Synchronize frozen dependencies
uv sync --locked
pnpm install --frozen-lockfile

# 3. Initialize local environment and launch Docker stack
python tools/dev.py start
```

Once running:
- Open the **React Command Center** at `http://localhost:8180`.
- Telemetry streams live from the C++ digital twin.
- Trigger an isolated fault injection from the UI to witness the LangGraph diagnostic workflow and WebAuthn ceremony.

### Running the Complete Automated Regression Gate
```powershell
python tools/dev.py check
```
Verifies:
- Ruff formatting and strict Mypy type-checking (67 source files).
- OpenAPI and TypeScript contract drift synchronization.
- 3 CTest C++ physical conservation tests.
- 398 Python unit, integration, and security tests.
- 35 Node.js independent executor tests.
- 17 Playwright Chromium end-to-end browser tests.
- Secret scanning (899 files clean) and dependency audits.

---

## 6. Video Demonstration & Media Assets

- **3-Minute Walkthrough Video**: [`submission/AEGIS_GRID_FINAL/DEMO_VIDEO.mp4`](file:///D:/AEGIS%20GRID/submission/AEGIS_GRID_FINAL/DEMO_VIDEO.mp4) (H.264 / AAC, 180s duration).
- **Pitch Deck (12 Slides)**: [`submission/AEGIS_GRID_FINAL/PITCH_DECK.pdf`](file:///D:/AEGIS%20GRID/submission/AEGIS_GRID_FINAL/PITCH_DECK.pdf).
- **Architecture Diagram**: [`submission/AEGIS_GRID_FINAL/ARCHITECTURE_DIAGRAM.svg`](file:///D:/AEGIS%20GRID/submission/AEGIS_GRID_FINAL/ARCHITECTURE_DIAGRAM.svg) and [`.png`](file:///D:/AEGIS%20GRID/submission/AEGIS_GRID_FINAL/ARCHITECTURE_DIAGRAM.png).
- **Cover Image**: [`submission/AEGIS_GRID_FINAL/COVER_IMAGE.png`](file:///D:/AEGIS%20GRID/submission/AEGIS_GRID_FINAL/COVER_IMAGE.png) (1920x1080, 16:9).

---

## 7. Security, Trust, and Limitations

1. **Air-Gapped Simulation Containment**: All execution in this repository is strictly confined to the isolated C++ factory digital twin. Physical plant I/O is completely absent.
2. **Honest Observability Bounds**: In Family 1 (`scenario-010`), a sensor clamped at 38°C under nominal load produces $\le 0.07^\circ\text{C}$ residual. The system honestly abstains rather than guessing without physical evidence.
3. **External Hardware Status**: Dedicated physical MI300X instance, live Evolus MCP remote tools, and formal production safety certifications remain marked as **EXTERNALLY BLOCKED** until verified in physical production environments.

---

## 8. License & Attribution

- Built for the **AMD Developer Hackathon ACT III — Track 1: Intelligent Industry**.
- Licensed under the Apache License 2.0.
- Real-world vector citations strictly attributed to Parker Hannifin, Danfoss, NIST, UCI Machine Learning Repository, and Zenodo under approved open-access licenses.
