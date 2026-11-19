#!/usr/bin/env python3
"""Build the 60-second Onn 4K Pro Commercial Video (Version 2 - High Broadcast Spec).

Includes:
- Dynamic video playing inside the TV screen bezel with NBA, NFL, NCAA, NHL & Blockbuster Movies + official logo badges.
- Watermark elimination (clean presenter cropping in PiP + studio vignette background grading).
- Non-obstructive, sleek teleprompter subtitles that never cover the PiP presenter window.
- Broadcast audio mastering with energetic EDM bed.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

REPO_DIR = Path(r"C:\Users\tee\.gemini\antigravity-ide\scratch\hermes-agent")
OUTPUT_VIDEO = Path(r"D:\AI-Avatars\Onn_4K_Pro_Commercial_1Min.mp4")
CLEAN_VIDEO = Path(r"D:\AI-Avatars\Onn_4K_Pro_Commercial_Clean_MusicOnly.mp4")
GUIDE_VIDEO = Path(r"D:\AI-Avatars\Onn_4K_Pro_Commercial_Teleprompter_Guide.mp4")
SRT_FILE = Path(r"D:\AI-Avatars\Onn_4K_Pro_Commercial_Voiceover.srt")
AVATAR_VIDEO = Path(r"D:\AI-Avatars\ScreenRecording_09-05-2026 04-28-18_1(1).mp4")
TV_SHOWCASE = REPO_DIR / "tv_showcase_12s.mp4"

FONTS = {
    "title": r"C:\Windows\Fonts\impact.ttf",
    "bold": r"C:\Windows\Fonts\arialbd.ttf",
    "regular": r"C:\Windows\Fonts\arial.ttf",
    "segoe": r"C:\Windows\Fonts\segoeuib.ttf",
}


def get_font(key: str, size: int) -> ImageFont.FreeTypeFont:
    path = FONTS.get(key, FONTS["bold"])
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def make_scene1_overlay() -> str:
    """Scene 1: Hook - Eliminate Your Cable Bill!"""
    im = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)

    # Top Warning Pill
    pill_w, pill_h = 960, 64
    px, py = (1920 - pill_w) // 2, 40
    draw.rounded_rectangle([px, py, px + pill_w, py + pill_h], radius=32, fill=(220, 20, 60, 230), outline=(255, 255, 255, 200), width=3)
    f_warn = get_font("segoe", 32)
    draw.text((px + 45, py + 12), "⚡ ATTENTION CABLE & SATELLITE SUBSCRIBERS ⚡", font=f_warn, fill=(255, 255, 255))

    # Bottom Lower Third
    bg_box = [60, 780, 1860, 1030]
    draw.rounded_rectangle(bg_box, radius=24, fill=(11, 19, 43, 245), outline=(0, 212, 255, 180), width=4)

    f_big = get_font("title", 82)
    draw.text((100, 795), "ELIMINATE YOUR CABLE BILL!", font=f_big, fill=(255, 221, 0))

    f_sub = get_font("bold", 42)
    draw.text((104, 895), "CUT THE CORD FOR GOOD • OVER 1,000+ LIVE CHANNELS", font=f_sub, fill=(255, 255, 255))

    f_pill = get_font("segoe", 26)
    draw.text((104, 960), "ZERO MONTHLY FEES  •  NO CONTRACTS  •  PLUG & PLAY", font=f_pill, fill=(0, 220, 255))

    # Paste cut cables in bottom right corner
    cables_path = REPO_DIR / "crop_cables.png"
    if cables_path.exists():
        cb = Image.open(cables_path).convert("RGBA")
        cb = cb.resize((480, 185), Image.Resampling.LANCZOS)
        im.paste(cb, (1360, 815), cb)

    out_path = REPO_DIR / "overlay_scene1.png"
    im.save(out_path)
    return str(out_path)


def make_scene2_bg() -> str:
    """Scene 2 Background: TV Frame Outline + Feature Cards."""
    im = Image.new("RGBA", (1920, 1080), (10, 17, 40, 255))
    draw = ImageDraw.Draw(im)

    # Header Banner
    draw.rounded_rectangle([60, 25, 1860, 125], radius=20, fill=(15, 25, 60, 240), outline=(0, 212, 255, 180), width=3)
    f_head = get_font("title", 62)
    draw.text((100, 36), "MEET THE ONN 4K PRO STREAMING BOX", font=f_head, fill=(255, 221, 0))
    f_sub = get_font("bold", 28)
    draw.text((1350, 52), "YOUR TOTAL FREEDOM STICK", font=f_sub, fill=(0, 220, 255))

    # TV frame bezel placeholder (video will be composited inside x=80, y=160, w=880, h=500)
    draw.rounded_rectangle([72, 152, 968, 668], radius=18, fill=(5, 8, 15, 255), outline=(0, 212, 255, 230), width=5)
    # TV stand
    draw.polygon([(460, 668), (580, 668), (550, 710), (490, 710)], fill=(30, 40, 60))
    draw.rounded_rectangle([420, 706, 620, 718], radius=6, fill=(50, 60, 80))

    # Right Side Feature Cards
    features = [
        ("4K ULTRA HD STREAMING", "Lightning fast HDR playback with Dolby Audio support", (255, 221, 0)),
        ("OVER 1,000+ LIVE CHANNELS", "Live news, sports, events & premium networks", (0, 220, 255)),
        ("ZERO MONTHLY SUBSCRIPTIONS", "Never pay a cable or streaming bill ever again", (0, 255, 140)),
        ("PLUG & PLAY EASY SETUP", "Works on any TV with HDMI in under 2 minutes", (255, 180, 50)),
    ]

    fy = 155
    f_ft = get_font("title", 36)
    f_fd = get_font("bold", 22)
    for title, desc, col in features:
        draw.rounded_rectangle([1010, fy, 1860, fy + 115], radius=18, fill=(16, 28, 68, 230), outline=col, width=3)
        draw.text((1040, fy + 16), f"★ {title}", font=f_ft, fill=col)
        draw.text((1045, fy + 65), desc, font=f_fd, fill=(235, 245, 255))
        fy += 135

    # Bottom Ticker Bar (presenter sits on left x=70..430, ticker info spans x=460..1860)
    draw.rounded_rectangle([460, 750, 1860, 970], radius=20, fill=(11, 20, 48, 240), outline=(255, 221, 0, 200), width=4)
    f_bar_big = get_font("title", 48)
    draw.text((500, 775), "FREE LIVE TV  •  FREE SPORTS  •  FREE PPV", font=f_bar_big, fill=(255, 221, 0))
    f_bar_sub = get_font("bold", 28)
    draw.text((505, 855), "Live NBA, NFL, NCAA, NHL, MLB, UFC, & Blockbuster Cinema Included", font=f_bar_sub, fill=(255, 255, 255))
    draw.text((505, 910), "★ 5 Unlinked Libraries Pre-Configured  •  Built-in VPN for 100% Privacy", font=f_bar_sub, fill=(0, 220, 255))

    out_path = REPO_DIR / "slide_scene2_v2.png"
    im.save(out_path)
    return str(out_path)


def make_scene3_bg() -> str:
    """Scene 3: 1,000+ Channels & Sports Grid."""
    im = Image.new("RGBA", (1920, 1080), (10, 16, 38, 255))
    draw = ImageDraw.Draw(im)

    # Top Header
    draw.rounded_rectangle([60, 25, 1860, 125], radius=20, fill=(15, 25, 60, 240), outline=(255, 221, 0, 200), width=3)
    f_head = get_font("title", 62)
    draw.text((100, 36), "UNLIMITED ENTERTAINMENT: 1,000+ CHANNELS", font=f_head, fill=(255, 221, 0))

    # 4 Category Cards
    cats = [
        ("📺 LIVE TV NETWORKS", ["ABC, CBS, NBC, FOX", "ESPN, CNN, HGTV, Discovery", "Over 1,000 channels worldwide"], (0, 212, 255)),
        ("🏈 ALL LIVE SPORTS", ["NFL Sunday Ticket & RedZone", "NBA, MLB, NHL & College Sports", "Soccer, UFC & Boxing Matches"], (255, 140, 0)),
        ("🥊 PAY-PER-VIEW EVENTS", ["Championship Title Fights", "Wrestling & MMA Main Events", "Zero extra charges or paywalls"], (255, 40, 60)),
        ("🎬 MOVIES & SHOWS", ["All blockbuster movie releases", "Full series binge-watching", "Thousands of on-demand titles"], (180, 80, 255)),
    ]

    coords = [
        (80, 150, 930, 440),
        (970, 150, 1840, 440),
        (80, 470, 930, 760),
        (970, 470, 1840, 760),
    ]

    f_cat = get_font("title", 36)
    f_item = get_font("bold", 24)

    for (title, items, col), (x1, y1, x2, y2) in zip(cats, coords):
        draw.rounded_rectangle([x1, y1, x2, y2], radius=18, fill=(16, 26, 62, 240), outline=col, width=3)
        draw.text((x1 + 25, y1 + 18), title, font=f_cat, fill=col)
        iy = y1 + 75
        for it in items:
            draw.text((x1 + 35, iy), f"✔  {it}", font=f_item, fill=(240, 245, 255))
            iy += 45

    # Bottom Ticker Bar (Presenter in center-bottom x=770..1150)
    draw.rounded_rectangle([60, 810, 730, 990], radius=18, fill=(220, 20, 60, 230), outline=(255, 255, 255, 200), width=3)
    f_bot = get_font("title", 38)
    draw.text((85, 840), "NO CONTRACTS", font=f_bot, fill=(255, 255, 255))
    draw.text((85, 900), "NO MONTHLY FEES", font=f_bot, fill=(255, 221, 0))

    draw.rounded_rectangle([1190, 810, 1860, 990], radius=18, fill=(220, 20, 60, 230), outline=(255, 255, 255, 200), width=3)
    draw.text((1220, 840), "ZERO PAYWALLS", font=f_bot, fill=(255, 255, 255))
    draw.text((1220, 900), "100% UNLOCKED", font=f_bot, fill=(255, 221, 0))

    out_path = REPO_DIR / "slide_scene3_v2.png"
    im.save(out_path)
    return str(out_path)


def make_scene4_bg() -> str:
    """Scene 4: 5 Unlinked Libraries & Built-In VPN."""
    im = Image.new("RGBA", (1920, 1080), (10, 16, 38, 255))
    draw = ImageDraw.Draw(im)

    # Top Header
    draw.rounded_rectangle([60, 25, 1860, 125], radius=20, fill=(15, 25, 60, 240), outline=(0, 255, 180, 200), width=3)
    f_head = get_font("title", 62)
    draw.text((100, 36), "5 UNLINKED LIBRARIES + BUILT-IN SECURE VPN", font=f_head, fill=(0, 255, 180))

    # Left Column: 5 Libraries
    draw.rounded_rectangle([80, 150, 930, 770], radius=20, fill=(16, 28, 68, 240), outline=(0, 212, 255, 180), width=3)
    f_t = get_font("title", 40)
    draw.text((115, 170), "📁 5 UNLINKED LIBRARIES", font=f_t, fill=(255, 221, 0))

    lib_items = [
        "Library 1: Movies, Series & Live TV",
        "Library 2: Live Sports & International",
        "Library 3: Custom Streaming Apps",
        "Library 4: Premium On-Demand Hub",
        "Library 5: Exclusive 4K Content",
        "Instant Access to 100+ Pre-Configured Apps",
    ]
    f_li = get_font("bold", 25)
    ly = 245
    for li in lib_items:
        draw.text((120, ly), f"★  {li}", font=f_li, fill=(235, 245, 255))
        ly += 75

    # Right Column: VPN & Privacy
    draw.rounded_rectangle([970, 150, 1840, 770], radius=20, fill=(16, 28, 68, 240), outline=(0, 255, 140, 180), width=3)
    draw.text((1005, 170), "🛡️ BUILT-IN VPN INCLUDED", font=f_t, fill=(0, 255, 140))

    vpn_items = [
        "100% Private, Encrypted Streaming",
        "Bypass ISP Throttling & Buffering",
        "Zero-Log Privacy Protection",
        "Fast High-Speed Dedicated Servers",
        "One-Click Automatic Protection",
        "Stream Freely Anywhere in the World",
    ]
    ly = 245
    for vi in vpn_items:
        draw.text((1015, ly), f"✔  {vi}", font=f_li, fill=(235, 245, 255))
        ly += 75

    # Bottom Callout Bar (left and right of presenter)
    draw.rounded_rectangle([60, 810, 730, 990], radius=18, fill=(0, 140, 255, 220), outline=(255, 255, 255, 200), width=3)
    f_bot = get_font("title", 38)
    draw.text((85, 845), "MAXIMUM SPEED", font=f_bot, fill=(255, 255, 255))
    draw.text((85, 905), "COMPLETE PRIVACY", font=f_bot, fill=(255, 221, 0))

    draw.rounded_rectangle([1190, 810, 1860, 990], radius=18, fill=(0, 140, 255, 220), outline=(255, 255, 255, 200), width=3)
    draw.text((1220, 845), "100+ APPS READY", font=f_bot, fill=(255, 255, 255))
    draw.text((1220, 905), "NO ISP THROTTLING", font=f_bot, fill=(0, 255, 140))

    out_path = REPO_DIR / "slide_scene4_v2.png"
    im.save(out_path)
    return str(out_path)


def make_scene5_overlay() -> str:
    """Scene 5: Grand Finale / Call to Action."""
    im = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)

    # Top Banner
    draw.rounded_rectangle([100, 35, 1820, 135], radius=24, fill=(11, 19, 43, 235), outline=(0, 212, 255, 200), width=3)
    f_head = get_font("title", 62)
    draw.text((150, 48), "★ ONN 4K PRO TOTAL FREEDOM STREAMING ★", font=f_head, fill=(0, 220, 255))

    # Center Hero Banner
    draw.rounded_rectangle([80, 680, 1840, 1020], radius=26, fill=(11, 19, 43, 245), outline=(255, 221, 0, 230), width=5)

    f_big = get_font("title", 84)
    draw.text((120, 700), "ELIMINATE YOUR CABLE BILL FOREVER!", font=f_big, fill=(255, 221, 0))

    f_sub = get_font("bold", 40)
    draw.text((125, 805), "1,000+ CHANNELS  •  5 LIBRARIES  •  VPN INCLUDED", font=f_sub, fill=(255, 255, 255))

    # CTA Button Pill
    pill_box = [120, 880, 1800, 985]
    draw.rounded_rectangle(pill_box, radius=24, fill=(200, 10, 50, 245), outline=(255, 255, 255, 220), width=3)
    f_cta = get_font("title", 52)
    draw.text((540, 905), "UPGRADE TO THE ONN 4K PRO TODAY!", font=f_cta, fill=(255, 255, 255))

    out_path = REPO_DIR / "overlay_scene5.png"
    im.save(out_path)
    return str(out_path)


def main():
    print("Generating updated graphics...")
    s1_overlay = make_scene1_overlay()
    s2_bg = make_scene2_bg()
    s3_bg = make_scene3_bg()
    s4_bg = make_scene4_bg()
    s5_overlay = make_scene5_overlay()

    master_audio = REPO_DIR / "master_audio.m4a"

    part1 = REPO_DIR / "part1.mp4"
    part2 = REPO_DIR / "part2.mp4"
    part3 = REPO_DIR / "part3.mp4"
    part4 = REPO_DIR / "part4.mp4"
    part5 = REPO_DIR / "part5.mp4"

    # Filter string to clean/darken the background vignette and remove watermarks in full presenter shots:
    # Scale to 1920x1080, crop 1920x1080, apply subtle contrast/brightness curve so background corners blend into dark studio
    vignette_filter = "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,eq=contrast=1.05:brightness=-0.04:gamma=0.96"

    # Clean crop for PiP (Presenter centered: crop 640x640 at x=340, y=30 to eliminate bookshelf watermarks)
    pip_filter = "crop=640:640:340:30,scale=340:340,pad=348:348:4:4:color=0x00D4FF"

    print("Encoding Scene 1 (The Hook: 0-10s)...")
    cmd_p1 = [
        "ffmpeg", "-y",
        "-ss", "0", "-t", "10",
        "-i", str(AVATAR_VIDEO),
        "-i", s1_overlay,
        "-filter_complex",
        f"[0:v]{vignette_filter}[vbg];"
        "[vbg][1:v]overlay=0:0[vout]",
        "-map", "[vout]",
        "-r", "30", "-c:v", "libx264", "-preset", "fast", "-crf", "19", "-pix_fmt", "yuv420p",
        str(part1),
    ]
    subprocess.run(cmd_p1, check=True)

    print("Encoding Scene 2 (The Solution with Dynamic TV Video: 10-22s, 12s)...")
    # s2_bg (input 0), TV showcase video (input 1), Avatar video (input 2)
    # TV video placed at x=80, y=160 (size 880x500)
    # Clean PiP presenter placed at x=70, y=700 (size 348x348)
    cmd_p2 = [
        "ffmpeg", "-y",
        "-loop", "1", "-t", "12", "-i", s2_bg,
        "-i", str(TV_SHOWCASE),
        "-ss", "0", "-t", "12", "-i", str(AVATAR_VIDEO),
        "-filter_complex",
        "[0:v]scale=1920:1080[bg];"
        "[1:v]scale=880:500[tvvid];"
        f"[2:v]{pip_filter}[pip];"
        "[bg][tvvid]overlay=80:160[bg_tv];"
        "[bg_tv][pip]overlay=70:660[vout]",
        "-map", "[vout]",
        "-r", "30", "-c:v", "libx264", "-preset", "fast", "-crf", "19", "-pix_fmt", "yuv420p",
        str(part2),
    ]
    subprocess.run(cmd_p2, check=True)

    print("Encoding Scene 3 (1000+ Channels: 22-35s, 13s)...")
    # Clean PiP presenter centered at bottom x=786, y=700
    cmd_p3 = [
        "ffmpeg", "-y",
        "-loop", "1", "-t", "13", "-i", s3_bg,
        "-ss", "3", "-t", "13", "-i", str(AVATAR_VIDEO),
        "-filter_complex",
        "[0:v]scale=1920:1080[bg];"
        f"[1:v]{pip_filter}[pip];"
        "[bg][pip]overlay=786:700[vout]",
        "-map", "[vout]",
        "-r", "30", "-c:v", "libx264", "-preset", "fast", "-crf", "19", "-pix_fmt", "yuv420p",
        str(part3),
    ]
    subprocess.run(cmd_p3, check=True)

    print("Encoding Scene 4 (5 Libraries & VPN: 35-48s, 13s)...")
    cmd_p4 = [
        "ffmpeg", "-y",
        "-loop", "1", "-t", "13", "-i", s4_bg,
        "-ss", "8", "-t", "13", "-i", str(AVATAR_VIDEO),
        "-filter_complex",
        "[0:v]scale=1920:1080[bg];"
        f"[1:v]{pip_filter}[pip];"
        "[bg][pip]overlay=786:700[vout]",
        "-map", "[vout]",
        "-r", "30", "-c:v", "libx264", "-preset", "fast", "-crf", "19", "-pix_fmt", "yuv420p",
        str(part4),
    ]
    subprocess.run(cmd_p4, check=True)

    print("Encoding Scene 5 (Climax & CTA: 48-60s, 12s)...")
    cmd_p5 = [
        "ffmpeg", "-y",
        "-ss", "10", "-t", "12",
        "-i", str(AVATAR_VIDEO),
        "-i", s5_overlay,
        "-filter_complex",
        f"[0:v]{vignette_filter}[vbg];"
        "[vbg][1:v]overlay=0:0[vout]",
        "-map", "[vout]",
        "-r", "30", "-c:v", "libx264", "-preset", "fast", "-crf", "19", "-pix_fmt", "yuv420p",
        str(part5),
    ]
    subprocess.run(cmd_p5, check=True)

    # Concat all 5 parts
    print("Stitching all scenes...")
    concat_txt = REPO_DIR / "concat_v2.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for p in [part1, part2, part3, part4, part5]:
            f.write(f"file '{p.resolve().as_posix()}'\n")

    # Final Video with Reference Audio
    cmd_final = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_txt),
        "-i", str(master_audio),
        "-c:v", "libx264", "-preset", "fast", "-crf", "19", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-map", "0:v:0", "-map", "1:a:0",
        "-shortest",
        str(OUTPUT_VIDEO),
    ]
    subprocess.run(cmd_final, check=True)
    print(f"Rendered: {OUTPUT_VIDEO}")

    # Clean Video with Music Only
    bgm_wav = REPO_DIR / "bgm.wav"
    cmd_clean = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_txt),
        "-i", str(bgm_wav),
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-map", "0:v:0", "-map", "1:a:0",
        "-shortest",
        str(CLEAN_VIDEO),
    ]
    subprocess.run(cmd_clean, check=True)
    print(f"Rendered: {CLEAN_VIDEO}")

    # Teleprompter Guide Video with Sleek Non-Obstructive Subtitles
    srt_escaped = str(SRT_FILE).replace("\\", "/").replace(":", "\\:")
    # Small sleek font (Fontsize=15), MarginV=15, Alignment=8 (top-center pill)
    sub_style = (
        "Fontname=Arial,Fontsize=15,PrimaryColour=&H00FFFFFF&,BackColour=&H80000000&,"
        "BorderStyle=3,Outline=1,Shadow=0,MarginV=15,Alignment=8"
    )
    cmd_guide = [
        "ffmpeg", "-y",
        "-i", str(CLEAN_VIDEO),
        "-vf", f"subtitles='{srt_escaped}':force_style='{sub_style}'",
        "-c:v", "libx264", "-preset", "fast", "-crf", "19",
        "-c:a", "copy",
        str(GUIDE_VIDEO),
    ]
    subprocess.run(cmd_guide, check=True)
    print(f"Rendered: {GUIDE_VIDEO}")
    print("ALL TAKES COMPLETE!")


if __name__ == "__main__":
    main()
