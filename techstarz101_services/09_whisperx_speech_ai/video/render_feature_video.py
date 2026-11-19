#!/usr/bin/env python3
"""
Feature Video Renderer for Techstarz101 Service #09: WhisperX Speech AI.
Uses persistent character reference: character_02_podcast_studio_mic.jpg
Output: whisperx_speech_ai_feature.mp4 (1080x1080, 30fps, 12s)
"""

import os
import shutil
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

CHAR_PATH = r"C:\Users\tee\.gemini\config\assets\characters\character_02_podcast_studio_mic.jpg"
OUT_DIR = Path("techstarz101_services/09_whisperx_speech_ai/video")
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
    draw.text((86, 44), "TECHSTARZ101 · SERVICE #09", fill=(148, 163, 184), font=get_font(20, True))
    draw.rounded_rectangle([WIDTH - 340, 32, WIDTH - 40, 78], radius=23, fill=(16, 185, 129))
    draw.text((WIDTH - 318, 44), "70X REAL-TIME SPEECH AI", fill=(255, 255, 255), font=get_font(19, True))

    if os.path.exists(CHAR_PATH):
        c = Image.open(CHAR_PATH).convert("RGBA")
        c.thumbnail((250, 250))
        mask = Image.new("L", c.size, 0)
        ImageDraw.Draw(mask).ellipse((0, 0, c.size[0], c.size[1]), fill=255)
        img.paste(c, (WIDTH - 290, 140), mask)
        draw.ellipse([WIDTH - 294, 136, WIDTH - 290 + c.size[0] + 4, 140 + c.size[1] + 4], outline=(56, 189, 248), width=3)

    if t < 3.0:
        draw.text((60, 200), "Transcribe 1 Hour of Audio", fill="#ffffff", font=get_font(50, True))
        draw.text((60, 268), "In Under 50 Seconds.", fill="#38bdf8", font=get_font(52, True))
        draw.rounded_rectangle([60, 385, 750, 565], radius=16, fill=(19, 29, 51), outline=(51, 65, 85), width=2)
        draw.text((90, 415), "✓  70x Real-Time CTranslate2 + WhisperX", fill="#10b981", font=get_font(24, True))
        draw.text((90, 465), "✓  Speaker Diarization & Word Timestamps", fill="#38bdf8", font=get_font(24, True))
        draw.text((90, 515), "✓  $0/minute Private Self-Hosted Audio Vault", fill="#c084fc", font=get_font(24, True))
        draw.text((60, 635), "Replace Gong, Otter & Rev with sovereign AI.", fill="#ffffff", font=get_font(31, True))
    elif t < 6.5:
        draw.text((60, 185), "2 Open-Source Speech Stacks", fill="#ffffff", font=get_font(46, True))
        draw.text((60, 248), "8 Click-to-Launch Standalone Apps", fill="#38bdf8", font=get_font(40, True))
        draw.rounded_rectangle([60, 350, 515, 620], radius=16, fill=(19, 29, 51), outline=(56, 189, 248), width=2)
        draw.text((85, 375), "STACK A · 70X ASR & SEARCH", fill="#38bdf8", font=get_font(22, True))
        draw.text((85, 420), "• Speaches (OpenAI Whisper)", fill="#e2e8f0", font=get_font(22))
        draw.text((85, 458), "• WhisperX ASR (REST API)", fill="#e2e8f0", font=get_font(22))
        draw.text((85, 496), "• MinIO (S3 Audio Vault)", fill="#e2e8f0", font=get_font(22))
        draw.text((85, 534), "• Meilisearch (<50ms Search)", fill="#e2e8f0", font=get_font(22))
        draw.text((85, 578), "Zero Per-Minute API Tax", fill="#10b981", font=get_font(20, True))

        draw.rounded_rectangle([545, 350, 1020, 620], radius=16, fill=(19, 29, 51), outline=(168, 85, 247), width=2)
        draw.text((570, 375), "STACK B · MEETING STUDIO", fill="#c084fc", font=get_font(22, True))
        draw.text((570, 420), "• Scriberr (AI Summaries)", fill="#e2e8f0", font=get_font(22))
        draw.text((570, 458), "• Whisper-WebUI (SRT/VTT)", fill="#e2e8f0", font=get_font(22))
        draw.text((570, 496), "• Label Studio (Audio QA)", fill="#e2e8f0", font=get_font(22))
        draw.text((570, 534), "• n8n Speech (CRM Sync)", fill="#e2e8f0", font=get_font(22))
        draw.text((570, 578), "100% Private On-Prem", fill="#10b981", font=get_font(20, True))
    elif t < 9.5:
        draw.text((60, 190), "Word-Aligned Diarization", fill="#ffffff", font=get_font(48, True))
        draw.text((60, 252), "+ Instant SRT / VTT Export", fill="#c084fc", font=get_font(40, True))
        draw.rounded_rectangle([60, 345, 980, 610], radius=16, fill=(15, 23, 42), outline=(99, 102, 241), width=2)
        draw.text((90, 375), "LIVE DIARIZED TRANSCRIPT (71.4x Real-Time):", fill="#94a3b8", font=get_font(20, True))
        draw.text((90, 420), "[00:00.20 -> 00:04.85] SPEAKER_00: Spending $3,200/mo on Gong...", fill="#38bdf8", font=get_font(20, True))
        draw.text((90, 465), "[00:05.12 -> 00:10.40] SPEAKER_01: Deploy WhisperX at 70x speed.", fill="#10b981", font=get_font(20, True))
        draw.text((90, 515), "✓ Auto-extracted CRM action items + downloadable .SRT / .VTT", fill="#e2e8f0", font=get_font(21))
    else:
        draw.text((60, 195), "Click Any Tool Repo Icon.", fill="#ffffff", font=get_font(50, True))
        draw.text((60, 265), "Own Your Speech AI Stack.", fill="#10b981", font=get_font(46, True))
        draw.rounded_rectangle([60, 360, 1020, 515], radius=16, fill=(19, 29, 51), outline=(16, 185, 129), width=2)
        draw.text((90, 392), "Dedicated App Links:  localhost:7872/t/<tool>", fill="#38bdf8", font=get_font(26, True))
        draw.text((90, 438), "Speaches · WhisperX · MinIO · Meilisearch · Scriberr", fill="#e2e8f0", font=get_font(22))
        draw.text((90, 474), "70x Real-Time · 100% Open Source", fill="#10b981", font=get_font(20, True))
        draw.rounded_rectangle([60, 555, 1020, 680], radius=16, fill=(56, 189, 248))
        draw.text((WIDTH // 2, 598), "FLAT $390 48-HOUR STARTER SPRINT", fill="#070a13", font=get_font(34, True), anchor="mm")
        draw.text((WIDTH // 2, 645), "https://techstarz101.com/agents/whisperx-transcription", fill="#0f172a", font=get_font(20, True), anchor="mm")

    draw.rectangle([0, HEIGHT - 80, WIDTH, HEIGHT], fill=(13, 19, 36))
    draw.text((60, HEIGHT - 52), "Techstarz101.com · Speaches · WhisperX · MinIO · Meilisearch · Scriberr", fill="#64748b", font=get_font(17))
    draw.text((WIDTH - 240, HEIGHT - 52), "100% OPEN SOURCE", fill="#10b981", font=get_font(18, True))
    img.save(FRAMES_DIR / f"frame_{idx:04d}.png")


def main():
    for i in range(TOTAL_FRAMES):
        render_frame(i)
    mp4 = OUT_DIR / "whisperx_speech_ai_feature.mp4"
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
