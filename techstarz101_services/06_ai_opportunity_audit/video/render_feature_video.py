#!/usr/bin/env python3
"""
Feature Video Renderer for Techstarz101 Service #06: AI Opportunity Audit ($750).
Uses persistent character reference: character_02_podcast_studio_mic.jpg
Output: ai_opportunity_audit_feature.mp4 (1080x1080, 30fps, 12s)
"""

import os
import shutil
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

CHAR_PATH = r"C:\Users\tee\.gemini\config\assets\characters\character_02_podcast_studio_mic.jpg"
OUT_DIR = Path("techstarz101_services/06_ai_opportunity_audit/video")
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
    draw.text((86, 44), "TECHSTARZ101 · SERVICE #06", fill=(148, 163, 184), font=get_font(20, True))
    draw.rounded_rectangle([WIDTH - 355, 32, WIDTH - 40, 78], radius=23, fill=(16, 185, 129))
    draw.text((WIDTH - 332, 44), "360° AI AUDIT · 100% CREDIT", fill=(255, 255, 255), font=get_font(19, True))

    if os.path.exists(CHAR_PATH):
        c = Image.open(CHAR_PATH).convert("RGBA")
        c.thumbnail((250, 250))
        mask = Image.new("L", c.size, 0)
        ImageDraw.Draw(mask).ellipse((0, 0, c.size[0], c.size[1]), fill=255)
        img.paste(c, (WIDTH - 290, 140), mask)
        draw.ellipse([WIDTH - 294, 136, WIDTH - 290 + c.size[0] + 4, 140 + c.size[1] + 4], outline=(16, 185, 129), width=3)

    if t < 3.0:
        draw.text((60, 200), "Where Is Your Business", fill="#ffffff", font=get_font(52, True))
        draw.text((60, 268), "Leaking SaaS & Labor Cash?", fill="#f43f5e", font=get_font(48, True))
        draw.rounded_rectangle([60, 385, 750, 565], radius=16, fill=(19, 29, 51), outline=(51, 65, 85), width=2)
        draw.text((90, 415), "• 360° Operational & SaaS Spend Tear-Down", fill="#38bdf8", font=get_font(24, True))
        draw.text((90, 465), "• Exact 90-Day Sovereign AI Automation Roadmap", fill="#10b981", font=get_font(24, True))
        draw.text((90, 515), "• 100% of $750 Credited Toward Your Full Build", fill="#c084fc", font=get_font(24, True))
        draw.text((60, 635), "Zero guesswork. Payback in under 30 days.", fill="#ffffff", font=get_font(31, True))
    elif t < 6.5:
        draw.text((60, 185), "2 Open-Source Audit Stacks", fill="#ffffff", font=get_font(46, True))
        draw.text((60, 248), "8 Click-to-Launch Standalone Apps", fill="#38bdf8", font=get_font(40, True))
        draw.rounded_rectangle([60, 350, 515, 620], radius=16, fill=(19, 29, 51), outline=(56, 189, 248), width=2)
        draw.text((85, 375), "STACK A · DISCOVERY & SOW", fill="#38bdf8", font=get_font(23, True))
        draw.text((85, 420), "• Formbricks (360° Intake)", fill="#e2e8f0", font=get_font(22))
        draw.text((85, 458), "• Cal.com (Kickoff Booking)", fill="#e2e8f0", font=get_font(22))
        draw.text((85, 496), "• BookStack (Roadmap Wiki)", fill="#e2e8f0", font=get_font(22))
        draw.text((85, 534), "• DocuSeal ($750 SOW E-Sign)", fill="#e2e8f0", font=get_font(22))
        draw.text((85, 578), "Zero Client Friction", fill="#10b981", font=get_font(20, True))

        draw.rounded_rectangle([545, 350, 1020, 620], radius=16, fill=(19, 29, 51), outline=(168, 85, 247), width=2)
        draw.text((570, 375), "STACK B · ROI & DELIVERY", fill="#c084fc", font=get_font(23, True))
        draw.text((570, 420), "• Excalidraw (Live Mapping)", fill="#e2e8f0", font=get_font(22))
        draw.text((570, 458), "• Grist (ROI Spreadsheet)", fill="#e2e8f0", font=get_font(22))
        draw.text((570, 496), "• Stirling-PDF (Exec Deck)", fill="#e2e8f0", font=get_font(22))
        draw.text((570, 534), "• Kimai (Credit Invoicing)", fill="#e2e8f0", font=get_font(22))
        draw.text((570, 578), "100% Open Source", fill="#10b981", font=get_font(20, True))
    elif t < 9.5:
        draw.text((60, 190), "Instant 360° ROI Scorecard", fill="#ffffff", font=get_font(48, True))
        draw.text((60, 252), "Real Numbers Before You Build", fill="#10b981", font=get_font(40, True))
        draw.rounded_rectangle([60, 345, 980, 610], radius=16, fill=(15, 23, 42), outline=(99, 102, 241), width=2)
        draw.text((90, 375), "SAMPLE 18-PERSON AGENCY AUDIT SCORECARD:", fill="#94a3b8", font=get_font(20, True))
        draw.text((90, 420), "• Annualized SaaS Savings (68%):   $22,848 / yr", fill="#38bdf8", font=get_font(23, True))
        draw.text((90, 465), "• Reclaimed Labor (1,152 hrs/yr):  $63,360 / yr", fill="#c084fc", font=get_font(23, True))
        draw.text((90, 510), "• Total Annual Operational Impact: $86,208 / yr", fill="#10b981", font=get_font(24, True))
        draw.text((90, 555), "• Estimated Payback Period:        14 Days", fill="#ffffff", font=get_font(23, True))
    else:
        draw.text((60, 195), "Book Your $750 Audit.", fill="#ffffff", font=get_font(52, True))
        draw.text((60, 265), "100% Credited to Your Build.", fill="#10b981", font=get_font(44, True))
        draw.rounded_rectangle([60, 360, 1020, 515], radius=16, fill=(19, 29, 51), outline=(16, 185, 129), width=2)
        draw.text((90, 392), "Dedicated App Links:  localhost:7870/t/<tool>", fill="#38bdf8", font=get_font(26, True))
        draw.text((90, 438), "Formbricks · Cal.com · BookStack · DocuSeal · Excalidraw · Grist", fill="#e2e8f0", font=get_font(20))
        draw.text((90, 474), "Executive PDF Report + 90-Day Roadmap Included", fill="#10b981", font=get_font(20, True))
        draw.rounded_rectangle([60, 555, 1020, 680], radius=16, fill=(56, 189, 248))
        draw.text((WIDTH // 2, 598), "$750 AI OPPORTUNITY AUDIT (100% CREDITED)", fill="#070a13", font=get_font(32, True), anchor="mm")
        draw.text((WIDTH // 2, 645), "https://techstarz101.com/audit", fill="#0f172a", font=get_font(22, True), anchor="mm")

    draw.rectangle([0, HEIGHT - 80, WIDTH, HEIGHT], fill=(13, 19, 36))
    draw.text((60, HEIGHT - 52), "Techstarz101.com · Formbricks · Cal.com · BookStack · DocuSeal · Grist · Kimai", fill="#64748b", font=get_font(17))
    draw.text((WIDTH - 240, HEIGHT - 52), "100% OPEN SOURCE", fill="#10b981", font=get_font(18, True))
    img.save(FRAMES_DIR / f"frame_{idx:04d}.png")


def main():
    for i in range(TOTAL_FRAMES):
        render_frame(i)
    mp4 = OUT_DIR / "ai_opportunity_audit_feature.mp4"
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
