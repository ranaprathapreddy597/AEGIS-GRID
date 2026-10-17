# AEGIS//GRID 2.0 — Final Hackathon Submission Checklist

> **Event**: AMD Developer Hackathon ACT III — Track 1: Intelligent Industry  
> **Platform**: lablab.ai  
> **Prepared**: 2026-10-17  
> **Audit Status**: FULLY PREPARED & VERIFIED

---

## 1. Submission Deliverables Checklist

| Item | Requirement / Asset | File Path in Submission Package | Status | Verification Detail |
|---|---|---|---|---|
| **1. Project Title** | Descriptive title | `SUBMISSION_FORM.md` | **READY** | *"AEGIS//GRID 2.0: The Autonomous Industrial Immune System"* |
| **2. Short Description** | $\le 255$ characters | `SUBMISSION_FORM.md` | **READY** | Exactly 251 characters (verified programmatically) |
| **3. Long Description** | $\ge 100$ words | `SUBMISSION_FORM.md` | **READY** | Exactly 294 words (verified programmatically) |
| **4. Technology Tags** | Tags list | `SUBMISSION_FORM.md` | **READY** | AMD ROCm, vLLM, LangGraph, React, TypeScript, C++20, Python, WebAuthn |
| **5. Category Tags** | Category selection | `SUBMISSION_FORM.md` | **READY** | Intelligent Industry, Industrial AI, Cybersecurity, Digital Twin |
| **6. Cover Image** | PNG/JPG, 16:9 ratio | `COVER_IMAGE.png` | **READY** | 1920x1080 PNG (16:9 aspect ratio, 420 KB) |
| **7. Pitch Deck (PDF)** | Presentation slides | `PITCH_DECK.pdf` | **READY** | 12 Slides, 16:9 landscape, generated with ReportLab (24 KB) |
| **8. Demo Video (MP4)** | Video $\le 5$ min | `DEMO_VIDEO.mp4` | **READY** | 180.0s (3:00) H.264 video of clean demo (4.5 MB) |
| **9. Narration Script** | Timestamped script | `DEMO_SCRIPT.md` | **READY** | Full 0:00–3:00 scene-by-scene narration and clicks |
| **10. Architecture Diagram** | SVG and PNG formats | `ARCHITECTURE_DIAGRAM.svg` / `.png` | **READY** | Vector SVG (1600x900) & high-res PNG generated |
| **11. Public README** | Repository documentation | `README.md` | **READY** | Complete architecture, quickstart, benchmark evidence |
| **12. Empirical Benchmarks** | Measured evaluation | `BENCHMARKS.md` | **READY** | 73% diagnosis recall, 70% forecast recall, 0 confounder alarms |
| **13. Security & Limits** | Formal boundaries | `SECURITY_AND_LIMITATIONS.md` | **READY** | WebAuthn boundaries, simulation containment, disclaimers |
| **14. Business Case** | Commercial strategy | `BUSINESS_CASE.md` | **READY** | Vertical targets, downtime economics, deployment model |
| **15. Criteria Matrix** | Track 1 alignment | `JUDGING_CRITERIA_MATRIX.md` | **READY** | Complete alignment against AMD ACT III criteria |
| **16. Submission ZIP** | Complete bundle archive | `submission/AEGIS_GRID_FINAL.zip` | **READY** | Bundles all 15 deliverables into one clean package |

---

## 2. External Actions & User Verification Matrix

The following items cannot be performed autonomously by an AI agent and are explicitly designated as **REQUIRES USER ACTION**:

| External Action | Required User Step | Guidance & Pre-Configured Assets | Status |
|---|---|---|---|
| **Public GitHub Repository** | Push local git repository to user's public GitHub account | `git remote add origin https://github.com/<your-username>/aegis-grid-2.0.git`<br>`git push -u origin main` | **REQUIRES USER ACTION** |
| **Lablab.ai Team Profile** | Log in to lablab.ai and ensure you are registered on an AMD ACT III team | Solo developers or teams must register via personal OAuth / email login on lablab.ai | **REQUIRES USER ACTION** |
| **Video Hosting Link** | If submission form requires an external video URL (YouTube/Vimeo/Loom) | Upload `submission/AEGIS_GRID_FINAL/DEMO_VIDEO.mp4` as an unlisted video on YouTube/Vimeo and paste the URL | **REQUIRES USER ACTION** |
| **Online Application URL** | If an external public web URL is required beyond local evaluation | Launch via AWS/Render/DigitalOcean using `infra/local/compose.yaml` or provide repository link with local Docker instructions | **REQUIRES USER ACTION** |
| **Final Form Submission** | Copy fields from `SUBMISSION_FORM.md` into the lablab.ai project submission page | All fields are pre-formatted and length-validated to paste directly into lablab.ai | **REQUIRES USER ACTION** |

---

## 3. Verified Blockers & Non-Applicable Items

| Item | Assessment | Formal Designation |
|---|---|---|
| **IBM Bob Tool Usage** | IBM Bob was an event-specific tool for an IBM hackathon. It is not required for the AMD Developer Hackathon ACT III. | **NOT APPLICABLE** (No false claim made) |
| **Physical Factory Actuation** | All execution is strictly air-gapped within the deterministic C++ digital twin. Physical plant I/O is absent. | **INTENTIONALLY BLOCKED BY SAFETY INTERLOCK** |
| **Dedicated MI300X Bare Metal** | Hosted AMD Token Factory endpoints evaluated (2,639 tokens); bare-metal cluster access was unprovisioned. | **EXTERNALLY BLOCKED** |
| **Live Evolus MCP Servers** | Strict Pydantic contracts and offline doubles implemented; live remote MCP extraction unprovisioned. | **EXTERNALLY BLOCKED** |
