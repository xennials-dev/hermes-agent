#!/usr/bin/env python3
"""
Feature Video Renderer for Techstarz101 Service #04: Brand & Web Launch.
Uses persistent character reference: character_01_street_cap_smile.jpg
Output: brand_web_launch_feature.mp4 (1080x1080, 30fps, 12s)
"""

import os
import shutil
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

CHAR_PATH = r"C:\Users\tee\.gemini\config\assets\characters\character_01_street_cap_smile.jpg"
OUT_DIR = Path("techstarz101_services/04_brand_web_launch/video")
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
    draw.text((86, 44), "TECHSTARZ101 · SERVICE #04", fill=(148, 163, 184), font=get_font(20, True))
    draw.rounded_rectangle([WIDTH - 330, 32, WIDTH - 40, 78], radius=23, fill=(16, 185, 129))
    draw.text((WIDTH - 308, 44), "BRAND & WEB LAUNCH", fill=(255, 255, 255), font=get_font(20, True))

    if os.path.exists(CHAR_PATH):
        c = Image.open(CHAR_PATH).convert("RGBA")
        c.thumbnail((250, 250))
        mask = Image.new("L", c.size, 0)
        ImageDraw.Draw(mask).ellipse((0, 0, c.size[0], c.size[1]), fill=255)
        img.paste(c, (WIDTH - 290, 140), mask)
        draw.ellipse([WIDTH - 294, 136, WIDTH - 290 + c.size[0] + 4, 140 + c.size[1] + 4], outline=(16, 185, 129), width=3)

    if t < 3.0:
        draw.text((60, 200), "From Initial Idea to", fill="#ffffff", font=get_font(52, True))
        draw.text((60, 268), "Live Deployed Web.", fill="#38bdf8", font=get_font(52, True))
        draw.rounded_rectangle([60, 385, 750, 565], radius=16, fill=(19, 29, 51), outline=(51, 65, 85), width=2)
        draw.text((90, 415), "X  Skip $8,000 agency branding timelines", fill="#fca5a5", font=get_font(25, True))
        draw.text((90, 465), "X  Zero Webflow / Figma / Squarespace rent", fill="#fca5a5", font=get_font(25, True))
        draw.text((90, 515), "X  Own your code, CMS, domains & SSL 100%", fill="#10b981", font=get_font(25, True))
        draw.text((60, 635), "Deploy your sovereign brand & site in 48 hours.", fill="#38bdf8", font=get_font(31, True))
    elif t < 6.5:
        draw.text((60, 185), "2 Open-Source Launch Stacks", fill="#ffffff", font=get_font(46, True))
        draw.text((60, 246), "8 Click-to-Launch Standalone Apps", fill="#38bdf8", font=get_font(40, True))
        draw.rounded_rectangle([60, 350, 515, 620], radius=16, fill=(19, 29, 51), outline=(56, 189, 248), width=2)
        draw.text((85, 375), "STACK A · DESIGN-TO-DEPLOY", fill="#38bdf8", font=get_font(23, True))
        draw.text((85, 420), "• Penpot (Figma Alternative)", fill="#e2e8f0", font=get_font(22))
        draw.text((85, 458), "• Directus (Headless CMS)", fill="#e2e8f0", font=get_font(22))
        draw.text((85, 496), "• Gitea (Self-Hosted Git/CI)", fill="#e2e8f0", font=get_font(22))
        draw.text((85, 534), "• Nginx Proxy Mgr (Auto SSL)", fill="#e2e8f0", font=get_font(22))
        draw.text((85, 578), "Full Code Ownership", fill="#10b981", font=get_font(20, True))

        draw.rounded_rectangle([545, 350, 1020, 620], radius=16, fill=(19, 29, 51), outline=(168, 85, 247), width=2)
        draw.text((570, 375), "STACK B · RAPID WEB & CMS", fill="#c084fc", font=get_font(23, True))
        draw.text((570, 420), "• WordPress (Visual Sites)", fill="#e2e8f0", font=get_font(22))
        draw.text((570, 458), "• Ghost (SEO Brand Blog)", fill="#e2e8f0", font=get_font(22))
        draw.text((570, 496), "• Strapi (Custom API CMS)", fill="#e2e8f0", font=get_font(22))
        draw.text((570, 534), "• Uptime Kuma (SSL Guard)", fill="#e2e8f0", font=get_font(22))
        draw.text((570, 578), "Zero Monthly SaaS Fees", fill="#10b981", font=get_font(20, True))
    elif t < 9.5:
        draw.text((60, 190), "Instant Brand Kit + HTML", fill="#ffffff", font=get_font(48, True))
        draw.text((60, 252), "Live Preview & One-Click Export", fill="#10b981", font=get_font(40, True))
        draw.rounded_rectangle([60, 345, 980, 610], radius=16, fill=(15, 23, 42), outline=(99, 102, 241), width=2)
        draw.text((90, 375), "BUILT-IN BRAND & SITE COMPILER (localhost:7868):", fill="#94a3b8", font=get_font(20, True))
        draw.text((90, 420), "✓ Vector SVG Logo + Responsive Design Tokens", fill="#38bdf8", font=get_font(23, True))
        draw.text((90, 465), "✓ Production Tailwind Landing Page (/preview/site)", fill="#e2e8f0", font=get_font(23))
        draw.text((90, 510), "✓ Automated SSL & Uptime Kuma Health Monitoring", fill="#10b981", font=get_font(23, True))
        draw.text((90, 555), "✓ Download index.html or Push Directly to Gitea", fill="#cbd5e1", font=get_font(22))
    else:
        draw.text((60, 195), "Click Any Tool Repo Icon.", fill="#ffffff", font=get_font(50, True))
        draw.text((60, 265), "Launch Your Brand Today.", fill="#10b981", font=get_font(46, True))
        draw.rounded_rectangle([60, 360, 1020, 515], radius=16, fill=(19, 29, 51), outline=(16, 185, 129), width=2)
        draw.text((90, 392), "Dedicated App Links:  localhost:7868/t/<tool>", fill="#38bdf8", font=get_font(26, True))
        draw.text((90, 438), "Penpot · Directus · Gitea · WordPress · Ghost · Strapi", fill="#e2e8f0", font=get_font(22))
        draw.text((90, 474), "100% Open Source · Self-Hosted Sovereignty", fill="#10b981", font=get_font(20, True))
        draw.rounded_rectangle([60, 555, 1020, 680], radius=16, fill=(56, 189, 248))
        draw.text((WIDTH // 2, 598), "FLAT $390 48-HOUR STARTER SPRINT", fill="#070a13", font=get_font(34, True), anchor="mm")
        draw.text((WIDTH // 2, 645), "https://techstarz101.com/agents/branding-agent", fill="#0f172a", font=get_font(21, True), anchor="mm")

    draw.rectangle([0, HEIGHT - 80, WIDTH, HEIGHT], fill=(13, 19, 36))
    draw.text((60, HEIGHT - 52), "Techstarz101.com · Penpot · Directus · Gitea · Nginx · WordPress · Ghost · Strapi", fill="#64748b", font=get_font(17))
    draw.text((WIDTH - 240, HEIGHT - 52), "100% OPEN SOURCE", fill="#10b981", font=get_font(18, True))
    img.save(FRAMES_DIR / f"frame_{idx:04d}.png")


def main():
    for i in range(TOTAL_FRAMES):
        render_frame(i)
    mp4 = OUT_DIR / "brand_web_launch_feature.mp4"
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
