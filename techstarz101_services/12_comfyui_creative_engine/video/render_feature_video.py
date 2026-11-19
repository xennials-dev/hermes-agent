"""
Renders the 1080x1080 30fps H.264 MP4 product feature video for
Service #12: ComfyUI Creative Engine using the persistent character reference
image (character_04_penthouse_lounge_tracksuit.jpg).
"""

from __future__ import annotations

import math
import shutil
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path(__file__).resolve().parent
FRAMES_DIR = OUT_DIR / "_frames"
OUT_MP4 = OUT_DIR / "comfyui_creative_engine_feature.mp4"
CHAR_IMG = Path("C:/Users/tee/.gemini/config/assets/characters/character_04_penthouse_lounge_tracksuit.jpg")

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
    img = Image.new("RGB", (W, H), (14, 6, 26))
    draw = ImageDraw.Draw(img)

    for x in range(0, W, 90):
        draw.line([(x, 0), (x, H)], fill=(30, 15, 50), width=1)
    for y in range(0, H, 90):
        draw.line([(0, y), (W, y)], fill=(30, 15, 50), width=1)

    draw.rounded_rectangle([54, 48, 415, 96], radius=24, fill=(58, 12, 68), outline=(217, 70, 239), width=2)
    draw.text((80, 58), "TS101-SRV-12 · COMFYUI", fill=(240, 171, 252), font=F_BADGE)
    draw.text((770, 58), "techstarz101.com", fill=(148, 163, 184), font=F_BADGE)

    pulse = int(6 + 6 * math.sin(t * 6.0))
    cx, cy = 890, 235
    draw.ellipse([cx - 115 - pulse, cy - 115 - pulse, cx + 115 + pulse, cy + 115 + pulse], outline=(217, 70, 239), width=4)
    img.paste(char_avatar, (cx - 105, cy - 105), char_avatar)

    # Animated node-graph connection dots
    for n in range(6):
        nx = 72 + n * 120
        ny = 345 + int(10 * math.sin(t * 4.0 + n))
        if n < 5:
            ny2 = 345 + int(10 * math.sin(t * 4.0 + n + 1))
            draw.line([(nx, ny), (nx + 120, ny2)], fill=(217, 70, 239), width=3)
        draw.ellipse([nx - 12, ny - 12, nx + 12, ny + 12], fill=(245, 158, 11), outline=(255, 255, 255), width=2)

    if t < 4.0:
        draw.text((54, 132), "ComfyUI Creative", fill=(255, 255, 255), font=F_TITLE)
        draw.text((54, 198), "Visual & Video Engine", fill=(232, 121, 249), font=F_TITLE)
        draw.text((54, 270), "Automated product shoots & 9:16 ad reels", fill=(203, 213, 225), font=F_SUB)

        cards = [
            ("$0.002/Render", "99.4% cheaper than commercial creative SaaS", (217, 70, 239)),
            ("Node-Graph API", "Reproducible Flux/SDXL & Rembg cutouts", (245, 158, 11)),
            ("9:16 + 1:1 + 16:9", "Auto-resized via imgproxy & NCA FFmpeg", (52, 211, 153)),
        ]
        for i, (head, desc, col) in enumerate(cards):
            y0 = 425 + i * 165
            draw.rounded_rectangle([54, y0, 1026, y0 + 140], radius=22, fill=(18, 14, 34), outline=col, width=3)
            draw.text((90, y0 + 24), head, fill=col, font=F_STAT)
            draw.text((90, y0 + 84), desc, fill=(226, 232, 240), font=F_CARD_B)
    elif t < 8.0:
        draw.text((54, 132), "2 Open-Source Stacks", fill=(255, 255, 255), font=F_TITLE)
        draw.text((54, 198), "8 Standalone Repos", fill=(251, 191, 36), font=F_TITLE)
        draw.text((54, 270), "Click any icon to boot solo — or stack together", fill=(203, 213, 225), font=F_SUB)

        draw.rounded_rectangle([54, 420, 525, 930], radius=24, fill=(23, 9, 34), outline=(217, 70, 239), width=3)
        draw.text((84, 450), "STACK A · Node Studio", fill=(240, 171, 252), font=F_CARD_T)
        for i, item in enumerate(["ComfyUI Studio (:6900)", "Rembg Cutout API (:6910)", "MinIO S3 Vault (:6920)", "imgproxy CDN (:6930)"]):
            draw.rounded_rectangle([84, 515 + i * 95, 495, 588 + i * 95], radius=14, fill=(6, 4, 16), outline=(45, 25, 65), width=2)
            draw.text((104, 538 + i * 95), item, fill=(241, 245, 249), font=F_CARD_B)

        draw.rounded_rectangle([555, 420, 1026, 930], radius=24, fill=(26, 18, 7), outline=(245, 158, 11), width=3)
        draw.text((585, 450), "STACK B · Reels & DAM", fill=(253, 230, 138), font=F_CARD_T)
        for i, item in enumerate(["InvokeAI Canvas (:7000)", "NCA FFmpeg API (:7010)", "PhotoPrism DAM (:7020)", "n8n Creative Hub (:7030)"]):
            draw.rounded_rectangle([585, 515 + i * 95, 996, 588 + i * 95], radius=14, fill=(6, 4, 16), outline=(55, 40, 18), width=2)
            draw.text((605, 538 + i * 95), item, fill=(241, 245, 249), font=F_CARD_B)
    else:
        draw.text((54, 132), "Unlimited Ad Creatives", fill=(255, 255, 255), font=F_TITLE)
        draw.text((54, 198), "Zero Credit Limits", fill=(232, 121, 249), font=F_TITLE)
        draw.text((54, 270), "Live Modular Hub on localhost:7876", fill=(203, 213, 225), font=F_SUB)

        draw.rounded_rectangle([54, 430, 1026, 860], radius=26, fill=(18, 14, 34), outline=(217, 70, 239), width=3)
        draw.text((94, 472), "INCLUDED OUT OF THE BOX:", fill=(240, 171, 252), font=F_CARD_T)
        bullets = [
            "• Dedicated /t/<id> one-click launcher per tool",
            "• Live ComfyUI API JSON Workflow Graph Compiler",
            "• Pre-built n8n Batch SKU & Reel Assembly JSONs",
            "• 100% Self-Hosted — Own Every Model & Asset",
        ]
        for i, b in enumerate(bullets):
            draw.text((94, 540 + i * 70), b, fill=(241, 245, 249), font=F_SUB)

        draw.rounded_rectangle([54, 900, 1026, 995], radius=22, fill=(217, 70, 239))
        draw.text((220, 926), "DEPLOY NOW  ·  TECHSTARZ101.COM", fill=(10, 4, 20), font=F_CARD_T)

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
