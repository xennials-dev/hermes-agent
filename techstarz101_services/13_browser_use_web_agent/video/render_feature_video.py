"""
Renders the 1080x1080 30fps H.264 MP4 product feature video for
Service #13: Browser-Use Web Agent using the persistent character reference
image (character_02_podcast_studio_mic.jpg).
"""

from __future__ import annotations

import math
import shutil
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path(__file__).resolve().parent
FRAMES_DIR = OUT_DIR / "_frames"
OUT_MP4 = OUT_DIR / "browser_use_web_agent_feature.mp4"
CHAR_IMG = Path("C:/Users/tee/.gemini/config/assets/characters/character_02_podcast_studio_mic.jpg")

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
    img = Image.new("RGB", (W, H), (4, 12, 26))
    draw = ImageDraw.Draw(img)

    for x in range(0, W, 90):
        draw.line([(x, 0), (x, H)], fill=(12, 30, 56), width=1)
    for y in range(0, H, 90):
        draw.line([(0, y), (W, y)], fill=(12, 30, 56), width=1)

    draw.rounded_rectangle([54, 48, 430, 96], radius=24, fill=(8, 44, 72), outline=(14, 165, 233), width=2)
    draw.text((80, 58), "TS101-SRV-13 · BROWSER RPA", fill=(125, 211, 252), font=F_BADGE)
    draw.text((770, 58), "techstarz101.com", fill=(148, 163, 184), font=F_BADGE)

    pulse = int(6 + 5 * math.sin(t * 5.5))
    cx, cy = 890, 235
    draw.ellipse([cx - 115 - pulse, cy - 115 - pulse, cx + 115 + pulse, cy + 115 + pulse], outline=(14, 165, 233), width=4)
    img.paste(char_avatar, (cx - 105, cy - 105), char_avatar)

    # Animated browser progress bar
    prog = int(60 + ((t % 4.0) / 4.0) * 620)
    draw.rounded_rectangle([54, 340, 710, 356], radius=8, fill=(15, 23, 42))
    draw.rounded_rectangle([54, 340, min(710, prog), 356], radius=8, fill=(14, 165, 233))

    if t < 4.0:
        draw.text((54, 132), "Browser-Use", fill=(255, 255, 255), font=F_TITLE)
        draw.text((54, 198), "Zero-API Web Agent", fill=(56, 189, 248), font=F_TITLE)
        draw.text((54, 270), "Automate any legacy portal without an API", fill=(203, 213, 225), font=F_SUB)

        cards = [
            ("Zero-API RPA", "Steel & Browserless isolated CDP sandboxes", (14, 165, 233)),
            ("Live 2FA Handoff", "Watch & intervene live via Selenium noVNC", (20, 184, 166)),
            ("24/7 Monitoring", "ChangeDetection diffs -> Windmill & n8n", (52, 211, 153)),
        ]
        for i, (head, desc, col) in enumerate(cards):
            y0 = 425 + i * 165
            draw.rounded_rectangle([54, y0, 1026, y0 + 140], radius=22, fill=(12, 22, 40), outline=col, width=3)
            draw.text((90, y0 + 24), head, fill=col, font=F_STAT)
            draw.text((90, y0 + 84), desc, fill=(226, 232, 240), font=F_CARD_B)
    elif t < 8.0:
        draw.text((54, 132), "2 Open-Source Stacks", fill=(255, 255, 255), font=F_TITLE)
        draw.text((54, 198), "8 Standalone Repos", fill=(45, 212, 191), font=F_TITLE)
        draw.text((54, 270), "Click any icon to boot solo — or stack together", fill=(203, 213, 225), font=F_SUB)

        draw.rounded_rectangle([54, 420, 525, 930], radius=24, fill=(7, 24, 40), outline=(14, 165, 233), width=3)
        draw.text((84, 450), "STACK A · AI Sandbox", fill=(125, 211, 252), font=F_CARD_T)
        for i, item in enumerate(["Browserless CDP (:7100)", "Crawl4AI Extractor (:7110)", "Steel AI Browser (:7120)", "ChangeDetection (:7130)"]):
            draw.rounded_rectangle([84, 515 + i * 95, 495, 588 + i * 95], radius=14, fill=(2, 6, 23), outline=(30, 41, 59), width=2)
            draw.text((104, 538 + i * 95), item, fill=(241, 245, 249), font=F_CARD_B)

        draw.rounded_rectangle([555, 420, 1026, 930], radius=24, fill=(7, 30, 30), outline=(20, 184, 166), width=3)
        draw.text((585, 450), "STACK B · Portal RPA", fill=(94, 234, 212), font=F_CARD_T)
        for i, item in enumerate(["Selenium + noVNC (:7200)", "Windmill RPA (:7210)", "Activepieces Glue (:7220)", "n8n RPA Hub (:7230)"]):
            draw.rounded_rectangle([585, 515 + i * 95, 996, 588 + i * 95], radius=14, fill=(2, 6, 23), outline=(30, 41, 59), width=2)
            draw.text((605, 538 + i * 95), item, fill=(241, 245, 249), font=F_CARD_B)
    else:
        draw.text((54, 132), "Replace Manual", fill=(255, 255, 255), font=F_TITLE)
        draw.text((54, 198), "Portal Busywork", fill=(56, 189, 248), font=F_TITLE)
        draw.text((54, 270), "Live Modular Hub on localhost:7877", fill=(203, 213, 225), font=F_SUB)

        draw.rounded_rectangle([54, 430, 1026, 860], radius=26, fill=(12, 22, 40), outline=(14, 165, 233), width=3)
        draw.text((94, 472), "INCLUDED OUT OF THE BOX:", fill=(125, 211, 252), font=F_CARD_T)
        bullets = [
            "• Dedicated /t/<id> one-click launcher per tool",
            "• Live Browser-Use & Playwright Script Compiler",
            "• Pre-built n8n Crawl4AI & ChangeDetection JSONs",
            "• Domain Allowlists + Human-in-the-Loop 2FA Gates",
        ]
        for i, b in enumerate(bullets):
            draw.text((94, 540 + i * 70), b, fill=(241, 245, 249), font=F_SUB)

        draw.rounded_rectangle([54, 900, 1026, 995], radius=22, fill=(14, 165, 233))
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
