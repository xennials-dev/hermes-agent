#!/usr/bin/env python3
"""Build the 60-second Onn 4K Pro Commercial Video (Version 3 - Watermark-Free & Non-Overlapping Teleprompter).

Improvements:
1. COMPLETE WATERMARK ELIMINATION:
   - Scenes 1 & 5: Clean broadcast studio stage with high-tech side graphic pillars + radial studio lighting vignette, completely covering the bookshelf HeyGen watermarks.
   - Scenes 2, 3, 4: Tight PiP framing around presenter (crop=640:640:340:30) with zero watermarks and glowing cyan border.
2. DYNAMIC TV SCREEN VIDEO:
   - Plays inside the TV bezel in Scene 2 with NBA, NFL, NCAA, NHL, and Blockbuster Movies + official broadcast badges.
3. TELEPROMPTER GUIDE FIX:
   - Subtitle text sized to clean 21pt font with PlayResX=1920/PlayResY=1080.
   - Exact pixel positioning that NEVER overlaps the PiP window, the presenter, or graphic cards.
4. BROADCAST AUDIO MASTERING:
   - Energetic EDM music bed + reference voiceover, plus clean music-only mix.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

REPO_DIR = Path(r"C:\Users\tee\.gemini\antigravity-ide\scratch\hermes-agent")
OUTPUT_VIDEO = Path(r"D:\AI-Avatars\Onn_4K_Pro_Commercial_1Min.mp4")
CLEAN_VIDEO = Path(r"D:\AI-Avatars\Onn_4K_Pro_Commercial_Clean_MusicOnly.mp4")
GUIDE_VIDEO = Path(r"D:\AI-Avatars\Onn_4K_Pro_Commercial_Teleprompter_Guide.mp4")
ASS_FILE = Path(r"D:\AI-Avatars\Onn_4K_Pro_Commercial_Voiceover.ass")
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


def make_studio_vignette() -> str:
    """Generate subtle dark studio vignette to dim bookshelf background behind presenter."""
    w, h = 1920, 1080
    cx, cy = 960, 380
    Y, X = np.ogrid[:h, :w]
    dist = np.sqrt((X - cx) ** 2 + ((Y - cy) * 1.25) ** 2)

    r_inner, r_outer = 210, 460
    alpha = np.clip((dist - r_inner) / (r_outer - r_inner), 0, 1)

    img_arr = np.zeros((h, w, 4), dtype=np.uint8)
    img_arr[..., 0] = 8
    img_arr[..., 1] = 14
    img_arr[..., 2] = 32
    img_arr[..., 3] = (alpha * 225).astype(np.uint8)

    out_path = REPO_DIR / "studio_vignette.png"
    Image.fromarray(img_arr, mode="RGBA").save(out_path)
    return str(out_path)


def make_scene1_overlay() -> str:
    """Scene 1: Hook with Broadcast Studio Side Pillars."""
    im = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)

    # Left broadcast sidebar (x: 0..420)
    draw.rectangle([0, 0, 420, 1080], fill=(8, 14, 32, 252))
    draw.line([(420, 0), (420, 1080)], fill=(0, 212, 255, 230), width=4)

    f_title = get_font("title", 34)
    f_sub = get_font("bold", 20)
    f_accent = get_font("segoe", 18)

    # Left Column Badges
    draw.rounded_rectangle([25, 45, 395, 175], radius=16, fill=(16, 28, 68, 235), outline=(255, 221, 0), width=2)
    draw.text((45, 60), "★ ONN 4K PRO", font=f_title, fill=(255, 221, 0))
    draw.text((45, 110), "The #1 Streaming Box of 2026", font=f_sub, fill=(255, 255, 255))
    draw.text((45, 140), "Zero Monthly Fees Forever", font=f_accent, fill=(0, 220, 255))

    draw.rounded_rectangle([25, 195, 395, 325], radius=16, fill=(16, 28, 68, 235), outline=(0, 255, 140), width=2)
    draw.text((45, 210), "★ 1,000+ LIVE CHANNELS", font=f_title, fill=(0, 255, 140))
    draw.text((45, 260), "Cable, Sports, News, Movies", font=f_sub, fill=(255, 255, 255))
    draw.text((45, 290), "Global Networks Included", font=f_accent, fill=(0, 220, 255))

    draw.rounded_rectangle([25, 345, 395, 475], radius=16, fill=(16, 28, 68, 235), outline=(255, 140, 0), width=2)
    draw.text((45, 360), "★ ALL LIVE SPORTS", font=f_title, fill=(255, 140, 0))
    draw.text((45, 410), "NFL, NBA, NCAA, NHL, PPV", font=f_sub, fill=(255, 255, 255))
    draw.text((45, 440), "Every Game In Crystal 4K", font=f_accent, fill=(0, 220, 255))

    draw.rounded_rectangle([25, 495, 395, 625], radius=16, fill=(16, 28, 68, 235), outline=(0, 212, 255), width=2)
    draw.text((45, 510), "★ 4K ULTRA HD HDR", font=f_title, fill=(0, 212, 255))
    draw.text((45, 560), "Dolby Audio Powered", font=f_sub, fill=(255, 255, 255))
    draw.text((45, 590), "Lightning Fast Playback", font=f_accent, fill=(0, 220, 255))

    # Right broadcast sidebar (x: 1500..1920)
    draw.rectangle([1500, 0, 1920, 1080], fill=(8, 14, 32, 252))
    draw.line([(1500, 0), (1500, 1080)], fill=(0, 212, 255, 230), width=4)

    draw.rounded_rectangle([1525, 45, 1895, 175], radius=16, fill=(16, 28, 68, 235), outline=(0, 212, 255), width=2)
    draw.text((1545, 60), "★ 5 UNLINKED LIBRARIES", font=f_title, fill=(0, 212, 255))
    draw.text((1545, 110), "Pre-loaded & Ready to Stream", font=f_sub, fill=(255, 255, 255))
    draw.text((1545, 140), "10,000+ On-Demand Movies", font=f_accent, fill=(0, 220, 255))

    draw.rounded_rectangle([1525, 195, 1895, 325], radius=16, fill=(16, 28, 68, 235), outline=(255, 221, 0), width=2)
    draw.text((1545, 210), "★ BUILT-IN VPN PRIVACY", font=f_title, fill=(255, 221, 0))
    draw.text((1545, 260), "100% Anonymous & Secure", font=f_sub, fill=(255, 255, 255))
    draw.text((1545, 290), "Zero Throttling or Tracking", font=f_accent, fill=(0, 220, 255))

    draw.rounded_rectangle([1525, 345, 1895, 475], radius=16, fill=(16, 28, 68, 235), outline=(255, 40, 60), width=2)
    draw.text((1545, 360), "★ ZERO CONTRACTS", font=f_title, fill=(255, 40, 60))
    draw.text((1545, 410), "Plug & Play on Any TV", font=f_sub, fill=(255, 255, 255))
    draw.text((1545, 440), "Eliminate Bills Forever", font=f_accent, fill=(0, 220, 255))

    draw.rounded_rectangle([1525, 495, 1895, 625], radius=16, fill=(16, 28, 68, 235), outline=(0, 255, 140), width=2)
    draw.text((1545, 510), "★ PLUG & PLAY", font=f_title, fill=(0, 255, 140))
    draw.text((1545, 560), "Setup in Under 2 Minutes", font=f_sub, fill=(255, 255, 255))
    draw.text((1545, 590), "Works on Any Television", font=f_accent, fill=(0, 220, 255))

    # Top Warning Pill
    pill_w, pill_h = 960, 58
    px, py = (1920 - pill_w) // 2, 22
    draw.rounded_rectangle([px, py, px + pill_w, py + pill_h], radius=29, fill=(220, 20, 60, 240), outline=(255, 255, 255, 200), width=3)
    f_warn = get_font("segoe", 28)
    draw.text((px + 65, py + 11), "⚡ ATTENTION CABLE & SATELLITE SUBSCRIBERS ⚡", font=f_warn, fill=(255, 255, 255))

    # Bottom Lower Third Banner
    bg_box = [60, 770, 1860, 1030]
    draw.rounded_rectangle(bg_box, radius=24, fill=(11, 19, 43, 250), outline=(0, 212, 255, 200), width=4)
    f_big = get_font("title", 80)
    draw.text((100, 785), "ELIMINATE YOUR CABLE BILL!", font=f_big, fill=(255, 221, 0))
    f_sub2 = get_font("bold", 38)
    draw.text((104, 885), "CUT THE CORD FOR GOOD • OVER 1,000+ LIVE CHANNELS", font=f_sub2, fill=(255, 255, 255))
    f_pill2 = get_font("segoe", 26)
    draw.text((104, 955), "ZERO MONTHLY FEES  •  NO CONTRACTS  •  PLUG & PLAY", font=f_pill2, fill=(0, 220, 255))

    # Paste cut cables in bottom right corner
    cables_path = REPO_DIR / "crop_cables.png"
    if cables_path.exists():
        cb = Image.open(cables_path).convert("RGBA")
        cb = cb.resize((460, 175), Image.Resampling.LANCZOS)
        im.paste(cb, (1370, 805), cb)

    out_path = REPO_DIR / "overlay_scene1_v3.png"
    im.save(out_path)
    return str(out_path)


def make_scene2_bg() -> str:
    """Scene 2 Background: TV Frame Outline + Feature Cards."""
    im = Image.new("RGBA", (1920, 1080), (10, 17, 40, 255))
    draw = ImageDraw.Draw(im)

    # Header Banner
    draw.rounded_rectangle([60, 20, 1860, 115], radius=20, fill=(15, 25, 60, 240), outline=(0, 212, 255, 180), width=3)
    f_head = get_font("title", 58)
    draw.text((100, 30), "MEET THE ONN 4K PRO STREAMING BOX", font=f_head, fill=(255, 221, 0))
    f_sub = get_font("bold", 26)
    draw.text((1370, 46), "YOUR TOTAL FREEDOM STICK", font=f_sub, fill=(0, 220, 255))

    # TV frame bezel placeholder (video will be composited inside x=80, y=145, w=880, h=500)
    draw.rounded_rectangle([72, 137, 968, 653], radius=18, fill=(5, 8, 15, 255), outline=(0, 212, 255, 230), width=5)
    # TV stand
    draw.polygon([(460, 653), (580, 653), (550, 695), (490, 695)], fill=(30, 40, 60))
    draw.rounded_rectangle([420, 691, 620, 703], radius=6, fill=(50, 60, 80))

    # Right Side Feature Cards
    features = [
        ("4K ULTRA HD STREAMING", "Lightning fast HDR playback with Dolby Audio support", (255, 221, 0)),
        ("OVER 1,000+ LIVE CHANNELS", "Live news, sports, events & premium networks", (0, 220, 255)),
        ("ZERO MONTHLY SUBSCRIPTIONS", "Never pay a cable or streaming bill ever again", (0, 255, 140)),
        ("PLUG & PLAY EASY SETUP", "Works on any TV with HDMI in under 2 minutes", (255, 180, 50)),
    ]

    fy = 145
    f_ft = get_font("title", 35)
    f_fd = get_font("bold", 22)
    for title, desc, col in features:
        draw.rounded_rectangle([1010, fy, 1860, fy + 110], radius=18, fill=(16, 28, 68, 230), outline=col, width=3)
        draw.text((1040, fy + 16), f"★ {title}", font=f_ft, fill=col)
        draw.text((1045, fy + 63), desc, font=f_fd, fill=(235, 245, 255))
        fy += 128

    # Bottom Ticker Bar (presenter sits on left x=70..418, ticker info spans x=460..1860)
    draw.rounded_rectangle([460, 755, 1860, 975], radius=20, fill=(11, 20, 48, 240), outline=(255, 221, 0, 200), width=4)
    f_bar_big = get_font("title", 46)
    draw.text((500, 775), "FREE LIVE TV  •  FREE SPORTS  •  FREE PPV", font=f_bar_big, fill=(255, 221, 0))
    f_bar_sub = get_font("bold", 27)
    draw.text((505, 850), "Live NBA, NFL, NCAA, NHL, MLB, UFC, & Blockbuster Cinema Included", font=f_bar_sub, fill=(255, 255, 255))
    draw.text((505, 905), "★ 5 Unlinked Libraries Pre-Configured  •  Built-in VPN for 100% Privacy", font=f_bar_sub, fill=(0, 220, 255))

    out_path = REPO_DIR / "slide_scene2_v3.png"
    im.save(out_path)
    return str(out_path)


def make_scene3_bg() -> str:
    """Scene 3: 1,000+ Channels & Sports Grid (Optimized for Teleprompter & PiP)."""
    im = Image.new("RGBA", (1920, 1080), (10, 16, 38, 255))
    draw = ImageDraw.Draw(im)

    # Top Header
    draw.rounded_rectangle([60, 20, 1860, 115], radius=20, fill=(15, 25, 60, 240), outline=(255, 221, 0, 200), width=3)
    f_head = get_font("title", 58)
    draw.text((100, 30), "UNLIMITED ENTERTAINMENT: 1,000+ CHANNELS", font=f_head, fill=(255, 221, 0))

    # 4 Category Cards (y: 155..655)
    cats = [
        ("📺 LIVE TV NETWORKS", ["ABC, CBS, NBC, FOX", "ESPN, CNN, HGTV, Discovery", "Over 1,000 channels worldwide"], (0, 212, 255)),
        ("🏈 ALL LIVE SPORTS", ["NFL Sunday Ticket & RedZone", "NBA, MLB, NHL & College Sports", "Soccer, UFC & Boxing Matches"], (255, 140, 0)),
        ("🥊 PAY-PER-VIEW EVENTS", ["Championship Title Fights", "Wrestling & MMA Main Events", "Zero extra charges or paywalls"], (255, 40, 60)),
        ("🎬 MOVIES & SHOWS", ["All blockbuster movie releases", "Full series binge-watching", "Thousands of on-demand titles"], (180, 80, 255)),
    ]

    coords = [
        (80, 155, 930, 395),
        (970, 155, 1840, 395),
        (80, 420, 930, 660),
        (970, 420, 1840, 660),
    ]

    f_cat = get_font("title", 34)
    f_item = get_font("bold", 23)

    for (title, items, col), (x1, y1, x2, y2) in zip(cats, coords):
        draw.rounded_rectangle([x1, y1, x2, y2], radius=18, fill=(16, 26, 62, 240), outline=col, width=3)
        draw.text((x1 + 25, y1 + 16), title, font=f_cat, fill=col)
        iy = y1 + 68
        for it in items:
            draw.text((x1 + 35, iy), f"✔  {it}", font=f_item, fill=(240, 245, 255))
            iy += 42

    # Bottom Ticker Pills (Presenter centered at x=786..1134, y=700..1048)
    draw.rounded_rectangle([60, 770, 730, 970], radius=18, fill=(220, 20, 60, 235), outline=(255, 255, 255, 200), width=3)
    f_bot = get_font("title", 40)
    draw.text((85, 800), "NO CONTRACTS", font=f_bot, fill=(255, 255, 255))
    draw.text((85, 875), "NO MONTHLY FEES", font=f_bot, fill=(255, 221, 0))

    draw.rounded_rectangle([1190, 770, 1860, 970], radius=18, fill=(220, 20, 60, 235), outline=(255, 255, 255, 200), width=3)
    draw.text((1220, 800), "ZERO PAYWALLS", font=f_bot, fill=(255, 255, 255))
    draw.text((1220, 875), "100% UNLOCKED", font=f_bot, fill=(255, 221, 0))

    out_path = REPO_DIR / "slide_scene3_v3.png"
    im.save(out_path)
    return str(out_path)


def make_scene4_bg() -> str:
    """Scene 4: 5 Unlinked Libraries & Built-In VPN."""
    im = Image.new("RGBA", (1920, 1080), (10, 16, 38, 255))
    draw = ImageDraw.Draw(im)

    # Top Header
    draw.rounded_rectangle([60, 20, 1860, 115], radius=20, fill=(15, 25, 60, 240), outline=(0, 255, 180, 200), width=3)
    f_head = get_font("title", 58)
    draw.text((100, 30), "5 UNLINKED LIBRARIES + BUILT-IN SECURE VPN", font=f_head, fill=(0, 255, 180))

    # Left Column: 5 Libraries (y: 155..665)
    draw.rounded_rectangle([80, 155, 930, 665], radius=20, fill=(16, 28, 68, 240), outline=(0, 212, 255, 180), width=3)
    f_t = get_font("title", 36)
    draw.text((115, 175), "📁 5 UNLINKED LIBRARIES", font=f_t, fill=(255, 221, 0))

    lib_items = [
        "Library 1: Movies, Series & Live TV",
        "Library 2: Live Sports & International",
        "Library 3: Custom Streaming Apps",
        "Library 4: Premium On-Demand Hub",
        "Library 5: Exclusive 4K Content",
    ]
    f_li = get_font("bold", 23)
    ly = 245
    for li in lib_items:
        draw.text((120, ly), f"★  {li}", font=f_li, fill=(235, 245, 255))
        ly += 68

    # Right Column: VPN & Privacy
    draw.rounded_rectangle([970, 155, 1840, 665], radius=20, fill=(16, 28, 68, 240), outline=(0, 255, 140, 180), width=3)
    draw.text((1005, 175), "🛡️ BUILT-IN VPN INCLUDED", font=f_t, fill=(0, 255, 140))

    vpn_items = [
        "100% Private, Encrypted Streaming",
        "Bypass ISP Throttling & Buffering",
        "Zero-Log Privacy Protection",
        "Fast High-Speed Dedicated Servers",
        "One-Click Automatic Protection",
    ]
    ly = 245
    for vi in vpn_items:
        draw.text((1015, ly), f"✔  {vi}", font=f_li, fill=(235, 245, 255))
        ly += 68

    # Bottom Callout Bar (left and right of presenter)
    draw.rounded_rectangle([60, 770, 730, 970], radius=18, fill=(0, 140, 255, 230), outline=(255, 255, 255, 200), width=3)
    f_bot = get_font("title", 40)
    draw.text((85, 805), "MAXIMUM SPEED", font=f_bot, fill=(255, 255, 255))
    draw.text((85, 880), "COMPLETE PRIVACY", font=f_bot, fill=(255, 221, 0))

    draw.rounded_rectangle([1190, 770, 1860, 970], radius=18, fill=(0, 140, 255, 230), outline=(255, 255, 255, 200), width=3)
    draw.text((1220, 805), "100+ APPS READY", font=f_bot, fill=(255, 255, 255))
    draw.text((1220, 880), "NO ISP THROTTLING", font=f_bot, fill=(0, 255, 140))

    out_path = REPO_DIR / "slide_scene4_v3.png"
    im.save(out_path)
    return str(out_path)


def make_scene5_overlay() -> str:
    """Scene 5: Grand Finale with Matching Broadcast Side Pillars."""
    im = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)

    f_title = get_font("title", 34)
    f_sub = get_font("bold", 20)
    f_accent = get_font("segoe", 18)

    # Left broadcast sidebar (x: 0..420)
    draw.rectangle([0, 0, 420, 1080], fill=(8, 14, 32, 252))
    draw.line([(420, 0), (420, 1080)], fill=(0, 212, 255, 230), width=4)

    draw.rounded_rectangle([25, 45, 395, 175], radius=16, fill=(16, 28, 68, 235), outline=(255, 221, 0), width=2)
    draw.text((45, 60), "★ ONN 4K PRO", font=f_title, fill=(255, 221, 0))
    draw.text((45, 110), "The Cable Killer", font=f_sub, fill=(255, 255, 255))
    draw.text((45, 140), "Upgrade Your Living Room", font=f_accent, fill=(0, 220, 255))

    draw.rounded_rectangle([25, 195, 395, 325], radius=16, fill=(16, 28, 68, 235), outline=(0, 255, 140), width=2)
    draw.text((45, 210), "★ SAVE $1,800/YEAR", font=f_title, fill=(0, 255, 140))
    draw.text((45, 260), "Stop Paying Monthly Bills", font=f_sub, fill=(255, 255, 255))
    draw.text((45, 290), "One Box • Zero Subscriptions", font=f_accent, fill=(0, 220, 255))

    draw.rounded_rectangle([25, 345, 395, 475], radius=16, fill=(16, 28, 68, 235), outline=(255, 140, 0), width=2)
    draw.text((45, 360), "★ 100% UNLOCKED", font=f_title, fill=(255, 140, 0))
    draw.text((45, 410), "Every Sport & Channel Live", font=f_sub, fill=(255, 255, 255))
    draw.text((45, 440), "No Restrictions or Blackouts", font=f_accent, fill=(0, 220, 255))

    # Right broadcast sidebar (x: 1500..1920)
    draw.rectangle([1500, 0, 1920, 1080], fill=(8, 14, 32, 252))
    draw.line([(1500, 0), (1500, 1080)], fill=(0, 212, 255, 230), width=4)

    draw.rounded_rectangle([1525, 45, 1895, 175], radius=16, fill=(16, 28, 68, 235), outline=(0, 212, 255), width=2)
    draw.text((1545, 60), "★ PLUG & PLAY", font=f_title, fill=(0, 212, 255))
    draw.text((1545, 110), "Connects in 60 Seconds", font=f_sub, fill=(255, 255, 255))
    draw.text((1545, 140), "Universal HDMI Compatibility", font=f_accent, fill=(0, 220, 255))

    draw.rounded_rectangle([1525, 195, 1895, 325], radius=16, fill=(16, 28, 68, 235), outline=(255, 221, 0), width=2)
    draw.text((1545, 210), "★ PRIVATE VPN", font=f_title, fill=(255, 221, 0))
    draw.text((1545, 260), "Military-Grade Encryption", font=f_sub, fill=(255, 255, 255))
    draw.text((1545, 290), "Stream in Total Safety", font=f_accent, fill=(0, 220, 255))

    draw.rounded_rectangle([1525, 345, 1895, 475], radius=16, fill=(16, 28, 68, 235), outline=(255, 40, 60), width=2)
    draw.text((1545, 360), "★ LIMITED BATCH", font=f_title, fill=(255, 40, 60))
    draw.text((1545, 410), "Units Ready to Ship Now", font=f_sub, fill=(255, 255, 255))
    draw.text((1545, 440), "Get Yours Before It Sells Out", font=f_accent, fill=(0, 220, 255))

    # Top Banner
    draw.rounded_rectangle([440, 25, 1480, 115], radius=24, fill=(11, 19, 43, 245), outline=(0, 212, 255, 200), width=3)
    f_head = get_font("title", 52)
    draw.text((475, 38), "★ ONN 4K PRO: TOTAL FREEDOM STREAMING ★", font=f_head, fill=(0, 220, 255))

    # Bottom Hero CTA Banner
    draw.rounded_rectangle([60, 720, 1860, 1030], radius=26, fill=(11, 19, 43, 250), outline=(255, 221, 0, 230), width=5)

    f_big = get_font("title", 76)
    draw.text((100, 740), "ELIMINATE YOUR CABLE BILL FOREVER!", font=f_big, fill=(255, 221, 0))

    f_sub2 = get_font("bold", 36)
    draw.text((105, 835), "1,000+ CHANNELS  •  5 LIBRARIES  •  VPN INCLUDED", font=f_sub2, fill=(255, 255, 255))

    # CTA Button Pill
    pill_box = [100, 895, 1820, 995]
    draw.rounded_rectangle(pill_box, radius=24, fill=(200, 10, 50, 245), outline=(255, 255, 255, 220), width=3)
    f_cta = get_font("title", 48)
    draw.text((560, 915), "UPGRADE TO THE ONN 4K PRO TODAY!", font=f_cta, fill=(255, 255, 255))

    out_path = REPO_DIR / "overlay_scene5_v3.png"
    im.save(out_path)
    return str(out_path)


def write_perfect_teleprompter_ass():
    """Write precision ASS subtitle file for the teleprompter guide video.

    Every line is positioned where it NEVER touches the PiP window, the presenter, or graphic cards.
    Font is crisp 20pt on 1920x1080 canvas.
    """
    ass_content = """[Script Info]
Title: Onn 4K Pro Commercial Teleprompter Guide
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Prompter,Arial,21,&H0000FFFF,&H000000FF,&H00000000,&HB0080E20,-1,0,0,0,100,100,0,0,3,3,0,5,30,30,20,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.50,0:00:09.50,Prompter,,0,0,0,,{\\pos(960,118)}Are you tired of paying hundreds of dollars every month for cable and streaming services? There is a better way.
Dialogue: 0,0:00:10.50,0:00:21.50,Prompter,,0,0,0,,{\\pos(1160,715)}Meet the Onn 4K Pro streaming box. It turns any television into an ultimate entertainment powerhouse.
Dialogue: 0,0:00:22.50,0:00:34.50,Prompter,,0,0,0,,{\\pos(960,140)}Get over one thousand live channels, live sports, pay-per-view events, and thousands of movies and TV shows.
Dialogue: 0,0:00:35.50,0:00:47.50,Prompter,,0,0,0,,{\\pos(960,140)}With five unlinked libraries and a built-in VPN, you get unlimited content with complete privacy and lightning speed.
Dialogue: 0,0:00:48.50,0:00:59.50,Prompter,,0,0,0,,{\\pos(960,140)}No contracts, no monthly fees, and no hassles. Eliminate your cable bill forever and upgrade to the Onn 4K Pro today!
"""
    with open(ASS_FILE, "w", encoding="utf-8") as f:
        f.write(ass_content)
    print(f"Wrote precision teleprompter ASS file: {ASS_FILE}")


def main():
    print("1. Generating graphic overlays & studio vignettes...")
    vignette_png = make_studio_vignette()
    s1_overlay = make_scene1_overlay()
    s2_bg = make_scene2_bg()
    s3_bg = make_scene3_bg()
    s4_bg = make_scene4_bg()
    s5_overlay = make_scene5_overlay()
    write_perfect_teleprompter_ass()

    master_audio = REPO_DIR / "master_audio.m4a"
    part1 = REPO_DIR / "part1_v3.mp4"
    part2 = REPO_DIR / "part2_v3.mp4"
    part3 = REPO_DIR / "part3_v3.mp4"
    part4 = REPO_DIR / "part4_v3.mp4"
    part5 = REPO_DIR / "part5_v3.mp4"

    # Presenter crop for Full Stage (Scene 1 & Scene 5):
    # Crop 720x720 centered at (300, 20), scale to 1080x1080, pad to 1920x1080 placed at x=420.
    # Overlay studio vignette, then overlay broadcast pillars + banners.
    # ZERO HeyGen watermarks will remain!
    full_stage_filter = (
        "[0:v]crop=720:720:300:20,scale=1080:1080[vcrop];"
        "[vcrop]pad=1920:1080:420:0:color=0x080E20[vpad];"
        "[vpad][1:v]overlay=0:0[vvig];"
        "[vvig][2:v]overlay=0:0[vout]"
    )

    # Clean crop for PiP (Presenter centered: crop 640x640 at x=340, y=30 to eliminate bookshelf watermarks)
    pip_filter = "crop=640:640:340:30,scale=340:340,pad=348:348:4:4:color=0x00D4FF"

    print("2. Encoding Scene 1 (The Hook: 0-10s) with Broadcast Stage...")
    cmd_p1 = [
        "ffmpeg", "-y",
        "-ss", "0", "-t", "10",
        "-i", str(AVATAR_VIDEO),
        "-i", vignette_png,
        "-i", s1_overlay,
        "-filter_complex", full_stage_filter,
        "-map", "[vout]",
        "-r", "30", "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
        str(part1),
    ]
    subprocess.run(cmd_p1, check=True)

    print("3. Encoding Scene 2 (The Solution with Dynamic TV Video: 10-22s, 12s)...")
    # TV video placed at x=80, y=145 (size 880x500)
    # Clean PiP presenter placed at x=70, y=660 (size 348x348)
    cmd_p2 = [
        "ffmpeg", "-y",
        "-loop", "1", "-t", "12", "-i", s2_bg,
        "-i", str(TV_SHOWCASE),
        "-ss", "0", "-t", "12", "-i", str(AVATAR_VIDEO),
        "-filter_complex",
        "[0:v]scale=1920:1080[bg];"
        "[1:v]scale=880:500[tvvid];"
        f"[2:v]{pip_filter}[pip];"
        "[bg][tvvid]overlay=80:145[bg_tv];"
        "[bg_tv][pip]overlay=70:660[vout]",
        "-map", "[vout]",
        "-r", "30", "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
        str(part2),
    ]
    subprocess.run(cmd_p2, check=True)

    print("4. Encoding Scene 3 (1000+ Channels & Sports: 22-35s, 13s)...")
    cmd_p3 = [
        "ffmpeg", "-y",
        "-loop", "1", "-t", "13", "-i", s3_bg,
        "-ss", "3", "-t", "13", "-i", str(AVATAR_VIDEO),
        "-filter_complex",
        "[0:v]scale=1920:1080[bg];"
        f"[1:v]{pip_filter}[pip];"
        "[bg][pip]overlay=786:700[vout]",
        "-map", "[vout]",
        "-r", "30", "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
        str(part3),
    ]
    subprocess.run(cmd_p3, check=True)

    print("5. Encoding Scene 4 (5 Libraries & VPN: 35-48s, 13s)...")
    cmd_p4 = [
        "ffmpeg", "-y",
        "-loop", "1", "-t", "13", "-i", s4_bg,
        "-ss", "8", "-t", "13", "-i", str(AVATAR_VIDEO),
        "-filter_complex",
        "[0:v]scale=1920:1080[bg];"
        f"[1:v]{pip_filter}[pip];"
        "[bg][pip]overlay=786:700[vout]",
        "-map", "[vout]",
        "-r", "30", "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
        str(part4),
    ]
    subprocess.run(cmd_p4, check=True)

    print("6. Encoding Scene 5 (Grand Finale CTA: 48-60s, 12s)...")
    cmd_p5 = [
        "ffmpeg", "-y",
        "-ss", "10", "-t", "12",
        "-i", str(AVATAR_VIDEO),
        "-i", vignette_png,
        "-i", s5_overlay,
        "-filter_complex", full_stage_filter,
        "-map", "[vout]",
        "-r", "30", "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
        str(part5),
    ]
    subprocess.run(cmd_p5, check=True)

    print("7. Stitching scenes...")
    concat_txt = REPO_DIR / "concat_v3.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for p in [part1, part2, part3, part4, part5]:
            f.write(f"file '{p.resolve().as_posix()}'\n")

    # Final Video with Reference Audio
    print("8. Rendering final master commercial...")
    cmd_final = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_txt),
        "-i", str(master_audio),
        "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-map", "0:v:0", "-map", "1:a:0",
        "-shortest",
        str(OUTPUT_VIDEO),
    ]
    subprocess.run(cmd_final, check=True)
    print(f"Rendered: {OUTPUT_VIDEO}")

    # Clean Video with Music Only
    bgm_wav = REPO_DIR / "bgm.wav"
    print("9. Rendering Clean (Music-Only) take...")
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

    # Teleprompter Guide Video with Non-Overlapping Precision ASS Subtitles
    ass_escaped = str(ASS_FILE).replace("\\", "/").replace(":", "\\:")
    print("10. Rendering Teleprompter Guide video with precision non-overlapping subtitles...")
    cmd_guide = [
        "ffmpeg", "-y",
        "-i", str(CLEAN_VIDEO),
        "-vf", f"ass='{ass_escaped}'",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "copy",
        str(GUIDE_VIDEO),
    ]
    subprocess.run(cmd_guide, check=True)
    print(f"Rendered: {GUIDE_VIDEO}")
    print("=== ALL VIDEO RENDERS SUCCESSFULLY COMPLETED! ===")


if __name__ == "__main__":
    main()
