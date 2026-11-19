#!/usr/bin/env python3
"""
High-Fidelity Feature Video Renderer for Techstarz101 Service #02: Social Media Closer.
Adheres strictly to the Global Video Character Reference Doctrine using:
character_02_podcast_studio_mic.jpg
Output: social_closer_feature.mp4 (1080x1080 universal social format, 30fps, 12s)
"""

import os
import shutil
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

CHAR_PATH = r"C:\Users\tee\.gemini\config\assets\characters\character_02_podcast_studio_mic.jpg"
OUT_DIR = Path("techstarz101_services/02_social_media_closer/video")
OUT_DIR.mkdir(parents=True, exist_ok=True)
FRAMES_DIR = OUT_DIR / "frames"
FRAMES_DIR.mkdir(parents=True, exist_ok=True)

WIDTH, HEIGHT = 1080, 1080
FPS = 30
DURATION_SEC = 12
TOTAL_FRAMES = FPS * DURATION_SEC


def get_font(size: int, bold: bool = False):
    font_names = ["Arial.ttf", "segoeui.ttf", "Calibri.ttf", "tahoma.ttf"]
    if bold:
        font_names = ["Arialbd.ttf", "segoeuib.ttf", "Calibrib.ttf", "tahomabd.ttf"] + font_names
    for name in font_names:
        try:
            return ImageFont.truetype(f"C:/Windows/Fonts/{name}", size)
        except Exception:
            pass
    return ImageFont.load_default()


def render_frame(frame_idx: int):
    t = frame_idx / FPS
    img = Image.new("RGB", (WIDTH, HEIGHT), "#070a13")
    draw = ImageDraw.Draw(img)

    # Header bar
    draw.rectangle([0, 0, WIDTH, 110], fill=(13, 19, 36))
    draw.line([0, 110, WIDTH, 110], fill=(30, 41, 59), width=2)

    draw.rounded_rectangle([40, 32, 340, 78], radius=23, fill=(30, 41, 59))
    draw.ellipse([58, 48, 72, 62], fill=(56, 189, 248))
    draw.text((86, 44), "TECHSTARZ101 · SERVICE #02", fill=(148, 163, 184), font=get_font(20, bold=True))

    draw.rounded_rectangle([WIDTH - 310, 32, WIDTH - 40, 78], radius=23, fill=(16, 185, 129))
    draw.text((WIDTH - 290, 44), "24/7 DM SALES CLOSER", fill=(255, 255, 255), font=get_font(20, bold=True))

    # Character reference circular avatar
    if os.path.exists(CHAR_PATH):
        char_img = Image.open(CHAR_PATH).convert("RGBA")
        char_img.thumbnail((250, 250))
        mask = Image.new("L", char_img.size, 0)
        ImageDraw.Draw(mask).ellipse((0, 0, char_img.size[0], char_img.size[1]), fill=255)
        img.paste(char_img, (WIDTH - 290, 140), mask)
        draw.ellipse([WIDTH - 294, 136, WIDTH - 290 + char_img.size[0] + 4, 140 + char_img.size[1] + 4],
                     outline=(168, 85, 247), width=3)

    if t < 3.0:
        draw.text((60, 200), "Stop Losing Social Leads", fill="#ffffff", font=get_font(52, bold=True))
        draw.text((60, 268), "While You Sleep.", fill="#f43f5e", font=get_font(52, bold=True))
        draw.rounded_rectangle([60, 385, 750, 565], radius=16, fill=(19, 29, 51), outline=(51, 65, 85), width=2)
        draw.text((90, 415), "X  $600+/mo for Buffer + ManyChat + Zapier", fill="#fca5a5", font=get_font(25, bold=True))
        draw.text((90, 465), "X  68% of DMs arrive after business hours", fill="#fca5a5", font=get_font(25, bold=True))
        draw.text((90, 515), "X  Prospects go cold in under 15 minutes", fill="#fca5a5", font=get_font(25, bold=True))
        draw.text((60, 635), "Deploy your own 24/7 Social Media Closer.", fill="#38bdf8", font=get_font(32, bold=True))

    elif t < 6.5:
        draw.text((60, 185), "2 Open-Source Tool Stacks", fill="#ffffff", font=get_font(48, bold=True))
        draw.text((60, 248), "9 Standalone Click-to-Launch Apps", fill="#38bdf8", font=get_font(42, bold=True))

        draw.rounded_rectangle([60, 350, 515, 620], radius=16, fill=(19, 29, 51), outline=(56, 189, 248), width=2)
        draw.text((85, 375), "STACK A · OMNICHANNEL", fill="#38bdf8", font=get_font(24, bold=True))
        draw.text((85, 420), "• Postiz (30+ Networks)", fill="#e2e8f0", font=get_font(22))
        draw.text((85, 458), "• Chatwoot (24/7 DM Inbox)", fill="#e2e8f0", font=get_font(22))
        draw.text((85, 496), "• n8n (Workflow Glue)", fill="#e2e8f0", font=get_font(22))
        draw.text((85, 534), "• Ollama LLM + Twenty CRM", fill="#e2e8f0", font=get_font(22))
        draw.text((85, 578), "Zero Per-Seat Licensing", fill="#10b981", font=get_font(20, bold=True))

        draw.rounded_rectangle([545, 350, 1020, 620], radius=16, fill=(19, 29, 51), outline=(168, 85, 247), width=2)
        draw.text((570, 375), "STACK B · AGENTIC LOW-CODE", fill="#c084fc", font=get_font(24, bold=True))
        draw.text((570, 420), "• Mixpost (Buffer Alternative)", fill="#e2e8f0", font=get_font(22))
        draw.text((570, 458), "• Flowise (Visual AI Agent)", fill="#e2e8f0", font=get_font(22))
        draw.text((570, 496), "• Activepieces (No-Code Glue)", fill="#e2e8f0", font=get_font(22))
        draw.text((570, 534), "• EspoCRM (Fast Deal Pipeline)", fill="#e2e8f0", font=get_font(22))
        draw.text((570, 578), "Mix, Match & Automate Freely", fill="#10b981", font=get_font(20, bold=True))

    elif t < 9.5:
        draw.text((60, 190), "Instant 24/7 DM Closing", fill="#ffffff", font=get_font(48, bold=True))
        draw.text((60, 252), "Qualifies Intent & Logs CRM Deals", fill="#c084fc", font=get_font(40, bold=True))

        draw.rounded_rectangle([60, 345, 980, 610], radius=16, fill=(15, 23, 42), outline=(99, 102, 241), width=2)
        draw.text((90, 372), "INBOUND DM (Instagram / Facebook / X):", fill="#94a3b8", font=get_font(20, bold=True))
        draw.text((90, 405), '"How much to automate our posts & DM replies?"', fill="#ffffff", font=get_font(24, bold=True))
        draw.line([90, 450, 950, 450], fill=(51, 65, 85), width=1)
        draw.text((90, 470), "AI CLOSER REPLY (<5s · Intent: PRICING):", fill="#10b981", font=get_font(20, bold=True))
        draw.text((90, 505), '"Flat $390 48-hour sprint, 100% refundable."', fill="#38bdf8", font=get_font(24, bold=True))
        draw.text((90, 548), "✓ Deal logged to Twenty CRM / EspoCRM automatically", fill="#cbd5e1", font=get_font(21))

    else:
        draw.text((60, 195), "Click Any Repo Icon.", fill="#ffffff", font=get_font(52, bold=True))
        draw.text((60, 265), "Run Individually or Stacked.", fill="#10b981", font=get_font(46, bold=True))

        draw.rounded_rectangle([60, 360, 1020, 515], radius=16, fill=(19, 29, 51), outline=(16, 185, 129), width=2)
        draw.text((90, 392), "Dedicated App Links:  localhost:7866/t/<tool>", fill="#38bdf8", font=get_font(26, bold=True))
        draw.text((90, 438), "Auto-boots Docker Compose · Zero Manual Wiring", fill="#e2e8f0", font=get_font(22))
        draw.text((90, 474), "100% Open Source · Self-Hosted Sovereignty", fill="#10b981", font=get_font(20, bold=True))

        draw.rounded_rectangle([60, 555, 1020, 680], radius=16, fill=(56, 189, 248))
        draw.text((WIDTH // 2, 598), "FLAT $390 48-HOUR STARTER SPRINT", fill="#070a13", font=get_font(34, bold=True), anchor="mm")
        draw.text((WIDTH // 2, 645), "https://techstarz101.com/agents/social-media-manager", fill="#0f172a", font=get_font(21, bold=True), anchor="mm")

    # Footer
    draw.rectangle([0, HEIGHT - 80, WIDTH, HEIGHT], fill=(13, 19, 36))
    draw.text((60, HEIGHT - 52), "Techstarz101.com · Postiz · Chatwoot · n8n · Ollama · Flowise · Twenty", fill="#64748b", font=get_font(18))
    draw.text((WIDTH - 240, HEIGHT - 52), "100% OPEN SOURCE", fill="#10b981", font=get_font(18, bold=True))

    img.save(FRAMES_DIR / f"frame_{frame_idx:04d}.png")


def main():
    print(f"Rendering {TOTAL_FRAMES} frames for Social Media Closer feature video...")
    for i in range(TOTAL_FRAMES):
        render_frame(i)
    mp4_out = OUT_DIR / "social_closer_feature.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-framerate", str(FPS),
        "-i", str(FRAMES_DIR / "frame_%04d.png"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "fast",
        str(mp4_out)
    ], check=True)
    shutil.rmtree(FRAMES_DIR)
    print(f"DONE: {mp4_out} ({os.path.getsize(mp4_out) / 1024 / 1024:.2f} MB)")


if __name__ == "__main__":
    main()
