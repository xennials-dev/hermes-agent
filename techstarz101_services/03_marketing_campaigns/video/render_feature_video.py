#!/usr/bin/env python3
"""
Feature Video Renderer for Techstarz101 Service #03: Marketing Campaigns.
Uses persistent character reference: character_04_penthouse_lounge_tracksuit.jpg
Output: marketing_campaigns_feature.mp4 (1080x1080, 30fps, 12s)
"""

import os
import shutil
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

CHAR_PATH = r"C:\Users\tee\.gemini\config\assets\characters\character_04_penthouse_lounge_tracksuit.jpg"
OUT_DIR = Path("techstarz101_services/03_marketing_campaigns/video")
OUT_DIR.mkdir(parents=True, exist_ok=True)
FRAMES_DIR = OUT_DIR / "frames"
FRAMES_DIR.mkdir(parents=True, exist_ok=True)

WIDTH, HEIGHT = 1080, 1080
FPS = 30
TOTAL_FRAMES = FPS * 12


def get_font(size: int, bold: bool = False):
    names = ["Arialbd.ttf", "segoeuib.ttf", "Calibrib.ttf"] if bold else ["Arial.ttf", "segoeui.ttf", "Calibri.ttf"]
    for n in names:
        try:
            return ImageFont.truetype(f"C:/Windows/Fonts/{n}", size)
        except Exception:
            pass
    return ImageFont.load_default()


def render_frame(idx: int):
    t = idx / FPS
    img = Image.new("RGB", (WIDTH, HEIGHT), "#070a13")
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, WIDTH, 110], fill=(13, 19, 36))
    draw.line([0, 110, WIDTH, 110], fill=(30, 41, 59), width=2)
    draw.rounded_rectangle([40, 32, 340, 78], radius=23, fill=(30, 41, 59))
    draw.ellipse([58, 48, 72, 62], fill=(56, 189, 248))
    draw.text((86, 44), "TECHSTARZ101 · SERVICE #03", fill=(148, 163, 184), font=get_font(20, True))
    draw.rounded_rectangle([WIDTH - 330, 32, WIDTH - 40, 78], radius=23, fill=(16, 185, 129))
    draw.text((WIDTH - 312, 44), "MULTI-ANGLE A/B ADS", fill=(255, 255, 255), font=get_font(20, True))

    if os.path.exists(CHAR_PATH):
        c = Image.open(CHAR_PATH).convert("RGBA")
        c.thumbnail((250, 250))
        mask = Image.new("L", c.size, 0)
        ImageDraw.Draw(mask).ellipse((0, 0, c.size[0], c.size[1]), fill=255)
        img.paste(c, (WIDTH - 290, 140), mask)
        draw.ellipse([WIDTH - 294, 136, WIDTH - 290 + c.size[0] + 4, 140 + c.size[1] + 4], outline=(56, 189, 248), width=3)

    if t < 3.0:
        draw.text((60, 200), "Stop Guessing Which", fill="#ffffff", font=get_font(52, True))
        draw.text((60, 268), "Ad Angle Converts.", fill="#f43f5e", font=get_font(52, True))
        draw.rounded_rectangle([60, 385, 750, 565], radius=16, fill=(19, 29, 51), outline=(51, 65, 85), width=2)
        draw.text((90, 415), "X  $1,500+/mo for HubSpot + Optimizely + GA", fill="#fca5a5", font=get_font(25, True))
        draw.text((90, 465), "X  Single-angle ads burn budget fast", fill="#fca5a5", font=get_font(25, True))
        draw.text((90, 515), "X  Zero visibility into true campaign ROAS", fill="#fca5a5", font=get_font(25, True))
        draw.text((60, 635), "Launch autonomous multi-angle A/B growth.", fill="#38bdf8", font=get_font(32, True))
    elif t < 6.5:
        draw.text((60, 185), "2 Open-Source Growth Stacks", fill="#ffffff", font=get_font(46, True))
        draw.text((60, 246), "8 Click-to-Launch Standalone Apps", fill="#38bdf8", font=get_font(40, True))
        draw.rounded_rectangle([60, 350, 515, 620], radius=16, fill=(19, 29, 51), outline=(56, 189, 248), width=2)
        draw.text((85, 375), "STACK A · EXPERIMENTATION", fill="#38bdf8", font=get_font(23, True))
        draw.text((85, 420), "• Mautic (Drip Automation)", fill="#e2e8f0", font=get_font(22))
        draw.text((85, 458), "• GrowthBook (Bayesian A/B)", fill="#e2e8f0", font=get_font(22))
        draw.text((85, 496), "• Umami (UTM Attribution)", fill="#e2e8f0", font=get_font(22))
        draw.text((85, 534), "• Shlink (Click Tracking)", fill="#e2e8f0", font=get_font(22))
        draw.text((85, 578), "Zero Contact Tax", fill="#10b981", font=get_font(20, True))

        draw.rounded_rectangle([545, 350, 1020, 620], radius=16, fill=(19, 29, 51), outline=(168, 85, 247), width=2)
        draw.text((570, 375), "STACK B · AD FUNNELS & BI", fill="#c084fc", font=get_font(23, True))
        draw.text((570, 420), "• Listmonk (Campaign Email)", fill="#e2e8f0", font=get_font(22))
        draw.text((570, 458), "• Matomo (Funnel Analytics)", fill="#e2e8f0", font=get_font(22))
        draw.text((570, 496), "• Typebot (Chat Ad Funnels)", fill="#e2e8f0", font=get_font(22))
        draw.text((570, 534), "• Metabase (ROAS & CAC BI)", fill="#e2e8f0", font=get_font(22))
        draw.text((570, 578), "100% Self-Hosted", fill="#10b981", font=get_font(20, True))
    elif t < 9.5:
        draw.text((60, 190), "4 Psychological Ad Angles", fill="#ffffff", font=get_font(48, True))
        draw.text((60, 252), "Auto-Promotes Bayesian Winners", fill="#c084fc", font=get_font(40, True))
        draw.rounded_rectangle([60, 345, 980, 610], radius=16, fill=(15, 23, 42), outline=(99, 102, 241), width=2)
        draw.text((90, 372), "LIVE A/B EXPERIMENT MATRIX (Meta / LinkedIn / Google):", fill="#94a3b8", font=get_font(20, True))
        draw.text((90, 412), "1. Pain / SaaS Tax Angle   -> Variant B (CTR 3.8%, ROAS 12.1x)", fill="#38bdf8", font=get_font(22, True))
        draw.text((90, 454), "2. 48-Hour Speed Guarantee -> Variant A (CTR 3.4%, ROAS 10.6x)", fill="#e2e8f0", font=get_font(22))
        draw.text((90, 496), "3. Sovereign ROI Math      -> Variant B (CTR 4.1%, ROAS 14.4x)", fill="#10b981", font=get_font(22, True))
        draw.text((90, 538), "4. Social Proof & Demo     -> Variant A (CTR 2.9%, ROAS 9.2x)", fill="#e2e8f0", font=get_font(22))
    else:
        draw.text((60, 195), "Run Any Tool Standalone", fill="#ffffff", font=get_font(50, True))
        draw.text((60, 265), "Or Stack Your Growth Engine.", fill="#10b981", font=get_font(44, True))
        draw.rounded_rectangle([60, 360, 1020, 515], radius=16, fill=(19, 29, 51), outline=(16, 185, 129), width=2)
        draw.text((90, 392), "Dedicated App Links:  localhost:7867/t/<tool>", fill="#38bdf8", font=get_font(26, True))
        draw.text((90, 438), "One-Click Docker Compose · Pre-Wired UTM & Webhooks", fill="#e2e8f0", font=get_font(22))
        draw.text((90, 474), "Zero Contact Tax · Full Ownership of Your Ad Data", fill="#10b981", font=get_font(20, True))
        draw.rounded_rectangle([60, 555, 1020, 680], radius=16, fill=(56, 189, 248))
        draw.text((WIDTH // 2, 598), "FLAT $390 48-HOUR STARTER SPRINT", fill="#070a13", font=get_font(34, True), anchor="mm")
        draw.text((WIDTH // 2, 645), "https://techstarz101.com/agents/marketing-campaign", fill="#0f172a", font=get_font(21, True), anchor="mm")

    draw.rectangle([0, HEIGHT - 80, WIDTH, HEIGHT], fill=(13, 19, 36))
    draw.text((60, HEIGHT - 52), "Techstarz101.com · Mautic · GrowthBook · Umami · Shlink · Listmonk · Metabase", fill="#64748b", font=get_font(17))
    draw.text((WIDTH - 240, HEIGHT - 52), "100% OPEN SOURCE", fill="#10b981", font=get_font(18, True))
    img.save(FRAMES_DIR / f"frame_{idx:04d}.png")


def main():
    for i in range(TOTAL_FRAMES):
        render_frame(i)
    mp4 = OUT_DIR / "marketing_campaigns_feature.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-framerate", str(FPS),
        "-i", str(FRAMES_DIR / "frame_%04d.png"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "fast",
        str(mp4)
    ], check=True)
    shutil.rmtree(FRAMES_DIR)
    print(f"DONE: {mp4} ({os.path.getsize(mp4)/1024/1024:.2f} MB)")


if __name__ == "__main__":
    main()
