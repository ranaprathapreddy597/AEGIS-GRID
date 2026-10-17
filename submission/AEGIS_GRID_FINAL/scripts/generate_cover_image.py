"""Generate high-resolution 16:9 cover image for AEGIS//GRID 2.0 hackathon submission."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "submission/AEGIS_GRID_FINAL/COVER_IMAGE.png"

WIDTH = 1920
HEIGHT = 1080


def create_cover():
    image = Image.new("RGBA", (WIDTH, HEIGHT), (10, 14, 22, 255))
    draw = ImageDraw.Draw(image)

    # 1. Subtle background grid
    grid_color = (22, 32, 48, 180)
    for x in range(0, WIDTH, 40):
        draw.line([(x, 0), (x, HEIGHT)], fill=grid_color, width=1)
    for y in range(0, HEIGHT, 40):
        draw.line([(0, y), (WIDTH, y)], fill=grid_color, width=1)

    # 2. Glowing diagonal tech accents
    for i in range(-5, 10):
        offset = i * 280
        draw.line([(offset, 0), (offset + 1200, HEIGHT)], fill=(18, 26, 40, 80), width=1)

    # 3. Top accent banner / border
    draw.rectangle([(0, 0), (WIDTH, 8)], fill=(237, 28, 36, 255))  # AMD Ruby stripe
    draw.rectangle([(0, 8), (WIDTH, 12)], fill=(0, 229, 255, 180))  # Cyan trace

    # 4. Header metadata
    # Try standard system fonts or default
    try:
        font_title = ImageFont.truetype("arialbd.ttf", 76)
        font_tagline = ImageFont.truetype("arial.ttf", 32)
        font_track = ImageFont.truetype("arialbd.ttf", 24)
        font_mono = ImageFont.truetype("consola.ttf", 18)
        font_pill = ImageFont.truetype("arialbd.ttf", 16)
        font_cell_title = ImageFont.truetype("arialbd.ttf", 20)
        font_cell_val = ImageFont.truetype("consola.ttf", 22)
    except OSError:
        font_title = ImageFont.load_default()
        font_tagline = ImageFont.load_default()
        font_track = ImageFont.load_default()
        font_mono = ImageFont.load_default()
        font_pill = ImageFont.load_default()
        font_cell_title = ImageFont.load_default()
        font_cell_val = ImageFont.load_default()

    # Event badge (top-left)
    draw.rounded_rectangle(
        [(100, 60), (740, 104)],
        radius=6,
        fill=(20, 28, 44, 230),
        outline=(237, 28, 36, 200),
        width=2,
    )
    draw.text(
        (120, 72),
        "AMD DEVELOPER HACKATHON ACT III • TRACK 1: INTELLIGENT INDUSTRY",
        font=font_track,
        fill=(255, 255, 255, 240),
    )

    # Security badge (top-right)
    draw.rounded_rectangle(
        [(WIDTH - 520, 60), (WIDTH - 100, 104)],
        radius=6,
        fill=(16, 26, 36, 230),
        outline=(0, 229, 255, 180),
        width=2,
    )
    draw.text(
        (WIDTH - 500, 72),
        "VERIFIED AIR-GAPPED IMMUNE SHIELD",
        font=font_track,
        fill=(0, 229, 255, 240),
    )

    # Main Project Title
    draw.text((100, 150), "AEGIS // GRID 2.0", font=font_title, fill=(255, 255, 255, 255))
    # Red accent glow on title
    draw.rectangle([(100, 245), (420, 250)], fill=(237, 28, 36, 255))
    draw.rectangle([(425, 245), (550, 250)], fill=(0, 229, 255, 255))

    # Tagline
    draw.text(
        (100, 265),
        "The Autonomous Industrial Immune System for Critical Manufacturing",
        font=font_tagline,
        fill=(180, 205, 230, 255),
    )

    # Six Factory Cells Live Twin Display (Middle section)
    # 6 cells across the width
    cell_w = 260
    cell_h = 240
    start_x = 100
    start_y = 360
    gap = 32

    cells_data = [
        {
            "id": "CELL-01",
            "name": "Precision CNC",
            "temp": "38.2°C",
            "flow": "0.28 kg/s",
            "status": "NOMINAL",
            "color": (0, 230, 118),
        },
        {
            "id": "CELL-02",
            "name": "Thermal Forge",
            "temp": "41.5°C",
            "flow": "0.31 kg/s",
            "status": "NOMINAL",
            "color": (0, 230, 118),
        },
        {
            "id": "CELL-03",
            "name": "Lithography",
            "temp": "68.9°C",
            "flow": "0.04 kg/s",
            "status": "CHOKED / FAULT",
            "color": (237, 28, 36),
        },
        {
            "id": "CELL-04",
            "name": "Cryo Plating",
            "temp": "34.1°C",
            "flow": "0.30 kg/s",
            "status": "NOMINAL",
            "color": (0, 230, 118),
        },
        {
            "id": "CELL-05",
            "name": "Inspection",
            "temp": "36.4°C",
            "flow": "0.29 kg/s",
            "status": "NOMINAL",
            "color": (0, 230, 118),
        },
        {
            "id": "CELL-06",
            "name": "Power Loop",
            "temp": "39.0°C",
            "flow": "0.27 kg/s",
            "status": "NOMINAL",
            "color": (0, 230, 118),
        },
    ]

    for idx, c in enumerate(cells_data):
        cx = start_x + idx * (cell_w + gap)
        cy = start_y
        border_col = c["color"]
        # Card background
        draw.rounded_rectangle(
            [(cx, cy), (cx + cell_w, cy + cell_h)],
            radius=8,
            fill=(15, 22, 34, 240),
            outline=border_col,
            width=2,
        )
        # Header inside card
        draw.rounded_rectangle([(cx, cy), (cx + cell_w, cy + 42)], radius=8, fill=(22, 32, 50, 255))
        draw.text((cx + 14, cy + 12), c["id"], font=font_cell_title, fill=(255, 255, 255, 255))
        draw.text((cx + cell_w - 95, cy + 14), c["status"], font=font_pill, fill=c["color"])
        # Body metrics
        draw.text((cx + 14, cy + 56), c["name"], font=font_mono, fill=(140, 165, 190, 255))
        draw.text((cx + 14, cy + 90), "TEMP:", font=font_mono, fill=(120, 140, 160, 255))
        draw.text((cx + 80, cy + 88), c["temp"], font=font_cell_val, fill=c["color"])
        draw.text((cx + 14, cy + 130), "FLOW:", font=font_mono, fill=(120, 140, 160, 255))
        draw.text((cx + 80, cy + 128), c["flow"], font=font_cell_val, fill=(200, 220, 245, 255))
        # Status footer bar
        draw.line(
            [(cx + 14, cy + 180), (cx + cell_w - 14, cy + 180)], fill=(40, 55, 80, 255), width=1
        )
        if "FAULT" in c["status"]:
            draw.text(
                (cx + 14, cy + 195),
                "🚨 SENTINEL DETECTED ANOMALY",
                font=font_pill,
                fill=(237, 28, 36, 255),
            )
        else:
            draw.text(
                (cx + 14, cy + 195),
                "✓ COUPLED EQUILIBRIUM",
                font=font_pill,
                fill=(0, 230, 118, 255),
            )

    # Architecture Pillars (Bottom section)
    pillars = [
        (
            "C++20 NATIVE DIGITAL TWIN",
            "Rigorous ODE conservation laws, deterministic 6-cell thermal & flow dynamics",
        ),
        (
            "AMD TOKEN FACTORY INFERENCE",
            "LangGraph multi-agent diagnostic & minimax counterfactual tournament",
        ),
        (
            "PINECONE DUAL RETRIEVAL",
            "1,235 native vectors + 103 licensed OEM & NIST references with strict provenance",
        ),
        (
            "WEBAUTHN ASYMMETRIC CONTROL",
            "FIDO2/CTAP2 hardware-bound approval; Ed25519 single-use execution capability",
        ),
    ]

    p_w = 405
    p_h = 170
    p_y = 660

    for i, (p_title, p_desc) in enumerate(pillars):
        px = start_x + i * (p_w + 40)
        draw.rounded_rectangle(
            [(px, p_y), (px + p_w, p_y + p_h)],
            radius=6,
            fill=(13, 19, 30, 230),
            outline=(35, 50, 75, 200),
            width=1,
        )
        # Pillar indicator icon line
        draw.rectangle(
            [(px, p_y), (px + p_w, p_y + 4)],
            fill=(237, 28, 36, 255) if i % 2 == 0 else (0, 229, 255, 255),
        )
        draw.text((px + 16, p_y + 20), p_title, font=font_pill, fill=(255, 255, 255, 255))
        # Wrap description
        words = p_desc.split(" ")
        lines = []
        cur_line = []
        for w in words:
            cur_line.append(w)
            if len(" ".join(cur_line)) > 36:
                lines.append(" ".join(cur_line[:-1]))
                cur_line = [w]
        if cur_line:
            lines.append(" ".join(cur_line))
        for line_idx, text_line in enumerate(lines):
            draw.text(
                (px + 16, p_y + 55 + line_idx * 24),
                text_line,
                font=font_mono,
                fill=(150, 175, 205, 255),
            )

    # Footer Strip (Metrics & Provenance)
    draw.rectangle([(0, HEIGHT - 90), (WIDTH, HEIGHT)], fill=(8, 11, 18, 255))
    draw.line([(0, HEIGHT - 90), (WIDTH, HEIGHT - 90)], fill=(30, 42, 64, 255), width=1)

    metrics_text = (
        "EVALUATED EVIDENCE: 398 Python / 3 CTest / 35 Node / 17 Playwright Checks PASS  |  "
        "Held-Out Diagnosis: 73.0% Recall / 100% Precision  |  "
        "Predictive Horizon: 70.0% Recall / 25s Lead Time"
    )
    draw.text((100, HEIGHT - 65), metrics_text, font=font_mono, fill=(0, 229, 255, 240))
    draw.text(
        (WIDTH - 420, HEIGHT - 65),
        "SHA-256 AUDIT-SEALED RECEIPTS",
        font=font_pill,
        fill=(0, 230, 118, 240),
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT, "PNG")
    print(f"Cover image created: {OUTPUT} ({WIDTH}x{HEIGHT})")


if __name__ == "__main__":
    create_cover()
