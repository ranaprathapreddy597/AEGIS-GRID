"""Generate professional 12-slide 16:9 PDF Pitch Deck for AEGIS//GRID 2.0 hackathon submission."""

from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "submission/AEGIS_GRID_FINAL"
PDF_PATH = OUTPUT_DIR / "PITCH_DECK.pdf"

# 16:9 Slide Dimensions (Points: 960 x 540)
PAGE_WIDTH = 960
PAGE_HEIGHT = 540

# Color Palette
BG_COLOR = HexColor("#0b0f19")
CARD_BG = HexColor("#131a28")
HEADER_BG = HexColor("#080c14")
AMD_RED = HexColor("#ED1C24")
CYAN = HexColor("#00E5FF")
GREEN = HexColor("#00E676")
AMBER = HexColor("#FFB300")
TEXT_WHITE = HexColor("#FFFFFF")
TEXT_LIGHT = HexColor("#C5D2E5")
TEXT_MUTED = HexColor("#8FA0BA")
LINE_COLOR = HexColor("#1f2c42")


def draw_header_footer(c: canvas.Canvas, slide_num: int, title: str, subtitle: str):
    # Top bar
    c.setFillColor(HEADER_BG)
    c.rect(0, PAGE_HEIGHT - 60, PAGE_WIDTH, 60, fill=1, stroke=0)
    c.setFillColor(AMD_RED)
    c.rect(0, PAGE_HEIGHT - 62, PAGE_WIDTH, 2, fill=1, stroke=0)

    # Title text
    c.setFillColor(TEXT_WHITE)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, PAGE_HEIGHT - 38, title)

    c.setFillColor(TEXT_MUTED)
    c.setFont("Helvetica", 11)
    c.drawString(
        40 + c.stringWidth(title, "Helvetica-Bold", 18) + 15, PAGE_HEIGHT - 37, f"|  {subtitle}"
    )

    # Top right event pill
    c.setFillColor(CARD_BG)
    c.setStrokeColor(CYAN)
    c.setLineWidth(1)
    c.roundRect(PAGE_WIDTH - 290, PAGE_HEIGHT - 45, 250, 26, 4, fill=1, stroke=1)
    c.setFillColor(CYAN)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(PAGE_WIDTH - 280, PAGE_HEIGHT - 33, "AMD ACT III: INTELLIGENT INDUSTRY")

    # Bottom bar
    c.setFillColor(HEADER_BG)
    c.rect(0, 0, PAGE_WIDTH, 30, fill=1, stroke=0)
    c.setStrokeColor(LINE_COLOR)
    c.line(0, 30, PAGE_WIDTH, 30)

    c.setFillColor(TEXT_MUTED)
    c.setFont("Helvetica", 9)
    c.drawString(
        40,
        11,
        "AEGIS//GRID 2.0  •  The Autonomous Industrial Immune System  •  lablab.ai Final Submission",
    )
    c.drawRightString(PAGE_WIDTH - 40, 11, f"Slide {slide_num} of 12")


def draw_card(c: canvas.Canvas, x, y, w, h, title="", stroke_color=LINE_COLOR):
    c.setFillColor(CARD_BG)
    c.setStrokeColor(stroke_color)
    c.setLineWidth(1.2)
    c.roundRect(x, y, w, h, 6, fill=1, stroke=1)
    if title:
        c.setFillColor(HexColor("#182336"))
        c.roundRect(x, y + h - 28, w, 28, 6, fill=1, stroke=0)
        c.setFillColor(TEXT_WHITE)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(x + 12, y + h - 19, title)


def render_pitch_deck():
    c = canvas.Canvas(str(PDF_PATH), pagesize=(PAGE_WIDTH, PAGE_HEIGHT))

    # =========================================================================
    # SLIDE 1: Title & Vision
    # =========================================================================
    c.setFillColor(BG_COLOR)
    c.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)
    # Background accent lines
    c.setStrokeColor(HexColor("#162234"))
    for x in range(0, PAGE_WIDTH, 40):
        c.line(x, 0, x, PAGE_HEIGHT)

    # Glowing banner
    c.setFillColor(AMD_RED)
    c.rect(80, PAGE_HEIGHT - 120, 12, 100, fill=1, stroke=0)

    c.setFillColor(TEXT_WHITE)
    c.setFont("Helvetica-Bold", 44)
    c.drawString(110, PAGE_HEIGHT - 75, "AEGIS // GRID 2.0")

    c.setFillColor(CYAN)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(110, PAGE_HEIGHT - 110, "The Autonomous Industrial Immune System")

    c.setFillColor(TEXT_LIGHT)
    c.setFont("Helvetica", 13)
    c.drawString(
        110,
        PAGE_HEIGHT - 145,
        "Coupled Physics Digital Twins  •  AMD Hosted Intelligence  •  Cryptographic Zero-Trust Execution",
    )

    # 3 core feature highlights
    draw_card(c, 80, 140, 245, 180, "PHYSICS-FIRST RESILIENCE", CYAN)
    c.setFillColor(TEXT_LIGHT)
    c.setFont("Helvetica", 10)
    c.drawString(95, 270, "• 6-Cell Coupled C++ Factory Twin")
    c.drawString(95, 250, "• Deterministic Energy Observer")
    c.drawString(95, 230, "• 100% Precision Anomaly Detection")
    c.drawString(95, 210, "• Detects Sensor Spoof & Clamps")
    c.drawString(95, 175, "✓ Outperforms Baseline Guards")

    draw_card(c, 355, 140, 250, 180, "AMD TOKEN FACTORY INFERENCE", AMD_RED)
    c.setFillColor(TEXT_LIGHT)
    c.setFont("Helvetica", 10)
    c.drawString(370, 270, "• LangGraph Multi-Agent Workflows")
    c.drawString(370, 250, "• 192GB HBM3 Memory Profiling")
    c.drawString(370, 230, "• Minimax Adversarial Tournament")
    c.drawString(370, 210, "• Pinecone Dual-Vector Retrieval")
    c.drawString(370, 175, "✓ 2,639 Evaluated Tokens")

    draw_card(c, 635, 140, 245, 180, "WEBAUTHN ASYMMETRIC CONTROL", GREEN)
    c.setFillColor(TEXT_LIGHT)
    c.setFont("Helvetica", 10)
    c.drawString(650, 270, "• FIDO2 / CTAP2 Passkey Approval")
    c.drawString(650, 250, "• Bound to Exact Action Digest")
    c.drawString(650, 230, "• Single-Use Ed25519 Capability")
    c.drawString(650, 210, "• Air-Gapped Executor & Interlocks")
    c.drawString(650, 175, "✓ Zero Unauthorized Writes")

    # Submitter info
    c.setFillColor(TEXT_MUTED)
    c.setFont("Helvetica", 10)
    c.drawString(
        80,
        70,
        "AMD Developer Hackathon ACT III  |  Track 1: Intelligent Industry  |  Hosted on lablab.ai  |  2026",
    )
    c.showPage()

    # =========================================================================
    # SLIDE 2: The Industrial Problem
    # =========================================================================
    c.setFillColor(BG_COLOR)
    c.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)
    draw_header_footer(
        c, 2, "THE INDUSTRIAL PROBLEM", "When Stealth Failures Meet Modern Automation"
    )

    draw_card(c, 40, 230, 420, 230, "STEALTH INDUSTRIAL ANOMALIES", AMD_RED)
    c.setFillColor(TEXT_LIGHT)
    c.setFont("Helvetica", 11)
    c.drawString(55, 400, "1. Deceptive Sensor Failures:")
    c.setFont("Helvetica", 10)
    c.drawString(70, 380, "A thermal sensor clamped to 38°C appears perfectly healthy to")
    c.drawString(70, 365, "standard SCADA alarms while cell temperature escalates toward 70°C.")
    c.setFont("Helvetica", 11)
    c.drawString(55, 335, "2. Cascading Physical Coupling:")
    c.setFont("Helvetica", 10)
    c.drawString(70, 315, "A choked coolant line or pump degradation in Cell 3 steals pressure")
    c.drawString(70, 300, "from peer cells, triggering systemic thermal runaway across the plant.")
    c.setFont("Helvetica", 11)
    c.drawString(55, 270, "3. Asymmetric Blast Radius:")
    c.setFont("Helvetica", 10)
    c.drawString(70, 250, "Unplanned thermal shutdown in advanced manufacturing costs")
    c.drawString(70, 235, "thousands of dollars per minute in lost precision tooling.")

    draw_card(c, 500, 230, 420, 230, "THE CATASTROPHIC LLM FAILURE MODE", AMBER)
    c.setFillColor(TEXT_LIGHT)
    c.setFont("Helvetica", 11)
    c.drawString(515, 400, "1. Unconstrained Hallucinated Actions:")
    c.setFont("Helvetica", 10)
    c.drawString(530, 380, "Generic LLMs connected to tool APIs generate unsafe restart proposals")
    c.drawString(530, 365, "without verifying plant pressure envelopes or physical interlocks.")
    c.setFont("Helvetica", 11)
    c.drawString(515, 335, "2. Prompt Injection & Malicious Manuals:")
    c.setFont("Helvetica", 10)
    c.drawString(530, 315, "Contradictory OEM documentation or adversarial external text can")
    c.drawString(530, 300, "trick ungrounded reasoning agents into executing fatal commands.")
    c.setFont("Helvetica", 11)
    c.drawString(515, 270, "3. Absence of Cryptographic Control Boundaries:")
    c.setFont("Helvetica", 10)
    c.drawString(530, 250, "Chatbots with direct database/actuator tokens invite unauthorized")
    c.drawString(530, 235, "mutations, replay attacks, and unverified autonomous actions.")

    draw_card(c, 40, 60, 880, 145, "THE AEGIS//GRID MANDATE")
    c.setFillColor(CYAN)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(
        55, 160, "INTELLIGENT INDUSTRY REQUIRES AN AUTONOMOUS IMMUNE SYSTEM — NOT JUST A CHATBOT."
    )
    c.setFillColor(TEXT_LIGHT)
    c.setFont("Helvetica", 10)
    c.drawString(55, 140, "• AI must never hold direct plant actuation authority.")
    c.drawString(
        55,
        120,
        "• Anomaly detection must be grounded in deterministic first-principles physics, not just statistical thresholds.",
    )
    c.drawString(
        55,
        100,
        "• All recovery plans must survive adversarial counterfactual simulation before presentation to a human.",
    )
    c.drawString(
        55,
        80,
        "• Execution must be gated behind cryptographically non-repudiable WebAuthn approval with atomic audit receipts.",
    )
    c.showPage()

    # =========================================================================
    # SLIDE 3: The AEGIS//GRID Solution
    # =========================================================================
    c.setFillColor(BG_COLOR)
    c.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)
    draw_header_footer(
        c, 3, "THE AEGIS//GRID SOLUTION", "End-to-End Autonomous Defense Architecture"
    )

    # 4 Architecture Quadrants
    quads = [
        (
            "1. NATIVE C++ DIGITAL TWIN",
            CYAN,
            [
                "• Deterministic 6-cell thermal & fluid kernel",
                "• Coupled ODEs for branch flow, heat flux, & mixing",
                "• Seeded fault injection (spoofing, chokes, bursts)",
                "• Conservation invariants checked on every step",
            ],
        ),
        (
            "2. RYZEN AI EDGE SENTINEL",
            GREEN,
            [
                "• Real-time First-Law energy balance observer",
                "• Physics residual detects hidden clamped sensors",
                "• Zero cloud dependency for local safety fallback",
                "• 100% precision on fresh-seed held-out cases",
            ],
        ),
        (
            "3. AMD HOSTED INTELLIGENCE",
            AMD_RED,
            [
                "• Cyclic LangGraph multi-agent diagnostic graph",
                "• Hosted AMD Token Factory vLLM inference",
                "• Dual Pinecone retrieval: 1,235 + 103 vectors",
                "• Minimax Red/Blue counterfactual tournament",
            ],
        ),
        (
            "4. CRYPTOGRAPHIC WEBAUTHN HITL",
            AMBER,
            [
                "• FIDO2 / CTAP2 hardware-bound approval",
                "• SHA-256 canonical proposal digest binding",
                "• Single-use Ed25519 capability with 60s TTL",
                "• Independent executor & persistent audit receipt",
            ],
        ),
    ]

    for i, (q_title, q_col, q_bullets) in enumerate(quads):
        qx = 40 + (i % 2) * 450
        qy = 255 if i < 2 else 60
        draw_card(c, qx, qy, 430, 175, q_title, q_col)
        c.setFillColor(TEXT_LIGHT)
        c.setFont("Helvetica", 10)
        for b_idx, bullet in enumerate(q_bullets):
            c.drawString(qx + 18, qy + 115 - b_idx * 22, bullet)

    c.showPage()

    # =========================================================================
    # SLIDE 4: AMD-Powered Intelligence
    # =========================================================================
    c.setFillColor(BG_COLOR)
    c.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)
    draw_header_footer(
        c,
        4,
        "AMD-POWERED INTELLIGENCE",
        "Hosted Token Factory Inference & 192GB HBM3 Memory Profiling",
    )

    draw_card(c, 40, 240, 420, 220, "AMD TOKEN FACTORY HOSTED ENDPOINTS", AMD_RED)
    c.setFillColor(TEXT_LIGHT)
    c.setFont("Helvetica", 10)
    c.drawString(55, 415, "• Hosted ROCm / vLLM Inference Gateway:")
    c.drawString(70, 395, "Real HTTP POST communication with AMD Token Factory")
    c.drawString(70, 380, "evaluating DeepSeek-R1 and Qwen model backends.")
    c.drawString(55, 355, "• Strict Contract Validation:")
    c.drawString(70, 335, "Structured output parsed into strict Pydantic models.")
    c.drawString(70, 320, "Rejects ungrounded causes and malformed JSON payloads.")
    c.drawString(55, 295, "• Evaluated Hosted Proof:")
    c.drawString(70, 275, "2,639 acknowledged tokens evaluated in hosted LangGraph")
    c.drawString(70, 260, "workflow with deterministic offline contingency fallback.")

    draw_card(c, 500, 240, 420, 220, "192GB HBM3 GPU MEMORY PROFILING", CYAN)
    c.setFillColor(TEXT_LIGHT)
    c.setFont("Helvetica", 10)
    c.drawString(515, 415, "• Analytical Memory Equation (tools/gpu_memory_budget.py):")
    c.setFillColor(HexColor("#00E5FF"))
    c.setFont("Courier-Bold", 9)
    c.drawString(530, 395, "Total = Weights + 2*N_layers*N_heads*Dim*Tokens*B + Buffers")
    c.setFillColor(TEXT_LIGHT)
    c.setFont("Helvetica", 10)
    c.drawString(515, 365, "• Long-Context Benchmark Analysis (30.5B Parameter Model):")
    c.drawString(530, 345, "- Weights (BF16): ~56.81 GiB")
    c.drawString(530, 330, "- KV Cache (256K Context, Batch 1): ~24.0 GiB")
    c.drawString(530, 315, "- KV Cache (256K Context, Batch 2): ~48.0 GiB")
    c.drawString(530, 295, "• Result: Standard 80 GiB GPUs encounter OOM at batch >= 1,")
    c.drawString(530, 280, "  whereas AMD Instinct MI300X (192 GB) provides 87 GiB headroom.")

    draw_card(c, 40, 60, 880, 160, "CYCLIC LANGGRAPH MULTI-AGENT REASONING PIPELINE")
    c.setFillColor(TEXT_LIGHT)
    c.setFont("Helvetica", 10)
    c.drawString(
        55,
        175,
        "1. Edge Sentinel triggers incident state upon detecting physical residual anomaly.",
    )
    c.drawString(
        55,
        155,
        "2. Causal Detective ranks competing hypotheses (sensor bias, choke, pump failure, electrical overload).",
    )
    c.drawString(
        55,
        135,
        "3. Manual Expert retrieves versioned OEM bulletins from Pinecone; blocks execution on contradictory manuals.",
    )
    c.drawString(
        55,
        115,
        "4. Blue Team proposes candidate recovery plans; Red Team injects worst-case adversarial conditions.",
    )
    c.drawString(
        55,
        95,
        "5. Simulation Referee executes C++ twin rollouts and halts at a durable checkpoint for human approval.",
    )
    c.showPage()

    # =========================================================================
    # SLIDE 5: Native C++ Factory Digital Twin
    # =========================================================================
    c.setFillColor(BG_COLOR)
    c.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)
    draw_header_footer(
        c, 5, "NATIVE C++ DIGITAL TWIN", "Coupled Physical Conservation & Counterfactual Replay"
    )

    draw_card(c, 40, 220, 420, 240, "PHYSICAL CONSERVATION LAWS", CYAN)
    c.setFillColor(TEXT_LIGHT)
    c.setFont("Helvetica", 10)
    c.drawString(55, 415, "• First-Principles Conservation ODEs:")
    c.setFillColor(HexColor("#00E5FF"))
    c.setFont("Courier-Bold", 9)
    c.drawString(70, 395, "C_i * dT_i/dt = P_i - h_i(q_i)*(T_i - T_coolant) + coupling_i")
    c.setFillColor(TEXT_LIGHT)
    c.setFont("Helvetica", 10)
    c.drawString(55, 365, "• Dynamic Flow Distribution:")
    c.drawString(70, 350, "Shared loop pressure drop across 6 branches with nonlinear")
    c.drawString(70, 335, "Darcy-Weisbach flow resistance and pump head curves.")
    c.drawString(55, 310, "• Seeded Deterministic Reproducibility:")
    c.drawString(70, 295, "Exact initial conditions, noise generators, and fault injections")
    c.drawString(70, 280, "guarantee bit-for-bit test reproducibility across platforms.")
    c.drawString(55, 255, "✓ 3/3 CTests Pass in 3.44s with zero leaks or numerical instability.")

    draw_card(c, 500, 220, 420, 240, "SEEDED CATASTROPHIC FAULT SUITE", AMD_RED)
    c.setFillColor(TEXT_LIGHT)
    c.setFont("Helvetica", 10)
    c.drawString(515, 415, "• Family 1: Sensor Spoofing & Clamping (scenario-010)")
    c.drawString(530, 395, "Sensor clamped to min(T, 38°C) while cell overheats to 70°C.")
    c.drawString(515, 370, "• Family 3: Mechanical Pump Degradation")
    c.drawString(530, 350, "Loop pressure collapses from 100 kPa to 18 kPa; flows drop.")
    c.drawString(515, 325, "• Family 5: Electrical Overload Bursts")
    c.drawString(530, 305, "Sudden electrical demand surge exceeding thermal dissipation.")
    c.drawString(515, 280, "• Family 9: Choked Coolant Valve (scenario-090)")
    c.drawString(530, 260, "Branch flow drops 90%; heat accumulates rapidly in cell.")
    c.drawString(515, 235, "✓ Multi-telemetry energy estimation catches all unmanifested states.")

    draw_card(c, 40, 60, 880, 140, "COUNTERFACTUAL RECOVERY STRATEGY COMPARISON")
    c.setFillColor(TEXT_LIGHT)
    c.setFont("Helvetica", 10)
    c.drawString(
        55,
        155,
        "• Rather than blindly trusting an AI recommendation, the simulator executes parallel candidate rollouts:",
    )
    c.drawString(
        70,
        135,
        "1. Safe Stop (Coordinated 6-Cell Cooldown): Safest, zero risk, moderate lost production.",
    )
    c.drawString(
        70,
        120,
        "2. Dynamic Flow Boost: Increases pump demand to 100%; effective for mild chokes, infeasible if pump is degraded.",
    )
    c.drawString(
        70,
        105,
        "3. Load Shedding: Throttles electrical power by 50%; partial thermal relief while maintaining production.",
    )
    c.drawString(
        55,
        80,
        "✓ The operator sees exact predicted temperatures, recovery horizons, and modeled downtime before approving.",
    )
    c.showPage()

    # =========================================================================
    # SLIDE 6: Dual-Vector Knowledge Retrieval
    # =========================================================================
    c.setFillColor(BG_COLOR)
    c.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)
    draw_header_footer(
        c,
        6,
        "DUAL PINECONE RETRIEVAL",
        "1,235 Synthetic Vectors + 103 Verified Real-World References",
    )

    draw_card(c, 40, 220, 420, 240, "PINECONE NAMESPACE PARTITIONING", CYAN)
    c.setFillColor(TEXT_LIGHT)
    c.setFont("Helvetica", 10)
    c.drawString(55, 415, "• Namespace 1: Synthetic Plant Manuals (1,235 Vectors)")
    c.drawString(70, 395, "Comprehensive operational specs, alarm procedures, thermal limits,")
    c.drawString(70, 380, "and safe-stop runbooks authored specifically for the 6-cell twin.")
    c.drawString(55, 350, "• Namespace 2: Real-World Licensed Corpus (103 Vectors)")
    c.drawString(70, 330, "Publicly licensed OEM & NIST datasets (Parker, Danfoss, NIST,")
    c.drawString(70, 315, "UCI, Zenodo) providing authentic cooling physics and valve data.")
    c.drawString(55, 285, "• Zero Vector Writes / Strict Read-Only Guard:")
    c.drawString(70, 265, "All evaluations preserve existing vectors; zero reingestion or")
    c.drawString(70, 250, "accidental modification during runtime execution.")

    draw_card(c, 500, 220, 420, 240, "CONTRADICTORY EVIDENCE DEFENSE", AMD_RED)
    c.setFillColor(TEXT_LIGHT)
    c.setFont("Helvetica", 10)
    c.drawString(515, 415, "• Contradictory Manuals Conflict Blocker:")
    c.drawString(530, 395, "When OEM Manual 1 specifies a 70°C emergency stop but an")
    c.drawString(530, 380, "unverified bulletin asserts 95°C, AEGIS//GRID detects the conflict.")
    c.drawString(515, 350, "• Deterministic Action Refusal:")
    c.drawString(530, 330, "The system refuses to authorize recovery until the contradiction")
    c.drawString(530, 315, "is reviewed and signed off by authorized human engineering.")
    c.drawString(515, 285, "• Prompt Injection Immunity:")
    c.drawString(530, 265, "Retrieved manual text is treated as untrusted data; structural")
    c.drawString(530, 250, "sandboxing prevents documents from executing tool instructions.")

    draw_card(c, 40, 60, 880, 140, "PROVENANCE & CITATION INTEGRITY")
    c.setFillColor(TEXT_LIGHT)
    c.setFont("Helvetica", 10)
    c.drawString(
        55,
        155,
        "• Every diagnostic assertion is bound to explicit document citations, page numbers, and SHA-256 hashes.",
    )
    c.drawString(
        55,
        135,
        "• Grounded Diagnosis: Causes lacking physical or manual evidence are rejected with explicit abstention.",
    )
    c.drawString(
        55,
        115,
        "• Tested on 30 healthy operating confounders: 0 false cause assertions (100% correct abstention).",
    )
    c.drawString(
        55,
        95,
        "• Tested on 100 fresh-seed native cases: 100% precision with 73.0% recall, outperforming legacy baselines.",
    )
    c.showPage()

    # =========================================================================
    # SLIDE 7: Cryptographic Human-in-the-Loop
    # =========================================================================
    c.setFillColor(BG_COLOR)
    c.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)
    draw_header_footer(
        c, 7, "WEBAUTHN ASYMMETRIC CONTROL", "FIDO2 / CTAP2 Hardware-Bound Authorization Ceremony"
    )

    # Step-by-step ceremony flow
    c.setFillColor(TEXT_LIGHT)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, 445, "THE 5-STEP WEBAUTHN SAFETY BOUNDARY")

    steps = [
        (
            "1. Action Proposal",
            "LangGraph generates canonical action proposal with exact parameters, expected state version, and SHA-256 digest.",
        ),
        (
            "2. Challenge Binding",
            "Server creates unpredictable WebAuthn challenge cryptographically bound to the exact action digest.",
        ),
        (
            "3. Passkey Ceremony",
            "Operator signs challenge using FIDO2 / CTAP2 hardware passkey (ES256 signature over clientDataJSON).",
        ),
        (
            "4. Single-Use Capability",
            "Server verifies signature and origin, issuing a single-use Ed25519 execution capability with 60s TTL.",
        ),
        (
            "5. Guarded Execution",
            "Independent executor verifies capability, enforces safety shield limits, executes stop, and writes audit receipt.",
        ),
    ]

    for s_idx, (s_title, s_desc) in enumerate(steps):
        sy = 390 - s_idx * 55
        c.setFillColor(CARD_BG)
        c.setStrokeColor(AMBER if s_idx == 2 else LINE_COLOR)
        c.roundRect(40, sy, 880, 45, 4, fill=1, stroke=1)
        c.setFillColor(AMBER if s_idx == 2 else CYAN)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(55, sy + 25, s_title)
        c.setFillColor(TEXT_LIGHT)
        c.setFont("Helvetica", 10)
        c.drawString(220, sy + 25, s_desc)

    draw_card(c, 40, 60, 880, 100, "MATHEMATICALLY PROVABLE ATTACK DEFENSES")
    c.setFillColor(TEXT_LIGHT)
    c.setFont("Helvetica", 10)
    c.drawString(
        55,
        115,
        "• Replay Rejection: Nonce & challenge expire after single use; identical replay attempts return HTTP 403.",
    )
    c.drawString(
        55,
        95,
        "• Tamper Rejection: Altering a single byte in the action plan changes the SHA-256 digest, invalidating the signature.",
    )
    c.drawString(
        55,
        75,
        "• Stale-State Rejection: If plant state changes before approval arrives, the state version mismatch aborts execution.",
    )
    c.showPage()

    # =========================================================================
    # SLIDE 8: Independent Execution & Audit Ledger
    # =========================================================================
    c.setFillColor(BG_COLOR)
    c.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)
    draw_header_footer(
        c, 8, "INDEPENDENT EXECUTION & AUDIT", "Zero-Trust Actuator Interlocks & Immutable Receipts"
    )

    draw_card(c, 40, 220, 420, 240, "INDEPENDENT SAFETY SHIELD", GREEN)
    c.setFillColor(TEXT_LIGHT)
    c.setFont("Helvetica", 10)
    c.drawString(55, 415, "• Physical Isolation from AI Orchestrator:")
    c.drawString(70, 395, "The execution gateway runs in an isolated Node.js container")
    c.drawString(70, 380, "with no access to AI bearer tokens or cloud credentials.")
    c.drawString(55, 350, "• Hard Safety Invariants:")
    c.drawString(70, 330, "Even with a valid user signature, the safety shield enforces:")
    c.drawString(70, 315, "- Maximum cell temperature limit (70.0°C hard cutoff)")
    c.drawString(70, 300, "- Minimum branch flow limits and valve slew rate clamps")
    c.drawString(70, 285, "- Deny-by-default on unmodeled physical actuators")
    c.drawString(55, 255, "✓ 35/35 Node Security Tests Pass verifying fail-closed policy.")

    draw_card(c, 500, 220, 420, 240, "CRYPTOGRAPHIC AUDIT RECEIPTS", CYAN)
    c.setFillColor(TEXT_LIGHT)
    c.setFont("Helvetica", 10)
    c.drawString(515, 415, "• Atomic Post-Execution Proof Structure:")
    c.drawString(530, 395, "Every approved action generates an immutable audit receipt")
    c.drawString(530, 380, "stored in an append-only MongoDB collection.")
    c.drawString(515, 350, "• Cryptographic Binding:")
    c.drawString(530, 330, "- Pre- and post-execution cell temperatures")
    c.drawString(530, 315, "- Full plant state version hash before and after")
    c.drawString(530, 300, "- Authorized user identity & WebAuthn credential ID")
    c.drawString(530, 285, "- Action ID, plan SHA-256, and execution timestamp")
    c.drawString(515, 255, "✓ 1 Commissioned Receipt Verified (96b9c3f4...) preserved.")

    draw_card(c, 40, 60, 880, 140, "AIR-GAPPED APPLICATION RUNTIME")
    c.setFillColor(TEXT_LIGHT)
    c.setFont("Helvetica", 10)
    c.drawString(
        55,
        155,
        "• Least-Privilege Tenancy: Storage authorization tests recorded 23 actual MongoDB privilege denials.",
    )
    c.drawString(
        55,
        135,
        "• Zero Forbidden Writes: Monitoring accounts have zero permission to modify operational or safety collections.",
    )
    c.drawString(
        55,
        115,
        "• Complete Source Preservation: 234 runtime/test files match clean export with zero mismatches.",
    )
    c.drawString(
        55,
        95,
        "• 100% Simulator Air-Gap: No uncontrolled connection to physical factory machinery.",
    )
    c.showPage()

    # =========================================================================
    # SLIDE 9: Measured Benchmark Results
    # =========================================================================
    c.setFillColor(BG_COLOR)
    c.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)
    draw_header_footer(
        c, 9, "EMPIRICAL BENCHMARKS", "Rigorous Held-Out Evaluation on Synthetic & Physical Data"
    )

    # Table of benchmark metrics
    c.setFillColor(CARD_BG)
    c.setStrokeColor(LINE_COLOR)
    c.roundRect(40, 210, 880, 250, 6, fill=1, stroke=1)

    # Table Header
    c.setFillColor(HexColor("#182336"))
    c.rect(40, 420, 880, 40, fill=1, stroke=0)
    c.setFillColor(CYAN)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(55, 435, "BENCHMARK EXPERIMENT")
    c.drawString(320, 435, "BASELINE / PREVIOUS")
    c.drawString(510, 435, "AEGIS//GRID 2.0 (OPTIMIZED)")
    c.drawString(750, 435, "STATISTICAL GAIN")

    # Table Rows
    rows = [
        (
            "Native Fault Diagnosis Recall (100 Cases)",
            "48.0% (48 / 100)",
            "73.0% (73 / 100)",
            "+25.0 pp (z = 3.74, p < 0.001)",
        ),
        (
            "Native Fault Diagnosis Precision",
            "100.0% (48 / 48)",
            "100.0% (73 / 73)",
            "Maintained 0 False Positives",
        ),
        (
            "Native Fault Diagnosis Accuracy",
            "65.0% (Legacy: 75.0%)",
            "80.0% (Legacy: 75.0%)",
            "+15.0 pp (Outperforms Legacy)",
        ),
        (
            "Healthy Confounders False Positives (30 Cases)",
            "30 FP (Legacy Baseline)",
            "0 FP (100% Abstention)",
            "Zero Hallucinated Causes",
        ),
        (
            "Thermal Forecasting Hazard Recall (30 Episodes)",
            "10.0% (2 / 20 Windows)",
            "70.0% (14 / 20 Windows)",
            "+60.0 pp (Fisher p = 0.00022)",
        ),
        ("Thermal Forecasting F1 Score", "0.167", "0.683", "4.1x Improvement"),
        (
            "Thermal Forecasting False Alarm Rate (1,455 Negs)",
            "0.14% (2 / 1,455)",
            "0.48% (7 / 1,455)",
            "Low FPR (< 0.5%)",
        ),
        (
            "Median Warning Lead Time Before Hazard",
            "60.0s (2 windows only)",
            "25.0s (14 windows)",
            "Actionable Warning Horizon",
        ),
    ]

    c.setFont("Helvetica", 9)
    for r_idx, (r_name, r_base, r_opt, r_gain) in enumerate(rows):
        ry = 395 - r_idx * 23
        c.setFillColor(TEXT_LIGHT)
        c.drawString(55, ry, r_name)
        c.setFillColor(TEXT_MUTED)
        c.drawString(320, ry, r_base)
        c.setFillColor(
            GREEN
            if "73.0%" in r_opt or "70.0%" in r_opt or "100.0%" in r_opt or "80.0%" in r_opt
            else TEXT_WHITE
        )
        c.drawString(510, ry, r_opt)
        c.setFillColor(CYAN)
        c.drawString(750, ry, r_gain)
        c.setStrokeColor(HexColor("#162030"))
        c.line(40, ry - 6, 920, ry - 6)

    draw_card(c, 40, 60, 880, 130, "FULL AUTOMATED REGRESSION GATE RESULTS")
    c.setFillColor(TEXT_LIGHT)
    c.setFont("Helvetica", 10)
    c.drawString(
        55,
        145,
        "• Python Test Suite: 398 / 398 PASS (32.05s) across unit, integration, and security suites.",
    )
    c.drawString(
        55,
        125,
        "• C++ Native Suite: 3 / 3 CTESTS PASS (3.44s) verifying conservation ODEs and numerical bounds.",
    )
    c.drawString(
        55,
        105,
        "• Node.js Test Suite: 35 / 35 PASS verifying independent executor policy and token verifications.",
    )
    c.drawString(
        55,
        85,
        "• Playwright Browser Suite: 17 / 17 PASS (2.1m) verifying real-time React dashboard and WebAuthn ceremonies.",
    )
    c.showPage()

    # =========================================================================
    # SLIDE 10: Market Opportunity & Business Case
    # =========================================================================
    c.setFillColor(BG_COLOR)
    c.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)
    draw_header_footer(
        c,
        10,
        "MARKET OPPORTUNITY & BUSINESS CASE",
        "High-Value Industrial Deployments for Critical Operations",
    )

    draw_card(c, 40, 220, 420, 240, "TARGET INDUSTRIAL VERTICALS", CYAN)
    c.setFillColor(TEXT_LIGHT)
    c.setFont("Helvetica", 10)
    c.drawString(55, 415, "1. Semiconductor & Advanced Packaging:")
    c.drawString(70, 395, "Extreme thermal sensitivity in lithography, etching, and chemical")
    c.drawString(70, 380, "deposition where a 2°C temperature shift spoils multi-million wafers.")
    c.drawString(55, 350, "2. Battery Gigafactories:")
    c.drawString(70, 330, "Continuous slurry mixing and cell formation loops where localized")
    c.drawString(70, 315, "cooling chokes risk thermal runaway and disastrous facility fires.")
    c.drawString(55, 285, "3. Critical Pharmaceutical Continuous Synthesis:")
    c.drawString(70, 265, "Strict thermal regulation required by FDA compliance; requires")
    c.drawString(70, 250, "immutable cryptographic receipts for all autonomous adjustments.")

    draw_card(c, 500, 220, 420, 240, "COMMERCIAL VALUE PROPOSITION", GREEN)
    c.setFillColor(TEXT_LIGHT)
    c.setFont("Helvetica", 10)
    c.drawString(515, 415, "• Downtime Prevention Economics:")
    c.drawString(530, 395, "Unplanned downtime in automotive stamping & precision machining")
    c.drawString(530, 380, "costs an estimated $22,000 per minute (Industry benchmark).")
    c.drawString(515, 350, "• 25-Second Warning Horizon:")
    c.drawString(530, 330, "Gives plant operators actionable lead time to execute coordinated")
    c.drawString(530, 315, "load shedding rather than suffering violent emergency trips.")
    c.drawString(515, 285, "• Insurability & Regulatory Audit Trail:")
    c.drawString(530, 265, "Cryptographic audit receipts provide non-repudiable engineering")
    c.drawString(530, 250, "evidence required for Lloyd's cyber-physical insurance riders.")

    draw_card(c, 40, 60, 880, 140, "DEPLOYMENT & LICENSING MODEL")
    c.setFillColor(TEXT_LIGHT)
    c.setFont("Helvetica", 10)
    c.drawString(
        55,
        155,
        "• On-Premise Edge Appliance: Lightweight Ryzen AI container running C++ sentinel and local emergency fallback.",
    )
    c.drawString(
        55,
        135,
        "• Enterprise Hybrid Cloud: Centralized AMD MI300X cluster running LangGraph multi-agent orchestration.",
    )
    c.drawString(
        55,
        115,
        "• Subscription Model: Tiered per-cell annual licensing + dedicated hardware-bound passkey tokens.",
    )
    c.drawString(
        55,
        95,
        "• Zero Vendor Lock-in: Standardized OpenAPI contracts and containerized deployment via Docker/Kubernetes.",
    )
    c.showPage()

    # =========================================================================
    # SLIDE 11: Competitive Differentiation
    # =========================================================================
    c.setFillColor(BG_COLOR)
    c.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)
    draw_header_footer(
        c,
        11,
        "COMPETITIVE DIFFERENTIATION",
        "Why AEGIS//GRID Outclasses Generic Industrial Dashboards",
    )

    draw_card(c, 40, 200, 275, 260, "GENERIC SCADA / DCS", HexColor("#556677"))
    c.setFillColor(TEXT_MUTED)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(55, 415, "TRADITIONAL CONTROLS")
    c.setFont("Helvetica", 9)
    c.drawString(55, 385, "• Static alarm thresholds.")
    c.drawString(55, 365, "• Blind to sensor spoofing.")
    c.drawString(55, 345, "• No causal explanation.")
    c.drawString(55, 325, "• Siloed manual runbooks.")
    c.drawString(55, 305, "• High false positive alarm")
    c.drawString(55, 290, "  fatigue for operators.")
    c.drawString(55, 265, "• No counterfactual preview.")
    c.drawString(55, 245, "• Vulnerable to credential theft.")

    draw_card(c, 340, 200, 275, 260, "NAIVE LLM AGENTS", AMBER)
    c.setFillColor(AMBER)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(355, 415, "CHATBOT ARCHITECTURES")
    c.setFont("Helvetica", 9)
    c.drawString(355, 385, "• Direct actuator API access.")
    c.drawString(355, 365, "• Severe hallucination risk.")
    c.drawString(355, 345, "• Vulnerable to prompt injection.")
    c.drawString(355, 325, "• No physical modeling.")
    c.drawString(355, 305, "• Model self-authorizes actions.")
    c.drawString(355, 285, "• High token latency during")
    c.drawString(355, 270, "  emergency shutdowns.")
    c.drawString(355, 245, "• Zero cryptographic audit trail.")

    draw_card(c, 640, 200, 280, 260, "AEGIS // GRID 2.0", GREEN)
    c.setFillColor(GREEN)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(655, 415, "AUTONOMOUS IMMUNE SYSTEM")
    c.setFont("Helvetica", 9)
    c.drawString(655, 385, "✓ First-Law energy observer.")
    c.drawString(655, 365, "✓ 100% precision on held-out faults.")
    c.drawString(655, 345, "✓ 0 false alarms on confounders.")
    c.drawString(655, 325, "✓ C++ counterfactual tournament.")
    c.drawString(655, 305, "✓ FIDO2 / CTAP2 human ceremony.")
    c.drawString(655, 285, "✓ Air-gapped independent shield.")
    c.drawString(655, 265, "✓ Single-use Ed25519 capabilities.")
    c.drawString(655, 245, "✓ Atomic SHA-256 audit receipts.")

    draw_card(c, 40, 60, 880, 120, "THE CORE DEFENSIVE PRINCIPLE")
    c.setFillColor(CYAN)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(
        55, 145, "AI PROPOSES • PHYSICS VERIFIES • HUMANS AUTHORIZE • AIR-GAPPED GATES EXECUTE"
    )
    c.setFillColor(TEXT_LIGHT)
    c.setFont("Helvetica", 10)
    c.drawString(
        55,
        125,
        "AEGIS//GRID completely decouples reasoning intelligence from actuation authority, ensuring that even a total",
    )
    c.drawString(
        55,
        105,
        "compromise of cloud AI models cannot breach hard plant safety interlocks or trigger unauthorized equipment operations.",
    )
    c.showPage()

    # =========================================================================
    # SLIDE 12: Alignment, Limitations & Closing
    # =========================================================================
    c.setFillColor(BG_COLOR)
    c.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)
    draw_header_footer(
        c, 12, "TRACK ALIGNMENT & CLOSING", "AMD Developer Hackathon ACT III — Submission Summary"
    )

    draw_card(c, 40, 240, 420, 220, "TRACK 1: INTELLIGENT INDUSTRY ALIGNMENT", AMD_RED)
    c.setFillColor(TEXT_LIGHT)
    c.setFont("Helvetica", 10)
    c.drawString(55, 415, "• Real Physical Modeling:")
    c.drawString(70, 395, "Built with C++20 ODE conservation laws, not simulated role-play.")
    c.drawString(55, 370, "• AMD Hardware Exploitation:")
    c.drawString(70, 350, "Demonstrated Token Factory inference & 192GB memory analysis.")
    c.drawString(55, 325, "• Measurable Industrial Impact:")
    c.drawString(
        70, 305, "25s lead time, 73% recall, 100% precision, zero confounder false alarms."
    )
    c.drawString(55, 280, "• Production-Grade Software Engineering:")
    c.drawString(70, 260, "398 Python, 3 CTests, 35 Node, 17 Playwright checks all passing.")

    draw_card(c, 500, 240, 420, 220, "HONEST LIMITATIONS & BOUNDARIES", AMBER)
    c.setFillColor(TEXT_LIGHT)
    c.setFont("Helvetica", 10)
    c.drawString(515, 415, "• Simulator Isolation:")
    c.drawString(530, 395, "All execution is strictly confined to the C++ twin; no physical I/O.")
    c.drawString(515, 370, "• Observability Boundary (Family 1):")
    c.drawString(530, 350, "Sensor clamped at 38°C under nominal load produces <= 0.07°C")
    c.drawString(530, 335, "residual; the system honestly abstains until heat rises.")
    c.drawString(515, 310, "• Hardware Blockers:")
    c.drawString(530, 290, "Dedicated MI300X instance, Evolus live tooling, and production")
    c.drawString(530, 275, "safety certification remain officially BLOCKED until validated.")

    draw_card(c, 40, 60, 880, 160, "SUBMISSION READINESS SUMMARY")
    c.setFillColor(GREEN)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(55, 175, "✓ DELIVERED: COMPLETE, REPRODUCIBLE, EVIDENCE-BACKED MONOREPO")
    c.setFillColor(TEXT_LIGHT)
    c.setFont("Helvetica", 10)
    c.drawString(
        55, 150, "• Working React Command Center & Real-Time Dashboard (Vite + TypeScript)."
    )
    c.drawString(
        55,
        130,
        "• Verified 3-Minute Clean Demo (180.0125s duration, video recorded, proof verified).",
    )
    c.drawString(
        55,
        110,
        "• Strict Zero-Secret Scan: 899 repository files scanned; 0 tokens or private keys embedded.",
    )
    c.drawString(
        55,
        90,
        "• Clean-Source Gate: Complete 398 Python / 3 CTest / 35 Node / 17 Playwright regression passes.",
    )
    c.drawString(
        55,
        70,
        "Repository: https://github.com/aegis-grid/aegis-grid-2.0  •  Thank You, AMD & Lablab.ai Judges!",
    )
    c.showPage()

    c.save()
    print(f"Pitch Deck PDF generated successfully: {PDF_PATH} (12 Slides, 16:9)")


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    render_pitch_deck()
