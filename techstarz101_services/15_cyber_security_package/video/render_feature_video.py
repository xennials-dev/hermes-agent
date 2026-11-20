"""
Renders the 1080x1080 30fps H.264 MP4 product feature video for
Service #15: Cyber Security Package using the persistent character reference
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
OUT_MP4 = OUT_DIR / "cyber_security_package_feature.mp4"
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
F_TITLE = load_font(54, True)
F_SUB = load_font(29, False)
F_CARD_T = load_font(30, True)
F_CARD_B = load_font(22, False)
F_STAT = load_font(44, True)


def draw_frame(idx: int, char_avatar: Image.Image) -> Image.Image:
    t = idx / FPS
    img = Image.new("RGB", (W, H), (14, 5, 12))
    draw = ImageDraw.Draw(img)

    for x in range(0, W, 90):
        draw.line([(x, 0), (x, H)], fill=(36, 12, 24), width=1)
    for y in range(0, H, 90):
        draw.line([(0, y), (W, y)], fill=(36, 12, 24), width=1)

    draw.rounded_rectangle([54, 48, 435, 96], radius=24, fill=(64, 12, 28), outline=(244, 63, 94), width=2)
    draw.text((80, 58), "TS101-SRV-15 · CYBER SOC", fill=(253, 164, 175), font=F_BADGE)
    draw.text((770, 58), "techstarz101.com", fill=(148, 163, 184), font=F_BADGE)

    pulse = int(6 + 6 * math.sin(t * 6.5))
    cx, cy = 890, 235
    draw.ellipse([cx - 115 - pulse, cy - 115 - pulse, cx + 115 + pulse, cy + 115 + pulse], outline=(244, 63, 94), width=4)
    img.paste(char_avatar, (cx - 105, cy - 105), char_avatar)

    # Animated radar sweep bar
    sweep = int(60 + abs(math.sin(t * 2.2)) * 620)
    draw.rounded_rectangle([54, 340, 710, 356], radius=8, fill=(24, 12, 20))
    draw.rounded_rectangle([max(54, sweep - 80), 340, min(710, sweep + 80), 356], radius=8, fill=(244, 63, 94))

    if t < 4.0:
        draw.text((54, 132), "Cyber Security", fill=(255, 255, 255), font=F_TITLE)
        draw.text((54, 198), "Zero-Trust SOC Suite", fill=(251, 113, 133), font=F_TITLE)
        draw.text((54, 270), "SAST, DAST, CVE scanning, IPS & SOAR", fill=(203, 213, 225), font=F_SUB)

        cards = [
            ("AppSec + CVEs", "OWASP ZAP, Aqua Trivy & SonarQube SAST", (244, 63, 94)),
            ("Active IPS", "CrowdSec real-time bouncer + Uptime TLS", (6, 182, 212)),
            ("Zero-Trust SOC", "Vaultwarden secrets + CyberChef + n8n SOAR", (16, 185, 129)),
        ]
        for i, (head, desc, col) in enumerate(cards):
            y0 = 425 + i * 165
            draw.rounded_rectangle([54, y0, 1026, y0 + 140], radius=22, fill=(22, 10, 18), outline=col, width=3)
            draw.text((90, y0 + 24), head, fill=col, font=F_STAT)
            draw.text((90, y0 + 84), desc, fill=(226, 232, 240), font=F_CARD_B)
    elif t < 8.0:
        draw.text((54, 132), "2 Open-Source Stacks", fill=(255, 255, 255), font=F_TITLE)
        draw.text((54, 198), "8 Standalone Repos", fill=(56, 189, 248), font=F_TITLE)
        draw.text((54, 270), "Click any icon to boot solo — or stack together", fill=(203, 213, 225), font=F_SUB)

        draw.rounded_rectangle([54, 420, 525, 930], radius=24, fill=(27, 9, 18), outline=(244, 63, 94), width=3)
        draw.text((84, 450), "STACK A · AppSec", fill=(253, 164, 175), font=F_CARD_T)
        for i, item in enumerate(["OWASP ZAP (:7500)", "Aqua Trivy (:7510)", "SonarQube SAST (:7520)", "Uptime Kuma (:7530)"]):
            draw.rounded_rectangle([84, 515 + i * 95, 495, 588 + i * 95], radius=14, fill=(10, 4, 8), outline=(64, 18, 34), width=2)
            draw.text((104, 538 + i * 95), item, fill=(241, 245, 249), font=F_CARD_B)

        draw.rounded_rectangle([555, 420, 1026, 930], radius=24, fill=(7, 24, 36), outline=(6, 182, 212), width=3)
        draw.text((585, 450), "STACK B · SOC & IPS", fill=(103, 232, 249), font=F_CARD_T)
        for i, item in enumerate(["CrowdSec IPS (:7600)", "Vaultwarden (:7610)", "GCHQ CyberChef (:7620)", "n8n SOAR Hub (:7630)"]):
            draw.rounded_rectangle([585, 515 + i * 95, 996, 588 + i * 95], radius=14, fill=(4, 12, 18), outline=(18, 48, 66), width=2)
            draw.text((605, 538 + i * 95), item, fill=(241, 245, 249), font=F_CARD_B)
    else:
        draw.text((54, 132), "Harden Your Stack", fill=(255, 255, 255), font=F_TITLE)
        draw.text((54, 198), "24/7 Autonomous Defense", fill=(251, 113, 133), font=F_TITLE)
        draw.text((54, 270), "Live Modular Hub on localhost:7879", fill=(203, 213, 225), font=F_SUB)

        draw.rounded_rectangle([54, 430, 1026, 860], radius=26, fill=(22, 10, 18), outline=(244, 63, 94), width=3)
        draw.text((94, 472), "INCLUDED OUT OF THE BOX:", fill=(253, 164, 175), font=F_CARD_T)
        bullets = [
            "• Dedicated /t/<id> one-click launcher per tool",
            "• Live HTTP Header, Secret & Container Auditor",
            "• Pre-built n8n Trivy CVE & CrowdSec SOAR JSONs",
            "• 100% Open-Source — Own Your Entire SOC",
        ]
        for i, b in enumerate(bullets):
            draw.text((94, 540 + i * 70), b, fill=(241, 245, 249), font=F_SUB)

        draw.rounded_rectangle([54, 900, 1026, 995], radius=22, fill=(244, 63, 94))
        draw.text((220, 926), "DEPLOY NOW  ·  TECHSTARZ101.COM", fill=(255, 255, 255), font=F_CARD_T)

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
