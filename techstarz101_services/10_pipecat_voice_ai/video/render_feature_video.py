"""
Renders the 1080x1080 30fps H.264 MP4 product feature video for
Service #10: Pipecat 24/7 Voice AI using the persistent character reference
image (character_01_street_cap_smile.jpg).
"""

from __future__ import annotations

import math
import shutil
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path(__file__).resolve().parent
FRAMES_DIR = OUT_DIR / "_frames"
OUT_MP4 = OUT_DIR / "pipecat_voice_ai_feature.mp4"
CHAR_IMG = Path("C:/Users/tee/.gemini/config/assets/characters/character_01_street_cap_smile.jpg")

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
F_TITLE = load_font(56, True)
F_SUB = load_font(30, False)
F_CARD_T = load_font(30, True)
F_CARD_B = load_font(22, False)
F_STAT = load_font(44, True)


def draw_frame(idx: int, char_avatar: Image.Image) -> Image.Image:
    t = idx / FPS
    img = Image.new("RGB", (W, H), (4, 10, 24))
    draw = ImageDraw.Draw(img)

    # Subtle animated grid
    for x in range(0, W, 90):
        draw.line([(x, 0), (x, H)], fill=(15, 28, 52), width=1)
    for y in range(0, H, 90):
        draw.line([(0, y), (W, y)], fill=(15, 28, 52), width=1)

    # Top header bar
    draw.rounded_rectangle([54, 48, 360, 96], radius=24, fill=(8, 47, 73), outline=(6, 182, 212), width=2)
    draw.text((80, 58), "TS101-SRV-10 · VOICE AI", fill=(103, 232, 249), font=F_BADGE)
    draw.text((770, 58), "techstarz101.com", fill=(148, 163, 184), font=F_BADGE)

    # Character circular portrait with pulsing voice ring
    pulse = int(6 + 6 * math.sin(t * 7.5))
    cx, cy = 890, 235
    draw.ellipse([cx - 115 - pulse, cy - 115 - pulse, cx + 115 + pulse, cy + 115 + pulse], outline=(6, 182, 212), width=4)
    img.paste(char_avatar, (cx - 105, cy - 105), char_avatar)

    # Animated live audio waveform next to portrait
    for b in range(18):
        bx = 60 + b * 36
        bh = int(18 + 38 * abs(math.sin(t * 6.0 + b * 0.45)))
        col = (34, 211, 238) if b % 2 == 0 else (167, 139, 250)
        draw.rounded_rectangle([bx, 330 - bh, bx + 20, 330 + bh], radius=8, fill=col)

    if t < 4.0:
        draw.text((54, 132), "Pipecat 24/7", fill=(255, 255, 255), font=F_TITLE)
        draw.text((54, 198), "Voice AI Receptionist", fill=(56, 189, 248), font=F_TITLE)
        draw.text((54, 270), "Sub-800ms phone answering & live booking", fill=(203, 213, 225), font=F_SUB)

        cards = [
            ("624ms E2E", "Silero VAD -> Speaches STT -> Kokoro TTS", (6, 182, 212)),
            ("$0.004/min", "Zero SaaS voice markup (vs $0.18/min)", (16, 185, 129)),
            ("24/7 Cal.com", "Books appointments & logs CRM mid-call", (139, 92, 246)),
        ]
        for i, (head, desc, col) in enumerate(cards):
            y0 = 430 + i * 165
            draw.rounded_rectangle([54, y0, 1026, y0 + 140], radius=22, fill=(15, 23, 42), outline=col, width=3)
            draw.text((90, y0 + 24), head, fill=col, font=F_STAT)
            draw.text((90, y0 + 84), desc, fill=(226, 232, 240), font=F_CARD_B)
    elif t < 8.0:
        draw.text((54, 132), "2 Open-Source Stacks", fill=(255, 255, 255), font=F_TITLE)
        draw.text((54, 198), "8 Standalone Repos", fill=(192, 132, 252), font=F_TITLE)
        draw.text((54, 270), "Click any icon to boot solo — or stack together", fill=(203, 213, 225), font=F_SUB)

        # Stack A box
        draw.rounded_rectangle([54, 420, 525, 930], radius=24, fill=(11, 22, 42), outline=(6, 182, 212), width=3)
        draw.text((84, 450), "STACK A · WebRTC", fill=(103, 232, 249), font=F_CARD_T)
        for i, item in enumerate(["LiveKit WebRTC (:6500)", "Kokoro-FastAPI (:6510)", "Speaches STT (:6520)", "Cal.com Booking (:6530)"]):
            draw.rounded_rectangle([84, 515 + i * 95, 495, 588 + i * 95], radius=14, fill=(2, 6, 23), outline=(30, 41, 59), width=2)
            draw.text((104, 538 + i * 95), item, fill=(241, 245, 249), font=F_CARD_B)

        # Stack B box
        draw.rounded_rectangle([555, 420, 1026, 930], radius=24, fill=(22, 16, 44), outline=(139, 92, 246), width=3)
        draw.text((585, 450), "STACK B · SIP PBX", fill=(216, 180, 254), font=F_CARD_T)
        for i, item in enumerate(["Asterisk SIP PBX (:6600)", "OpenedAI Piper (:6610)", "Open WebUI Brain (:6620)", "n8n Call Router (:6630)"]):
            draw.rounded_rectangle([585, 515 + i * 95, 996, 588 + i * 95], radius=14, fill=(2, 6, 23), outline=(30, 41, 59), width=2)
            draw.text((605, 538 + i * 95), item, fill=(241, 245, 249), font=F_CARD_B)
    else:
        draw.text((54, 132), "Never Miss a Call", fill=(255, 255, 255), font=F_TITLE)
        draw.text((54, 198), "Own Your Voice Stack", fill=(52, 211, 153), font=F_TITLE)
        draw.text((54, 270), "Live Modular Hub on localhost:7873", fill=(203, 213, 225), font=F_SUB)

        draw.rounded_rectangle([54, 430, 1026, 860], radius=26, fill=(15, 23, 42), outline=(16, 185, 129), width=3)
        draw.text((94, 472), "INCLUDED OUT OF THE BOX:", fill=(110, 231, 183), font=F_CARD_T)
        bullets = [
            "• Dedicated /t/<id> one-click launcher per tool",
            "• Live Sub-800ms Phone Receptionist Simulator",
            "• Pre-built n8n Call Booking & Escalation JSONs",
            "• 100% Self-Hosted — Zero Per-Minute Vendor Lock-In",
        ]
        for i, b in enumerate(bullets):
            draw.text((94, 540 + i * 70), b, fill=(241, 245, 249), font=F_SUB)

        draw.rounded_rectangle([54, 900, 1026, 995], radius=22, fill=(6, 182, 212))
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
        frame = draw_frame(i, avatar)
        frame.save(FRAMES_DIR / f"frame_{i:04d}.png")

    cmd = [
        "ffmpeg",
        "-y",
        "-framerate",
        str(FPS),
        "-i",
        str(FRAMES_DIR / "frame_%04d.png"),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-crf",
        "20",
        str(OUT_MP4),
    ]
    subprocess.run(cmd, check=True)
    shutil.rmtree(FRAMES_DIR)
    print(f"Rendered {OUT_MP4} ({OUT_MP4.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
