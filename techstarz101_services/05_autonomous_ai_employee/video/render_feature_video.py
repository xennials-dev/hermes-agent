#!/usr/bin/env python3
"""
Feature Video Renderer for Techstarz101 Service #05: Autonomous AI Employee.
Uses persistent character reference: character_03_executive_suite_suit.jpg
Output: autonomous_ai_employee_feature.mp4 (1080x1080, 30fps, 12s)
"""

import os
import shutil
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

CHAR_PATH = r"C:\Users\tee\.gemini\config\assets\characters\character_03_executive_suite_suit.jpg"
OUT_DIR = Path("techstarz101_services/05_autonomous_ai_employee/video")
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
    draw.text((86, 44), "TECHSTARZ101 · SERVICE #05", fill=(148, 163, 184), font=get_font(20, True))
    draw.rounded_rectangle([WIDTH - 355, 32, WIDTH - 40, 78], radius=23, fill=(16, 185, 129))
    draw.text((WIDTH - 335, 44), "AUTONOMOUS AI EMPLOYEE", fill=(255, 255, 255), font=get_font(19, True))

    if os.path.exists(CHAR_PATH):
        c = Image.open(CHAR_PATH).convert("RGBA")
        c.thumbnail((250, 250))
        mask = Image.new("L", c.size, 0)
        ImageDraw.Draw(mask).ellipse((0, 0, c.size[0], c.size[1]), fill=255)
        img.paste(c, (WIDTH - 290, 140), mask)
        draw.ellipse([WIDTH - 294, 136, WIDTH - 290 + c.size[0] + 4, 140 + c.size[1] + 4], outline=(56, 189, 248), width=3)

    if t < 3.0:
        draw.text((60, 200), "Hire a 24/7 Full-Stack", fill="#ffffff", font=get_font(52, True))
        draw.text((60, 268), "Autonomous AI Teammate.", fill="#38bdf8", font=get_font(48, True))
        draw.rounded_rectangle([60, 385, 750, 565], radius=16, fill=(19, 29, 51), outline=(51, 65, 85), width=2)
        draw.text((90, 415), "✓  Remembers every SOP & meeting in Qdrant", fill="#10b981", font=get_font(24, True))
        draw.text((90, 465), "✓  Runs durable multi-day tasks on Temporal", fill="#38bdf8", font=get_font(24, True))
        draw.text((90, 515), "✓  Full audit logs & human approval gates", fill="#c084fc", font=get_font(24, True))
        draw.text((60, 635), "Zero payroll overhead. 100% sovereign data.", fill="#ffffff", font=get_font(31, True))
    elif t < 6.5:
        draw.text((60, 185), "2 Executive AI Stacks", fill="#ffffff", font=get_font(48, True))
        draw.text((60, 248), "8 Click-to-Launch Standalone Apps", fill="#38bdf8", font=get_font(40, True))
        draw.rounded_rectangle([60, 350, 515, 620], radius=16, fill=(19, 29, 51), outline=(56, 189, 248), width=2)
        draw.text((85, 375), "STACK A · ORCHESTRATOR", fill="#38bdf8", font=get_font(23, True))
        draw.text((85, 420), "• Open WebUI (Command UI)", fill="#e2e8f0", font=get_font(22))
        draw.text((85, 458), "• Qdrant (Vector Memory)", fill="#e2e8f0", font=get_font(22))
        draw.text((85, 496), "• Temporal (Durable Tasks)", fill="#e2e8f0", font=get_font(22))
        draw.text((85, 534), "• Langfuse (Audit Traces)", fill="#e2e8f0", font=get_font(22))
        draw.text((85, 578), "Enterprise Governance", fill="#10b981", font=get_font(20, True))

        draw.rounded_rectangle([545, 350, 1020, 620], radius=16, fill=(19, 29, 51), outline=(168, 85, 247), width=2)
        draw.text((570, 375), "STACK B · VISUAL TEAMMATE", fill="#c084fc", font=get_font(23, True))
        draw.text((570, 420), "• Dify (Agent Workflows)", fill="#e2e8f0", font=get_font(22))
        draw.text((570, 458), "• AnythingLLM (RAG + MCP)", fill="#e2e8f0", font=get_font(22))
        draw.text((570, 496), "• LiteLLM (Model Router)", fill="#e2e8f0", font=get_font(22))
        draw.text((570, 534), "• NocoDB (Approval Board)", fill="#e2e8f0", font=get_font(22))
        draw.text((570, 578), "Zero Vendor Lock-In", fill="#10b981", font=get_font(20, True))
    elif t < 9.5:
        draw.text((60, 190), "Delegate One Directive.", fill="#ffffff", font=get_font(48, True))
        draw.text((60, 252), "Executes Across Your Stack.", fill="#c084fc", font=get_font(42, True))
        draw.rounded_rectangle([60, 345, 980, 610], radius=16, fill=(15, 23, 42), outline=(99, 102, 241), width=2)
        draw.text((90, 375), "EXECUTIVE ORCHESTRATION DAG:", fill="#94a3b8", font=get_font(20, True))
        draw.text((90, 420), "1. Recall SOPs & prior deals (Qdrant / AnythingLLM)", fill="#38bdf8", font=get_font(22, True))
        draw.text((90, 465), "2. Synthesize weekly brief & client follow-ups", fill="#e2e8f0", font=get_font(22))
        draw.text((90, 510), "3. Stage external sends for 1-click Approval Gate", fill="#10b981", font=get_font(22, True))
        draw.text((90, 555), "4. Log full trace & $0.00 local cost in Langfuse", fill="#cbd5e1", font=get_font(22))
    else:
        draw.text((60, 195), "Click Any Tool Repo Icon.", fill="#ffffff", font=get_font(50, True))
        draw.text((60, 265), "Deploy Your AI Employee.", fill="#10b981", font=get_font(46, True))
        draw.rounded_rectangle([60, 360, 1020, 515], radius=16, fill=(19, 29, 51), outline=(16, 185, 129), width=2)
        draw.text((90, 392), "Dedicated App Links:  localhost:7869/t/<tool>", fill="#38bdf8", font=get_font(26, True))
        draw.text((90, 438), "Open WebUI · Qdrant · Temporal · Langfuse · Dify · NocoDB", fill="#e2e8f0", font=get_font(21))
        draw.text((90, 474), "100% Open Source · Sovereign Executive AI", fill="#10b981", font=get_font(20, True))
        draw.rounded_rectangle([60, 555, 1020, 680], radius=16, fill=(56, 189, 248))
        draw.text((WIDTH // 2, 598), "FLAT $390 48-HOUR STARTER SPRINT", fill="#070a13", font=get_font(34, True), anchor="mm")
        draw.text((WIDTH // 2, 645), "https://techstarz101.com/agents/autonomous-ai-employee", fill="#0f172a", font=get_font(20, True), anchor="mm")

    draw.rectangle([0, HEIGHT - 80, WIDTH, HEIGHT], fill=(13, 19, 36))
    draw.text((60, HEIGHT - 52), "Techstarz101.com · Open WebUI · Qdrant · Temporal · Langfuse · Dify · LiteLLM", fill="#64748b", font=get_font(17))
    draw.text((WIDTH - 240, HEIGHT - 52), "100% OPEN SOURCE", fill="#10b981", font=get_font(18, True))
    img.save(FRAMES_DIR / f"frame_{idx:04d}.png")


def main():
    for i in range(TOTAL_FRAMES):
        render_frame(i)
    mp4 = OUT_DIR / "autonomous_ai_employee_feature.mp4"
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
