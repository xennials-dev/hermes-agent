#!/usr/bin/env python3
"""
Feature Video Renderer for Techstarz101 Service #07: Listmonk Email Marketing.
Uses persistent character reference: character_04_penthouse_lounge_tracksuit.jpg
Output: listmonk_email_feature.mp4 (1080x1080, 30fps, 12s)
"""

import os
import shutil
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

CHAR_PATH = r"C:\Users\tee\.gemini\config\assets\characters\character_04_penthouse_lounge_tracksuit.jpg"
OUT_DIR = Path("techstarz101_services/07_listmonk_email/video")
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
    draw.text((86, 44), "TECHSTARZ101 · SERVICE #07", fill=(148, 163, 184), font=get_font(20, True))
    draw.rounded_rectangle([WIDTH - 340, 32, WIDTH - 40, 78], radius=23, fill=(16, 185, 129))
    draw.text((WIDTH - 318, 44), "ZERO CONTACT TAX EMAIL", fill=(255, 255, 255), font=get_font(19, True))

    if os.path.exists(CHAR_PATH):
        c = Image.open(CHAR_PATH).convert("RGBA")
        c.thumbnail((250, 250))
        mask = Image.new("L", c.size, 0)
        ImageDraw.Draw(mask).ellipse((0, 0, c.size[0], c.size[1]), fill=255)
        img.paste(c, (WIDTH - 290, 140), mask)
        draw.ellipse([WIDTH - 294, 136, WIDTH - 290 + c.size[0] + 4, 140 + c.size[1] + 4], outline=(56, 189, 248), width=3)

    if t < 3.0:
        draw.text((60, 200), "Stop Paying Mailchimp", fill="#ffffff", font=get_font(52, True))
        draw.text((60, 268), "$950/mo For Your Own List.", fill="#f43f5e", font=get_font(48, True))
        draw.rounded_rectangle([60, 385, 750, 565], radius=16, fill=(19, 29, 51), outline=(51, 65, 85), width=2)
        draw.text((90, 415), "X  50,000 contacts = $725–$950/mo on Klaviyo", fill="#fca5a5", font=get_font(24, True))
        draw.text((90, 465), "✓  Self-Hosted Listmonk = $0 contact tax", fill="#10b981", font=get_font(24, True))
        draw.text((90, 515), "✓  Stalwart DKIM/DMARC + Reacher hygiene", fill="#38bdf8", font=get_font(24, True))
        draw.text((60, 635), "Save $10,000+/year owning your email stack.", fill="#ffffff", font=get_font(31, True))
    elif t < 6.5:
        draw.text((60, 185), "2 Open-Source Email Stacks", fill="#ffffff", font=get_font(46, True))
        draw.text((60, 248), "8 Click-to-Launch Standalone Apps", fill="#38bdf8", font=get_font(40, True))
        draw.rounded_rectangle([60, 350, 515, 620], radius=16, fill=(19, 29, 51), outline=(56, 189, 248), width=2)
        draw.text((85, 375), "STACK A · BROADCAST ENGINE", fill="#38bdf8", font=get_font(22, True))
        draw.text((85, 420), "• Listmonk (Millions/hr)", fill="#e2e8f0", font=get_font(22))
        draw.text((85, 458), "• Stalwart (Rust SMTP/DKIM)", fill="#e2e8f0", font=get_font(22))
        draw.text((85, 496), "• Mailpit (HTML QA Sandbox)", fill="#e2e8f0", font=get_font(22))
        draw.text((85, 534), "• Reacher (Bounce Scrubber)", fill="#e2e8f0", font=get_font(22))
        draw.text((85, 578), "99%+ Inbox Deliverability", fill="#10b981", font=get_font(20, True))

        draw.rounded_rectangle([545, 350, 1020, 620], radius=16, fill=(19, 29, 51), outline=(168, 85, 247), width=2)
        draw.text((570, 375), "STACK B · VISUAL LIFECYCLE", fill="#c084fc", font=get_font(22, True))
        draw.text((570, 420), "• Keila (Visual Editor)", fill="#e2e8f0", font=get_font(22))
        draw.text((570, 458), "• Roundcube (Reply Inbox)", fill="#e2e8f0", font=get_font(22))
        draw.text((570, 496), "• n8n (Behavioral Drips)", fill="#e2e8f0", font=get_font(22))
        draw.text((570, 534), "• Adminer (SQL Segments)", fill="#e2e8f0", font=get_font(22))
        draw.text((570, 578), "100% Open Source", fill="#10b981", font=get_font(20, True))
    elif t < 9.5:
        draw.text((60, 190), "Built-In SPF/DKIM/DMARC", fill="#ffffff", font=get_font(48, True))
        draw.text((60, 252), "& Zero-Tax Savings Modeler", fill="#10b981", font=get_font(40, True))
        draw.rounded_rectangle([60, 345, 980, 610], radius=16, fill=(15, 23, 42), outline=(99, 102, 241), width=2)
        draw.text((90, 375), "50,000 SUBSCRIBERS · 200,000 EMAILS / MONTH:", fill="#94a3b8", font=get_font(20, True))
        draw.text((90, 420), "• Klaviyo Monthly Cost:         $950 / mo", fill="#fca5a5", font=get_font(23, True))
        draw.text((90, 465), "• Sovereign Listmonk + SMTP:    $20 / mo", fill="#10b981", font=get_font(23, True))
        draw.text((90, 510), "• Annualized Cash Saved:        $11,160 / yr", fill="#38bdf8", font=get_font(24, True))
        draw.text((90, 555), "✓ Auto-generated SPF, DKIM & DMARC records ready", fill="#cbd5e1", font=get_font(22))
    else:
        draw.text((60, 195), "Click Any Tool Repo Icon.", fill="#ffffff", font=get_font(50, True))
        draw.text((60, 265), "Own Your Email Engine.", fill="#10b981", font=get_font(46, True))
        draw.rounded_rectangle([60, 360, 1020, 515], radius=16, fill=(19, 29, 51), outline=(16, 185, 129), width=2)
        draw.text((90, 392), "Dedicated App Links:  localhost:7871/t/<tool>", fill="#38bdf8", font=get_font(26, True))
        draw.text((90, 438), "Listmonk · Stalwart · Mailpit · Reacher · Keila · Roundcube", fill="#e2e8f0", font=get_font(21))
        draw.text((90, 474), "Zero Contact Tax · 100% Open Source", fill="#10b981", font=get_font(20, True))
        draw.rounded_rectangle([60, 555, 1020, 680], radius=16, fill=(56, 189, 248))
        draw.text((WIDTH // 2, 598), "FLAT $390 48-HOUR STARTER SPRINT", fill="#070a13", font=get_font(34, True), anchor="mm")
        draw.text((WIDTH // 2, 645), "https://techstarz101.com/agents/listmonk-email", fill="#0f172a", font=get_font(21, True), anchor="mm")

    draw.rectangle([0, HEIGHT - 80, WIDTH, HEIGHT], fill=(13, 19, 36))
    draw.text((60, HEIGHT - 52), "Techstarz101.com · Listmonk · Stalwart · Mailpit · Reacher · Keila · n8n", fill="#64748b", font=get_font(17))
    draw.text((WIDTH - 240, HEIGHT - 52), "100% OPEN SOURCE", fill="#10b981", font=get_font(18, True))
    img.save(FRAMES_DIR / f"frame_{idx:04d}.png")


def main():
    for i in range(TOTAL_FRAMES):
        render_frame(i)
    mp4 = OUT_DIR / "listmonk_email_feature.mp4"
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
