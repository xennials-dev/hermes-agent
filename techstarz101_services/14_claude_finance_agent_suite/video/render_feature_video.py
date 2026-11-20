"""
Renders the 1080x1080 30fps H.264 MP4 product feature video for
Service #14: Claude Finance Agent Suite using the persistent character reference
image (character_03_executive_suite_suit.jpg).
"""

from __future__ import annotations

import math
import shutil
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path(__file__).resolve().parent
FRAMES_DIR = OUT_DIR / "_frames"
OUT_MP4 = OUT_DIR / "claude_finance_agent_suite_feature.mp4"
CHAR_IMG = Path("C:/Users/tee/.gemini/config/assets/characters/character_03_executive_suite_suit.jpg")

W, H = 1080, 1080
FPS = 30
DURATION = 12
TOTAL_FRAMES = FPS * DURATION


def load_font(size: int, bold: bool = False):
    candidates = (
        ["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf"]
        if bold
        else ["C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf"]
    )
    for c in candidates:
        if Path(c).exists():
            return ImageFont.truetype(c, size)
    return ImageFont.load_default()


F_BADGE = load_font(24, True)
F_TITLE = load_font(54, True)
F_SUB = load_font(29, False)
F_CARD_T = load_font(30, True)
F_CARD_B = load_font(22, False)
F_STAT = load_font(44, True)


def draw_frame(idx: int, char_avatar: Image.Image) -> Image.Image:
    t = idx / FPS
    img = Image.new("RGB", (W, H), (12, 10, 6))
    draw = ImageDraw.Draw(img)

    for x in range(0, W, 90):
        draw.line([(x, 0), (x, H)], fill=(30, 24, 14), width=1)
    for y in range(0, H, 90):
        draw.line([(0, y), (W, y)], fill=(30, 24, 14), width=1)

    draw.rounded_rectangle([54, 48, 435, 96], radius=24, fill=(52, 34, 8), outline=(245, 158, 11), width=2)
    draw.text((80, 58), "TS101-SRV-14 · FINANCE AI", fill=(253, 230, 138), font=F_BADGE)
    draw.text((770, 58), "techstarz101.com", fill=(148, 163, 184), font=F_BADGE)

    pulse = int(6 + 5 * math.sin(t * 5.0))
    cx, cy = 890, 235
    draw.ellipse([cx - 115 - pulse, cy - 115 - pulse, cx + 115 + pulse, cy + 115 + pulse], outline=(245, 158, 11), width=4)
    img.paste(char_avatar, (cx - 105, cy - 105), char_avatar)

    # Animated stock/EBITDA chart line
    pts = []
    for k in range(14):
        px = 60 + k * 48
        py = 365 - int(22 + 16 * math.sin(t * 3.5 + k * 0.5) + k * 3.2)
        pts.append((px, py))
    draw.line(pts, fill=(16, 185, 129), width=4)

    if t < 4.0:
        draw.text((54, 132), "Claude Finance", fill=(255, 255, 255), font=F_TITLE)
        draw.text((54, 198), "10-Agent IB/PE/KYC", fill=(251, 191, 36), font=F_TITLE)
        draw.text((54, 270), "Institutional DCF, LBO & OFAC/PEP diligence", fill=(203, 213, 225), font=F_SUB)

        cards = [
            ("10 Agents", "EDGAR -> Comps -> DCF -> LBO -> QoE -> IC Memo", (245, 158, 11)),
            ("OFAC & PEP KYC", "Real-time OpenSanctions Yente UBO screening", (16, 185, 129)),
            ("Full Audit Trail", "Immutable citation hashes in Langfuse ledger", (56, 189, 248)),
        ]
        for i, (head, desc, col) in enumerate(cards):
            y0 = 425 + i * 165
            draw.rounded_rectangle([54, y0, 1026, y0 + 140], radius=22, fill=(22, 18, 12), outline=col, width=3)
            draw.text((90, y0 + 24), head, fill=col, font=F_STAT)
            draw.text((90, y0 + 84), desc, fill=(226, 232, 240), font=F_CARD_B)
    elif t < 8.0:
        draw.text((54, 132), "2 Open-Source Stacks", fill=(255, 255, 255), font=F_TITLE)
        draw.text((54, 198), "8 Standalone Repos", fill=(52, 211, 153), font=F_TITLE)
        draw.text((54, 270), "Click any icon to boot solo — or stack together", fill=(203, 213, 225), font=F_SUB)

        draw.rounded_rectangle([54, 420, 525, 930], radius=24, fill=(26, 20, 7), outline=(245, 158, 11), width=3)
        draw.text((84, 450), "STACK A · IB & PE", fill=(253, 230, 138), font=F_CARD_T)
        for i, item in enumerate(["OpenBB API (:7300)", "Jupyter Quant (:7310)", "Docling 10-K (:7320)", "Metabase IC (:7330)"]):
            draw.rounded_rectangle([84, 515 + i * 95, 495, 588 + i * 95], radius=14, fill=(10, 8, 4), outline=(55, 42, 18), width=2)
            draw.text((104, 538 + i * 95), item, fill=(241, 245, 249), font=F_CARD_B)

        draw.rounded_rectangle([555, 420, 1026, 930], radius=24, fill=(7, 25, 21), outline=(16, 185, 129), width=3)
        draw.text((585, 450), "STACK B · KYC & Audit", fill=(110, 231, 183), font=F_CARD_T)
        for i, item in enumerate(["Yente KYC (:7400)", "NocoDB Deal Room (:7410)", "Langfuse Audit (:7420)", "n8n 10-Agent Hub (:7430)"]):
            draw.rounded_rectangle([585, 515 + i * 95, 996, 588 + i * 95], radius=14, fill=(4, 14, 12), outline=(20, 52, 42), width=2)
            draw.text((605, 538 + i * 95), item, fill=(241, 245, 249), font=F_CARD_B)
    else:
        draw.text((54, 132), "Institutional Grade", fill=(255, 255, 255), font=F_TITLE)
        draw.text((54, 198), "100% On-Premise", fill=(251, 191, 36), font=F_TITLE)
        draw.text((54, 270), "Live Modular Hub on localhost:7878", fill=(203, 213, 225), font=F_SUB)

        draw.rounded_rectangle([54, 430, 1026, 860], radius=26, fill=(22, 18, 12), outline=(245, 158, 11), width=3)
        draw.text((94, 472), "INCLUDED OUT OF THE BOX:", fill=(253, 230, 138), font=F_CARD_T)
        bullets = [
            "• Dedicated /t/<id> one-click launcher per tool",
            "• Live 10-Agent DCF / LBO MOIC / IRR Simulator",
            "• Pre-built n8n CIM-to-IC-Memo & KYC JSONs",
            "• Zero Cloud Data Leakage — Own Every Ledger",
        ]
        for i, b in enumerate(bullets):
            draw.text((94, 540 + i * 70), b, fill=(241, 245, 249), font=F_SUB)

        draw.rounded_rectangle([54, 900, 1026, 995], radius=22, fill=(245, 158, 11))
        draw.text((220, 926), "DEPLOY NOW  ·  TECHSTARZ101.COM", fill=(12, 10, 6), font=F_CARD_T)

    return img


def main() -> None:
    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)

    raw = Image.open(CHAR_IMG).convert("RGBA")
    side = min(raw.size)
    left = (raw.width - side) // 2
    top = (raw.height - side) // 2
    crop = raw.crop((left, top, left + side, top + side)).resize((210, 210), Image.Resampling.LANCZOS)
    mask = Image.new("L", (210, 210), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, 210, 210], fill=255)
    avatar = Image.new("RGBA", (210, 210), (0, 0, 0, 0))
    avatar.paste(crop, (0, 0), mask)

    for i in range(TOTAL_FRAMES):
        draw_frame(i, avatar).save(FRAMES_DIR / f"frame_{i:04d}.png")

    subprocess.run(
        [
            "ffmpeg", "-y", "-framerate", str(FPS),
            "-i", str(FRAMES_DIR / "frame_%04d.png"),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
            str(OUT_MP4),
        ],
        check=True,
    )
    shutil.rmtree(FRAMES_DIR)
    print(f"Rendered {OUT_MP4} ({OUT_MP4.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
