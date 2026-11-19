"""
Renders the 1080x1080 30fps H.264 MP4 product feature video for
Service #11: Docling Document RAG using the persistent character reference
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
OUT_MP4 = OUT_DIR / "docling_document_rag_feature.mp4"
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
    img = Image.new("RGB", (W, H), (3, 11, 20))
    draw = ImageDraw.Draw(img)

    for x in range(0, W, 90):
        draw.line([(x, 0), (x, H)], fill=(12, 29, 44), width=1)
    for y in range(0, H, 90):
        draw.line([(0, y), (W, y)], fill=(12, 29, 44), width=1)

    draw.rounded_rectangle([54, 48, 395, 96], radius=24, fill=(6, 46, 36), outline=(16, 185, 129), width=2)
    draw.text((80, 58), "TS101-SRV-11 · DOCLING RAG", fill=(110, 231, 183), font=F_BADGE)
    draw.text((770, 58), "techstarz101.com", fill=(148, 163, 184), font=F_BADGE)

    pulse = int(5 + 5 * math.sin(t * 5.0))
    cx, cy = 890, 235
    draw.ellipse([cx - 115 - pulse, cy - 115 - pulse, cx + 115 + pulse, cy + 115 + pulse], outline=(16, 185, 129), width=4)
    img.paste(char_avatar, (cx - 105, cy - 105), char_avatar)

    # Animated document scan bar
    scan_x = int(60 + (t / DURATION) * 620)
    draw.rounded_rectangle([54, 340, 710, 356], radius=8, fill=(15, 23, 42))
    draw.rounded_rectangle([54, 340, min(710, scan_x + 90), 356], radius=8, fill=(16, 185, 129))

    if t < 4.0:
        draw.text((54, 132), "Docling Document", fill=(255, 255, 255), font=F_TITLE)
        draw.text((54, 198), "RAG Intelligence", fill=(52, 211, 153), font=F_TITLE)
        draw.text((54, 270), "93.6% table accuracy · Zero cloud data leakage", fill=(203, 213, 225), font=F_SUB)

        cards = [
            ("93.6% Tables", "Preserves complex financial & legal PDF grids", (16, 185, 129)),
            ("Hybrid Search", "Qdrant + Weaviate BM25 & dense vectors", (56, 189, 248)),
            ("100% Private", "Self-hosted Paperless-ngx, AnythingLLM & n8n", (129, 140, 248)),
        ]
        for i, (head, desc, col) in enumerate(cards):
            y0 = 425 + i * 165
            draw.rounded_rectangle([54, y0, 1026, y0 + 140], radius=22, fill=(15, 23, 42), outline=col, width=3)
            draw.text((90, y0 + 24), head, fill=col, font=F_STAT)
            draw.text((90, y0 + 84), desc, fill=(226, 232, 240), font=F_CARD_B)
    elif t < 8.0:
        draw.text((54, 132), "2 Open-Source Stacks", fill=(255, 255, 255), font=F_TITLE)
        draw.text((54, 198), "8 Standalone Repos", fill=(129, 140, 248), font=F_TITLE)
        draw.text((54, 270), "Click any icon to boot solo — or stack together", fill=(203, 213, 225), font=F_SUB)

        draw.rounded_rectangle([54, 420, 525, 930], radius=24, fill=(7, 25, 21), outline=(16, 185, 129), width=3)
        draw.text((84, 450), "STACK A · Layout RAG", fill=(110, 231, 183), font=F_CARD_T)
        for i, item in enumerate(["IBM Docling Serve (:6700)", "Qdrant Vector DB (:6710)", "AnythingLLM Studio (:6720)", "Apache Tika OCR (:6730)"]):
            draw.rounded_rectangle([84, 515 + i * 95, 495, 588 + i * 95], radius=14, fill=(2, 6, 23), outline=(30, 41, 59), width=2)
            draw.text((104, 538 + i * 95), item, fill=(241, 245, 249), font=F_CARD_B)

        draw.rounded_rectangle([555, 420, 1026, 930], radius=24, fill=(14, 16, 38), outline=(99, 102, 241), width=3)
        draw.text((585, 450), "STACK B · Vault & Sync", fill=(165, 180, 252), font=F_CARD_T)
        for i, item in enumerate(["Paperless-ngx (:6800)", "Weaviate Hybrid (:6810)", "Open WebUI Chat (:6820)", "n8n Ingest Router (:6830)"]):
            draw.rounded_rectangle([585, 515 + i * 95, 996, 588 + i * 95], radius=14, fill=(2, 6, 23), outline=(30, 41, 59), width=2)
            draw.text((605, 538 + i * 95), item, fill=(241, 245, 249), font=F_CARD_B)
    else:
        draw.text((54, 132), "Stop Losing Data", fill=(255, 255, 255), font=F_TITLE)
        draw.text((54, 198), "In Broken PDF Parsers", fill=(52, 211, 153), font=F_TITLE)
        draw.text((54, 270), "Live Modular Hub on localhost:7874", fill=(203, 213, 225), font=F_SUB)

        draw.rounded_rectangle([54, 430, 1026, 860], radius=26, fill=(15, 23, 42), outline=(16, 185, 129), width=3)
        draw.text((94, 472), "INCLUDED OUT OF THE BOX:", fill=(110, 231, 183), font=F_CARD_T)
        bullets = [
            "• Dedicated /t/<id> one-click launcher per tool",
            "• Live Table-Atomic Extractor & Chunking Simulator",
            "• Pre-built n8n Docling -> Qdrant/Weaviate JSONs",
            "• 100% Self-Hosted — Zero External API Lock-In",
        ]
        for i, b in enumerate(bullets):
            draw.text((94, 540 + i * 70), b, fill=(241, 245, 249), font=F_SUB)

        draw.rounded_rectangle([54, 900, 1026, 995], radius=22, fill=(16, 185, 129))
        draw.text((220, 926), "DEPLOY NOW  ·  TECHSTARZ101.COM", fill=(2, 6, 23), font=F_CARD_T)

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
