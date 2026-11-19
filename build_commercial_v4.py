#!/usr/bin/env python3
"""Build the 60-second Onn 4K Pro Commercial Video (Version 4 - Official Logos & Motion Infographics).

Improvements in V4:
1. OFFICIAL LOGOS:
   - 8 Official TV Network logos: ABC, CBS, NBC, FOX, ESPN, CNN, HGTV, Discovery.
   - 6 Official Sports logos: NFL, NBA, MLB, NHL, UFC, NCAA.
2. DYNAMIC MOTION GRAPHIC INFOGRAPHICS:
   - Scene 3: Staggered spring entrance, periodic specular light-sweep shimmer across cards, pulsing live broadcast indicators.
   - Scene 4: Staggered holographic slide entrance for 5 Unlinked Libraries + Cyber VPN HUD security benefits, pulsing AES-256 encryption status.
3. WATERMARK-FREE & NON-OVERLAPPING TELEPROMPTER:
   - Preserves all broadcast pillars, TV bezel video in Scene 2, tight clean PiP framing, and 21pt ASS teleprompter guide.
"""

from __future__ import annotations

import math
import os
import subprocess
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

REPO_DIR = Path(r"C:\Users\tee\.gemini\antigravity-ide\scratch\hermes-agent")
LOGOS_DIR = REPO_DIR / "network_logos"
OUTPUT_DIR = Path(r"D:\AI-Avatars")
OUTPUT_VIDEO = OUTPUT_DIR / "Onn_4K_Pro_Commercial_1Min.mp4"
CLEAN_VIDEO = OUTPUT_DIR / "Onn_4K_Pro_Commercial_Clean_MusicOnly.mp4"
GUIDE_VIDEO = OUTPUT_DIR / "Onn_4K_Pro_Commercial_Teleprompter_Guide.mp4"
ASS_FILE = OUTPUT_DIR / "Onn_4K_Pro_Commercial_Voiceover.ass"
AVATAR_VIDEO = OUTPUT_DIR / "avatar_clean.mp4"
TV_SHOWCASE = REPO_DIR / "tv_showcase_12s.mp4"

FONTS = {
    "bebas": str(REPO_DIR / "fonts" / "BebasNeue.ttf"),
    "din": r"C:\Windows\Fonts\bahnschrift.ttf",
    "bold": r"C:\Windows\Fonts\segoeuib.ttf",
    "reg": r"C:\Windows\Fonts\segoeui.ttf",
    "title": r"C:\Windows\Fonts\impact.ttf",
}

def get_font(key: str, size: int) -> ImageFont.FreeTypeFont:
    path = FONTS.get(key, FONTS["bold"])
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

def ease_out_back(x: float) -> float:
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * math.pow(x - 1, 3) + c1 * math.pow(x - 1, 2)

def ease_out_cubic(x: float) -> float:
    return 1 - math.pow(1 - x, 3)

def draw_star(draw: ImageDraw.Draw, cx: float, cy: float, r_outer: float = 11, r_inner: float = 4.8, fill=(255, 221, 0)):
    points = []
    for i in range(10):
        r = r_outer if i % 2 == 0 else r_inner
        angle = math.pi / 2 + i * math.pi / 5
        x = cx + r * math.cos(angle)
        y = cy - r * math.sin(angle)
        points.append((x, y))
    draw.polygon(points, fill=fill)

def make_studio_vignette() -> str:
    """Generate subtle dark studio vignette to dim bookshelf background behind presenter."""
    w, h = 1920, 1080
    cx, cy = 960, 380
    Y, X = np.ogrid[:h, :w]
    dist = np.sqrt((X - cx) ** 2 + ((Y - cy) * 1.25) ** 2)

    r_inner, r_outer = 130, 330
    alpha = np.clip((dist - r_inner) / (r_outer - r_inner), 0, 1)

    img_arr = np.zeros((h, w, 4), dtype=np.uint8)
    img_arr[..., 0] = 6
    img_arr[..., 1] = 10
    img_arr[..., 2] = 24
    img_arr[..., 3] = (alpha * 255).astype(np.uint8)

    out_path = REPO_DIR / "studio_vignette.png"
    Image.fromarray(img_arr, mode="RGBA").save(out_path)
    return str(out_path)

def make_scene1_overlay() -> str:
    """Scene 1: Hook with Broadcast Studio Side Pillars."""
    im = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)

    draw.rectangle([0, 0, 420, 1080], fill=(8, 14, 32, 252))
    draw.line([(420, 0), (420, 1080)], fill=(0, 212, 255, 230), width=4)

    f_title = get_font("bebas", 34)
    f_sub = get_font("din", 20)
    f_accent = get_font("bold", 18)

    draw.rounded_rectangle([25, 45, 395, 175], radius=16, fill=(16, 28, 68, 235), outline=(255, 221, 0), width=2)
    draw_star(draw, 52, 78, 10, 4.5, fill=(255, 221, 0))
    draw.text((70, 60), "ONN 4K PRO", font=f_title, fill=(255, 221, 0))
    draw.text((45, 110), "The #1 Streaming Box of 2026", font=f_sub, fill=(255, 255, 255))
    draw.text((45, 140), "Zero Monthly Fees Forever", font=f_accent, fill=(0, 220, 255))

    draw.rounded_rectangle([25, 195, 395, 325], radius=16, fill=(16, 28, 68, 235), outline=(0, 255, 140), width=2)
    draw_star(draw, 52, 228, 10, 4.5, fill=(0, 255, 140))
    draw.text((70, 210), "1,000+ LIVE CHANNELS", font=f_title, fill=(0, 255, 140))
    draw.text((45, 260), "Cable, Sports, News, Movies", font=f_sub, fill=(255, 255, 255))
    draw.text((45, 290), "Global Networks Included", font=f_accent, fill=(0, 220, 255))

    draw.rounded_rectangle([25, 345, 395, 475], radius=16, fill=(16, 28, 68, 235), outline=(255, 140, 0), width=2)
    draw_star(draw, 52, 378, 10, 4.5, fill=(255, 140, 0))
    draw.text((70, 360), "ALL LIVE SPORTS", font=f_title, fill=(255, 140, 0))
    draw.text((45, 410), "NFL, NBA, NCAA, NHL, PPV", font=f_sub, fill=(255, 255, 255))
    draw.text((45, 440), "Every Game in Crystal 4K", font=f_accent, fill=(0, 220, 255))

    draw.rounded_rectangle([25, 495, 395, 625], radius=16, fill=(16, 28, 68, 235), outline=(0, 212, 255), width=2)
    draw_star(draw, 52, 528, 10, 4.5, fill=(0, 212, 255))
    draw.text((70, 510), "4K ULTRA HD HDR", font=f_title, fill=(0, 212, 255))
    draw.text((45, 560), "Dolby Audio Powered", font=f_sub, fill=(255, 255, 255))
    draw.text((45, 590), "Lightning Fast Playback", font=f_accent, fill=(0, 220, 255))

    draw.rectangle([1500, 0, 1920, 1080], fill=(8, 14, 32, 252))
    draw.line([(1500, 0), (1500, 1080)], fill=(0, 212, 255, 230), width=4)

    draw.rounded_rectangle([1525, 45, 1895, 175], radius=16, fill=(16, 28, 68, 235), outline=(0, 212, 255), width=2)
    draw_star(draw, 1552, 78, 10, 4.5, fill=(0, 212, 255))
    draw.text((1570, 60), "5 UNLINKED LIBRARIES", font=f_title, fill=(0, 212, 255))
    draw.text((1545, 110), "Pre-loaded & Ready to Stream", font=f_sub, fill=(255, 255, 255))
    draw.text((1545, 140), "10,000+ On-Demand Movies", font=f_accent, fill=(0, 220, 255))

    draw.rounded_rectangle([1525, 195, 1895, 325], radius=16, fill=(16, 28, 68, 235), outline=(255, 221, 0), width=2)
    draw_star(draw, 1552, 228, 10, 4.5, fill=(255, 221, 0))
    draw.text((1570, 210), "BUILT-IN VPN PRIVACY", font=f_title, fill=(255, 221, 0))
    draw.text((1545, 260), "100% Anonymous & Secure", font=f_sub, fill=(255, 255, 255))
    draw.text((1545, 290), "Zero Throttling or Tracking", font=f_accent, fill=(0, 220, 255))

    draw.rounded_rectangle([1525, 345, 1895, 475], radius=16, fill=(16, 28, 68, 235), outline=(255, 40, 60), width=2)
    draw_star(draw, 1552, 378, 10, 4.5, fill=(255, 40, 60))
    draw.text((1570, 360), "ZERO CONTRACTS", font=f_title, fill=(255, 40, 60))
    draw.text((1545, 410), "Plug & Play on Any TV", font=f_sub, fill=(255, 255, 255))
    draw.text((1545, 440), "Eliminate Bills Forever", font=f_accent, fill=(0, 220, 255))

    draw.rounded_rectangle([1525, 495, 1895, 625], radius=16, fill=(16, 28, 68, 235), outline=(0, 255, 140), width=2)
    draw_star(draw, 1552, 528, 10, 4.5, fill=(0, 255, 140))
    draw.text((1570, 510), "PLUG & PLAY", font=f_title, fill=(0, 255, 140))
    draw.text((1545, 560), "Setup in Under 2 Minutes", font=f_sub, fill=(255, 255, 255))
    draw.text((1545, 590), "Works on Any Television", font=f_accent, fill=(0, 220, 255))

    pill_w, pill_h = 960, 58
    px, py = (1920 - pill_w) // 2, 22
    draw.rounded_rectangle([px, py, px + pill_w, py + pill_h], radius=29, fill=(220, 20, 60, 240), outline=(255, 255, 255, 200), width=3)
    f_warn = get_font("din", 28)
    draw_star(draw, px + 50, py + 29, 9, 4, fill=(255, 255, 255))
    draw.text((px + 72, py + 12), "ATTENTION CABLE & SATELLITE SUBSCRIBERS", font=f_warn, fill=(255, 255, 255))
    draw_star(draw, px + pill_w - 50, py + 29, 9, 4, fill=(255, 255, 255))

    bg_box = [60, 770, 1860, 1030]
    draw.rounded_rectangle(bg_box, radius=24, fill=(11, 19, 43, 250), outline=(0, 212, 255, 200), width=4)
    f_big = get_font("bebas", 80)
    draw.text((100, 785), "ELIMINATE YOUR CABLE BILL!", font=f_big, fill=(255, 221, 0))
    f_sub2 = get_font("din", 38)
    draw.text((104, 885), "CUT THE CORD FOR GOOD • OVER 1,000+ LIVE CHANNELS", font=f_sub2, fill=(255, 255, 255))
    f_pill2 = get_font("bold", 26)
    draw.text((104, 955), "ZERO MONTHLY FEES  •  NO CONTRACTS  •  PLUG & PLAY", font=f_pill2, fill=(0, 220, 255))

    cables_path = REPO_DIR / "crop_cables.png"
    if cables_path.exists():
        cb = Image.open(cables_path).convert("RGBA")
        draw.rounded_rectangle([1340, 790, 1830, 1010], radius=16, fill=(16, 28, 64, 245), outline=(0, 212, 255, 180), width=2)
        f_cut = get_font("bebas", 26)
        draw.text((1365, 800), "CUT THE CORDS & SAVE $2,000+/YR", font=f_cut, fill=(255, 221, 0))
        cb_clean = cb.crop((0, 125, cb.width, cb.height)).resize((460, 140), Image.Resampling.LANCZOS)
        im.alpha_composite(cb_clean, (1355, 850))

    out_path = REPO_DIR / "overlay_scene1_v4.png"
    im.save(out_path)
    return str(out_path)

    out_path = REPO_DIR / "overlay_scene1_v4.png"
    im.save(out_path)
    return str(out_path)

def make_scene2_bg() -> str:
    """Scene 2: Solution with TV Bezel."""
    im = Image.new("RGBA", (1920, 1080), (10, 16, 38, 255))
    draw = ImageDraw.Draw(im)

    draw.rounded_rectangle([60, 20, 1860, 115], radius=20, fill=(15, 25, 60, 240), outline=(0, 212, 255, 200), width=3)
    f_head = get_font("bebas", 58)
    draw.text((100, 30), "MEET THE ONN 4K PRO STREAMING POWERHOUSE", font=f_head, fill=(255, 221, 0))

    # TV Bezel frame at (70, 135) to (970, 655)
    draw.rounded_rectangle([70, 135, 970, 655], radius=16, fill=(0, 0, 0, 255), outline=(0, 212, 255, 220), width=5)

    # Right Column: Specifications & Feature Badges
    draw.rounded_rectangle([1000, 135, 1860, 1020], radius=20, fill=(15, 25, 60, 240), outline=(0, 212, 255, 180), width=3)

    box_img_path = REPO_DIR / "crop_box.png"
    if box_img_path.exists():
        box_im = Image.open(box_img_path).convert("RGBA")
        box_im = box_im.resize((380, 230), Image.Resampling.LANCZOS)
        im.alpha_composite(box_im, (1240, 155))

    f_card_t = get_font("bebas", 34)
    f_card_d = get_font("bold", 20)

    cards = [
        ("4K ULTRA HD + HDR10+", "Cinematic picture clarity with vivid contrast", (255, 221, 0), 400),
        ("DOLBY AUDIO BUILT-IN", "Theater-quality surround sound audio", (0, 212, 255), 515),
        ("32GB EXPANDABLE STORAGE", "Pre-loaded with premium streaming apps", (0, 255, 140), 630),
        ("ULTRA-FAST WI-FI 6", "Buffer-free streaming with zero lag or delay", (255, 140, 0), 745),
        ("GOOGLE TV + VOICE REMOTE", "Hands-free Google Assistant smart control", (200, 100, 255), 860),
    ]

    for title, desc, col, y_pos in cards:
        draw.rounded_rectangle([1030, y_pos, 1830, y_pos + 95], radius=14, fill=(18, 32, 75, 235), outline=col, width=2)
        draw_star(draw, 1058, y_pos + 32, 10, 4.5, fill=col)
        draw.text((1078, y_pos + 14), title, font=f_card_t, fill=col)
        draw.text((1055, y_pos + 56), desc, font=f_card_d, fill=(235, 245, 255))

    out_path = REPO_DIR / "slide_scene2_v4.png"
    im.save(out_path)
    return str(out_path)

def make_scene5_overlay() -> str:
    """Scene 5: Grand Finale with Matching Broadcast Side Pillars."""
    im = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)

    f_title = get_font("bebas", 34)
    f_sub = get_font("din", 20)
    f_accent = get_font("bold", 18)

    draw.rectangle([0, 0, 420, 1080], fill=(8, 14, 32, 252))
    draw.line([(420, 0), (420, 1080)], fill=(0, 212, 255, 230), width=4)

    draw.rounded_rectangle([25, 45, 395, 175], radius=16, fill=(16, 28, 68, 235), outline=(255, 221, 0), width=2)
    draw_star(draw, 52, 78, 10, 4.5, fill=(255, 221, 0))
    draw.text((70, 60), "ONN 4K PRO", font=f_title, fill=(255, 221, 0))
    draw.text((45, 110), "The Cable Killer", font=f_sub, fill=(255, 255, 255))
    draw.text((45, 140), "Upgrade Your Living Room", font=f_accent, fill=(0, 220, 255))

    draw.rounded_rectangle([25, 195, 395, 325], radius=16, fill=(16, 28, 68, 235), outline=(0, 255, 140), width=2)
    draw_star(draw, 52, 228, 10, 4.5, fill=(0, 255, 140))
    draw.text((70, 210), "SAVE $1,800/YEAR", font=f_title, fill=(0, 255, 140))
    draw.text((45, 260), "Stop Paying Monthly Bills", font=f_sub, fill=(255, 255, 255))
    draw.text((45, 290), "One Box • Zero Subscriptions", font=f_accent, fill=(0, 220, 255))

    draw.rounded_rectangle([25, 345, 395, 475], radius=16, fill=(16, 28, 68, 235), outline=(255, 140, 0), width=2)
    draw_star(draw, 52, 378, 10, 4.5, fill=(255, 140, 0))
    draw.text((70, 360), "100% UNLOCKED", font=f_title, fill=(255, 140, 0))
    draw.text((45, 410), "Every Sport & Channel Live", font=f_sub, fill=(255, 255, 255))
    draw.text((45, 440), "No Restrictions or Blackouts", font=f_accent, fill=(0, 220, 255))

    draw.rectangle([1500, 0, 1920, 1080], fill=(8, 14, 32, 252))
    draw.line([(1500, 0), (1500, 1080)], fill=(0, 212, 255, 230), width=4)

    draw.rounded_rectangle([1525, 45, 1895, 175], radius=16, fill=(16, 28, 68, 235), outline=(0, 212, 255), width=2)
    draw_star(draw, 1552, 78, 10, 4.5, fill=(0, 212, 255))
    draw.text((1570, 60), "PLUG & PLAY", font=f_title, fill=(0, 212, 255))
    draw.text((1545, 110), "Connects in 60 Seconds", font=f_sub, fill=(255, 255, 255))
    draw.text((1545, 140), "Universal HDMI Compatibility", font=f_accent, fill=(0, 220, 255))

    draw.rounded_rectangle([1525, 195, 1895, 325], radius=16, fill=(16, 28, 68, 235), outline=(255, 221, 0), width=2)
    draw_star(draw, 1552, 228, 10, 4.5, fill=(255, 221, 0))
    draw.text((1570, 210), "PRIVATE VPN", font=f_title, fill=(255, 221, 0))
    draw.text((1545, 260), "Military-Grade Encryption", font=f_sub, fill=(255, 255, 255))
    draw.text((1545, 290), "Stream in Total Safety", font=f_accent, fill=(0, 220, 255))

    draw.rounded_rectangle([1525, 345, 1895, 475], radius=16, fill=(16, 28, 68, 235), outline=(255, 40, 60), width=2)
    draw_star(draw, 1552, 378, 10, 4.5, fill=(255, 40, 60))
    draw.text((1570, 360), "LIMITED BATCH", font=f_title, fill=(255, 40, 60))
    draw.text((1545, 410), "Units Ready to Ship Now", font=f_sub, fill=(255, 255, 255))
    draw.text((1545, 440), "Get Yours Before It Sells Out", font=f_accent, fill=(0, 220, 255))

    draw.rounded_rectangle([440, 25, 1480, 115], radius=24, fill=(11, 19, 43, 245), outline=(0, 212, 255, 200), width=3)
    f_head = get_font("bebas", 52)
    draw_star(draw, 490, 70, 14, 6, fill=(0, 220, 255))
    draw.text((520, 38), "ONN 4K PRO: TOTAL FREEDOM STREAMING", font=f_head, fill=(0, 220, 255))
    draw_star(draw, 1430, 70, 14, 6, fill=(0, 220, 255))

    draw.rounded_rectangle([60, 720, 1860, 1030], radius=26, fill=(11, 19, 43, 250), outline=(255, 221, 0, 230), width=5)
    f_big = get_font("bebas", 76)
    draw.text((100, 740), "ELIMINATE YOUR CABLE BILL FOREVER!", font=f_big, fill=(255, 221, 0))

    f_sub2 = get_font("din", 36)
    draw.text((105, 835), "1,000+ CHANNELS  •  5 LIBRARIES  •  VPN INCLUDED", font=f_sub2, fill=(255, 255, 255))

    pill_box = [100, 895, 1820, 995]
    draw.rounded_rectangle(pill_box, radius=24, fill=(200, 10, 50, 245), outline=(255, 255, 255, 220), width=3)
    f_cta = get_font("bebas", 48)
    draw.text((560, 915), "UPGRADE TO THE ONN 4K PRO TODAY!", font=f_cta, fill=(255, 255, 255))

    out_path = REPO_DIR / "overlay_scene5_v4.png"
    im.save(out_path)
    return str(out_path)

def generate_animated_scene3(output_mp4: Path, total_frames: int = 390, fps: int = 30):
    """Render animated Scene 3 with official logos and motion graphics."""
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo", "-s", "1920x1080", "-pix_fmt", "rgba",
        "-r", str(fps), "-i", "-",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
        str(output_mp4)
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    tv_logo_imgs = {}
    tv_logos = [
        ("abc.png", "ABC"), ("cbs.png", "CBS"), ("nbc.png", "NBC"), ("fox.png", "FOX"),
        ("espn.png", "ESPN"), ("cnn.png", "CNN"), ("hgtv.png", "HGTV"), ("discovery.png", "DISCOVERY"),
    ]
    for fn, _ in tv_logos:
        p = LOGOS_DIR / fn
        if p.exists():
            im = Image.open(p).convert("RGBA")
            im.thumbnail((154, 66), Image.Resampling.LANCZOS)
            tv_logo_imgs[fn] = im

    sports_logo_imgs = {}
    sports_logos = [
        ("nfl.png", "NFL"), ("nba.png", "NBA"), ("mlb.png", "MLB"),
        ("nhl.png", "NHL"), ("ufc.png", "UFC"), ("ncaa.png", "NCAA"),
    ]
    for fn, _ in sports_logos:
        p = LOGOS_DIR / fn
        if p.exists():
            im = Image.open(p).convert("RGBA")
            im.thumbnail((215, 66), Image.Resampling.LANCZOS)
            sports_logo_imgs[fn] = im

    f_head = get_font("bebas", 58)
    f_tag = get_font("din", 22)
    f_col_title = get_font("bebas", 28)
    f_sub = get_font("din", 19)
    f_item_title = get_font("din", 21)
    f_item_desc = get_font("reg", 17)
    f_bot_title = get_font("bebas", 48)
    f_bot_sub = get_font("bebas", 38)
    w, h = 1920, 1080

    for f_idx in range(total_frames):
        t = f_idx / fps
        im = Image.new("RGBA", (w, h), (8, 14, 30, 255))
        draw = ImageDraw.Draw(im)

        # Header
        h_prog = min(1.0, f_idx / 20.0)
        h_y_offset = int((1.0 - ease_out_cubic(h_prog)) * -60)
        draw.rounded_rectangle([60, 20 + h_y_offset, 1860, 120 + h_y_offset], radius=20, fill=(13, 23, 52, 245), outline=(0, 212, 255, 220), width=3)
        draw.text((100, 32 + h_y_offset), "OVER 1,000+ LIVE CHANNELS & ALL LIVE SPORTS", font=f_head, fill=(255, 221, 0))

        pulse_alpha = int(180 + 75 * math.sin(t * 4.0))
        draw.rounded_rectangle([1510, 40 + h_y_offset, 1830, 100 + h_y_offset], radius=15, fill=(16, 28, 64, 255), outline=(0, 212, 255, 255), width=2)
        draw.text((1535, 54 + h_y_offset), "100% UNLOCKED BROADCAST", font=f_tag, fill=(0, 220, 255))

        # Left Column Panel
        p_left_prog = min(1.0, max(0.0, (f_idx - 5) / 25.0))
        p_left_x_offset = int((1.0 - ease_out_cubic(p_left_prog)) * -100)
        panel_alpha = int(240 * p_left_prog)

        if p_left_prog > 0:
            lx1, ly1, lx2, ly2 = 60 + p_left_x_offset, 145, 930 + p_left_x_offset, 685
            draw.rounded_rectangle([lx1, ly1, lx2, ly2], radius=22, fill=(14, 25, 55, panel_alpha), outline=(0, 212, 255, int(180 * p_left_prog)), width=3)
            
            draw.rounded_rectangle([90 + p_left_x_offset, 165, 340 + p_left_x_offset, 210], radius=12, fill=(0, 212, 255, 230))
            draw.text((108 + p_left_x_offset, 172), "LIVE TV NETWORKS", font=f_col_title, fill=(8, 14, 30))
            draw.text((360 + p_left_x_offset, 178), "ABC, CBS, NBC, FOX, ESPN, CNN & MORE", font=f_sub, fill=(200, 225, 255))

            card_w, card_h = 190, 88
            grid_start_x = 90 + p_left_x_offset
            grid_start_y = 230
            gap_x = 22
            gap_y = 18

            shimmer_cycle = (t % 3.0) / 3.0
            shimmer_active_col = shimmer_cycle * 6.0 - 1.0

            for idx, (logo_fn, name) in enumerate(tv_logos):
                col = idx % 4
                row = idx // 4
                card_delay = 10 + idx * 3
                c_prog = min(1.0, max(0.0, (f_idx - card_delay) / 16.0))
                if c_prog <= 0:
                    continue

                cx = grid_start_x + col * (card_w + gap_x)
                cy = grid_start_y + row * (card_h + gap_y)

                dist = abs(col - shimmer_active_col)
                if dist < 0.8:
                    card_outline = (255, 255, 255, 255)
                    card_fill = (255, 255, 255, 255)
                    border_w = 3
                else:
                    card_outline = (0, 212, 255, 160)
                    card_fill = (245, 250, 255, 250)
                    border_w = 2

                draw.rounded_rectangle([cx, cy, cx + card_w, cy + card_h], radius=14, fill=card_fill, outline=card_outline, width=border_w)
                
                if logo_fn in tv_logo_imgs:
                    l_img = tv_logo_imgs[logo_fn]
                    px = cx + (card_w - l_img.width) // 2
                    py = cy + (card_h - l_img.height) // 2
                    im.alpha_composite(l_img, (px, py))

            draw.rounded_rectangle([90 + p_left_x_offset, 440, 900 + p_left_x_offset, 510], radius=12, fill=(20, 34, 72, 180), outline=(0, 212, 255, 80), width=1)
            draw.ellipse([110 + p_left_x_offset, 460, 126 + p_left_x_offset, 476], fill=(0, 255, 180))
            draw.text((140 + p_left_x_offset, 448), "OVER 1,000 CHANNELS WORLDWIDE", font=f_item_title, fill=(255, 255, 255))
            draw.text((140 + p_left_x_offset, 478), "News, Entertainment, Family, Kids, Documentaries & Local Broadcasts", font=f_item_desc, fill=(185, 210, 245))

            draw.rounded_rectangle([90 + p_left_x_offset, 520, 900 + p_left_x_offset, 590], radius=12, fill=(20, 34, 72, 180), outline=(0, 212, 255, 80), width=1)
            draw.ellipse([110 + p_left_x_offset, 540, 126 + p_left_x_offset, 556], fill=(0, 212, 255))
            draw.text((140 + p_left_x_offset, 528), "CRYSTAL 4K ULTRA HD & FULL HD STREAMS", font=f_item_title, fill=(255, 255, 255))
            draw.text((140 + p_left_x_offset, 558), "Dolby Digital surround sound with lightning-fast instant channel zapping", font=f_item_desc, fill=(185, 210, 245))

            draw.rounded_rectangle([90 + p_left_x_offset, 600, 900 + p_left_x_offset, 670], radius=12, fill=(20, 34, 72, 180), outline=(0, 212, 255, 80), width=1)
            draw.ellipse([110 + p_left_x_offset, 620, 126 + p_left_x_offset, 636], fill=(255, 221, 0))
            draw.text((140 + p_left_x_offset, 608), "ZERO MONTHLY FEES • NO CONTRACTS EVER", font=f_item_title, fill=(255, 221, 0))
            draw.text((140 + p_left_x_offset, 638), "Plug & play on any TV — keep your channels active forever without paying bills", font=f_item_desc, fill=(185, 210, 245))

        # Right Column Panel: All Live Sports
        p_right_prog = min(1.0, max(0.0, (f_idx - 5) / 25.0))
        p_right_x_offset = int((1.0 - ease_out_cubic(p_right_prog)) * 100)

        if p_right_prog > 0:
            rx1, ry1, rx2, ry2 = 990 + p_right_x_offset, 145, 1860 + p_right_x_offset, 685
            draw.rounded_rectangle([rx1, ry1, rx2, ry2], radius=22, fill=(14, 25, 55, panel_alpha), outline=(255, 140, 0, int(180 * p_right_prog)), width=3)
            
            draw.rounded_rectangle([1020 + p_right_x_offset, 165, 1290 + p_right_x_offset, 210], radius=12, fill=(255, 140, 0, 230))
            draw.text((1038 + p_right_x_offset, 172), "ALL LIVE SPORTS & PPV", font=f_col_title, fill=(8, 14, 30))
            draw.text((1310 + p_right_x_offset, 178), "EVERY GAME • EVERY LEAGUE • ZERO PAYWALLS", font=f_sub, fill=(255, 220, 180))

            s_card_w, s_card_h = 255, 88
            s_start_x = 1020 + p_right_x_offset
            s_start_y = 230
            s_gap_x = 22
            s_gap_y = 18

            for idx, (logo_fn, name) in enumerate(sports_logos):
                col = idx % 3
                row = idx // 3
                card_delay = 12 + idx * 4
                c_prog = min(1.0, max(0.0, (f_idx - card_delay) / 16.0))
                if c_prog <= 0:
                    continue

                cx = s_start_x + col * (s_card_w + s_gap_x)
                cy = s_start_y + row * (s_card_h + s_gap_y)

                dist = abs(col - shimmer_active_col)
                if dist < 0.8:
                    card_outline = (255, 255, 255, 255)
                    card_fill = (255, 250, 250, 255)
                    border_w = 3
                else:
                    card_outline = (255, 140, 0, 160)
                    card_fill = (245, 250, 255, 250)
                    border_w = 2

                draw.rounded_rectangle([cx, cy, cx + s_card_w, cy + s_card_h], radius=14, fill=card_fill, outline=card_outline, width=border_w)
                
                if logo_fn in sports_logo_imgs:
                    l_img = sports_logo_imgs[logo_fn]
                    px = cx + (s_card_w - l_img.width) // 2
                    py = cy + (s_card_h - l_img.height) // 2
                    im.alpha_composite(l_img, (px, py))

            draw.rounded_rectangle([1020 + p_right_x_offset, 440, 1830 + p_right_x_offset, 510], radius=12, fill=(20, 34, 72, 180), outline=(255, 140, 0, 80), width=1)
            draw.ellipse([1040 + p_right_x_offset, 460, 1056 + p_right_x_offset, 476], fill=(255, 140, 0))
            draw.text((1070 + p_right_x_offset, 448), "NFL SUNDAY TICKET & REDZONE PASS", font=f_item_title, fill=(255, 255, 255))
            draw.text((1070 + p_right_x_offset, 478), "Catch every out-of-market touchdown live without high-priced satellite packages", font=f_item_desc, fill=(185, 210, 245))

            draw.rounded_rectangle([1020 + p_right_x_offset, 520, 1830 + p_right_x_offset, 590], radius=12, fill=(20, 34, 72, 180), outline=(255, 140, 0, 80), width=1)
            draw.ellipse([1040 + p_right_x_offset, 540, 1056 + p_right_x_offset, 556], fill=(0, 212, 255))
            draw.text((1070 + p_right_x_offset, 528), "NBA LEAGUE PASS, MLB & NHL CENTER ICE", font=f_item_title, fill=(255, 255, 255))
            draw.text((1070 + p_right_x_offset, 558), "Full regular season and playoff access for basketball, baseball, hockey & college sports", font=f_item_desc, fill=(185, 210, 245))

            draw.rounded_rectangle([1020 + p_right_x_offset, 600, 1830 + p_right_x_offset, 670], radius=12, fill=(20, 34, 72, 180), outline=(255, 140, 0, 80), width=1)
            draw.ellipse([1040 + p_right_x_offset, 620, 1056 + p_right_x_offset, 636], fill=(255, 40, 60))
            draw.text((1070 + p_right_x_offset, 608), "CHAMPIONSHIP UFC & BOXING PAY-PER-VIEWS", font=f_item_title, fill=(255, 221, 0))
            draw.text((1070 + p_right_x_offset, 638), "Stream major championship PPV title fights included with zero extra fees", font=f_item_desc, fill=(185, 210, 245))

        # Bottom Callout Cards
        bot_prog = min(1.0, max(0.0, (f_idx - 20) / 20.0))
        bot_y_offset = int((1.0 - ease_out_cubic(bot_prog)) * 120)

        if bot_prog > 0:
            draw.rounded_rectangle([60, 770 + bot_y_offset, 730, 970 + bot_y_offset], radius=20, fill=(220, 20, 60, 235), outline=(255, 255, 255, 220), width=3)
            draw.text((95, 800 + bot_y_offset), "NO CONTRACTS", font=f_bot_title, fill=(255, 255, 255))
            draw.text((95, 875 + bot_y_offset), "NO MONTHLY FEES", font=f_bot_sub, fill=(255, 221, 0))

            draw.rounded_rectangle([1190, 770 + bot_y_offset, 1860, 970 + bot_y_offset], radius=20, fill=(14, 25, 55, 240), outline=(0, 255, 180, 220), width=3)
            draw.text((1225, 800 + bot_y_offset), "ZERO PAYWALLS", font=f_bot_title, fill=(0, 255, 180))
            draw.text((1225, 875 + bot_y_offset), "100% UNLOCKED ENTERTAINMENT", font=f_bot_sub, fill=(255, 221, 0))

        proc.stdin.write(im.tobytes())

    proc.stdin.close()
    proc.wait()
    print(f"Generated animated scene 3 video: {output_mp4}")

def generate_animated_scene4(output_mp4: Path, total_frames: int = 390, fps: int = 30):
    """Render animated Scene 4: 5 Unlinked Libraries + Built-In Secure VPN."""
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo", "-s", "1920x1080", "-pix_fmt", "rgba",
        "-r", str(fps), "-i", "-",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
        str(output_mp4)
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    f_head = get_font("bebas", 58)
    f_tag = get_font("din", 22)
    f_col_title = get_font("bebas", 28)
    f_sub = get_font("din", 19)
    f_badge = get_font("bebas", 22)
    f_name = get_font("din", 22)
    f_desc = get_font("reg", 16)
    f_bot_title = get_font("bebas", 48)
    f_bot_sub = get_font("bebas", 38)
    w, h = 1920, 1080

    libraries = [
        ("LIB 01", "CINEMA VAULT", "10,000+ Blockbuster Releases, 4K Box Sets & Complete Series", (0, 212, 255)),
        ("LIB 02", "LIVE SPORTS CENTER", "NFL Sunday Ticket, NBA League Pass, MLB, NHL & PPV Fights", (255, 140, 0)),
        ("LIB 03", "CUSTOM APP UNIVERSE", "Over 100+ Pre-Installed Streaming Apps & Power User Tools", (0, 255, 180)),
        ("LIB 04", "ON-DEMAND TV HUB", "Full TV Series Binge Vault, Reality Shows & Kids Networks", (180, 100, 255)),
        ("LIB 05", "4K ULTRA STREAMING", "Dolby Atmos Surround Audio & Pure 4K Crystal HDR Playback", (255, 221, 0)),
    ]

    vpn_features = [
        ("AES-256", "MILITARY-GRADE 256-BIT ENCRYPTION", "Bank-level AES encryption shields all your streaming activity", (0, 255, 140)),
        ("SPEED", "ZERO ISP THROTTLING & BUFFERING", "Bypass Internet provider speed limits for lightning 4K playback", (0, 212, 255)),
        ("PRIVACY", "STRICT ZERO-LOG PRIVACY POLICY", "Total anonymity with zero tracking, logging, or activity records", (255, 221, 0)),
        ("SERVERS", "HIGH-SPEED DEDICATED SERVERS", "Optimized global bandwidth for instant buffer-free streaming", (255, 140, 0)),
        ("AUTO", "INSTANT ONE-CLICK PROTECTION", "Automatic connection built into the box — zero setup needed", (0, 255, 180)),
    ]

    card_start_y = 225
    c_h = 82
    c_gap = 10

    for f_idx in range(total_frames):
        t = f_idx / fps
        im = Image.new("RGBA", (w, h), (8, 14, 30, 255))
        draw = ImageDraw.Draw(im)

        # Header
        h_prog = min(1.0, f_idx / 20.0)
        h_y_offset = int((1.0 - ease_out_cubic(h_prog)) * -60)
        draw.rounded_rectangle([60, 20 + h_y_offset, 1860, 120 + h_y_offset], radius=20, fill=(13, 23, 52, 245), outline=(0, 255, 180, 220), width=3)
        draw.text((100, 32 + h_y_offset), "5 UNLINKED LIBRARIES + BUILT-IN SECURE VPN", font=f_head, fill=(0, 255, 180))

        pulse_alpha = int(180 + 75 * math.sin(t * 4.0))
        draw.rounded_rectangle([1480, 40 + h_y_offset, 1830, 100 + h_y_offset], radius=15, fill=(12, 32, 54, 255), outline=(0, 255, 180, 255), width=2)
        draw.text((1505, 54 + h_y_offset), "ENTERTAINMENT ECOSYSTEM", font=f_tag, fill=(0, 255, 180))

        # Left Column: 5 Libraries
        p_left_prog = min(1.0, max(0.0, (f_idx - 5) / 25.0))
        p_left_x_offset = int((1.0 - ease_out_cubic(p_left_prog)) * -100)
        panel_alpha = int(240 * p_left_prog)

        if p_left_prog > 0:
            draw.rounded_rectangle([60 + p_left_x_offset, 145, 930 + p_left_x_offset, 685], radius=22, fill=(14, 25, 55, panel_alpha), outline=(0, 212, 255, int(180 * p_left_prog)), width=3)
            draw.rounded_rectangle([90 + p_left_x_offset, 165, 360 + p_left_x_offset, 210], radius=12, fill=(0, 212, 255, 230))
            draw.text((108 + p_left_x_offset, 172), "5 UNLINKED LIBRARIES", font=f_col_title, fill=(8, 14, 30))
            draw.text((380 + p_left_x_offset, 178), "PRE-CONFIGURED & INSTANTLY ACCESSIBLE", font=f_sub, fill=(200, 225, 255))

            # Staggered Library Cards
            shimmer_cycle = (t % 2.5) / 2.5
            shimmer_active_idx = int(shimmer_cycle * 5.0)

            for idx, (badge, name, desc, accent) in enumerate(libraries):
                c_delay = 10 + idx * 4
                c_prog = min(1.0, max(0.0, (f_idx - c_delay) / 16.0))
                if c_prog <= 0:
                    continue

                c_x_off = int((1.0 - ease_out_cubic(c_prog)) * -120)
                cy = card_start_y + idx * (c_h + c_gap)
                
                # Active highlight glow
                if idx == shimmer_active_idx:
                    card_outline = (255, 255, 255, 255)
                    card_fill = (25, 42, 90, 250)
                    b_w = 3
                else:
                    card_outline = accent
                    card_fill = (18, 30, 64, 220)
                    b_w = 2

                draw.rounded_rectangle([90 + p_left_x_offset + c_x_off, cy, 900 + p_left_x_offset + c_x_off, cy + c_h], radius=14, fill=card_fill, outline=card_outline, width=b_w)
                
                # Badge pill
                draw.rounded_rectangle([105 + p_left_x_offset + c_x_off, cy + 18, 180 + p_left_x_offset + c_x_off, cy + c_h - 18], radius=8, fill=accent)
                draw.text((114 + p_left_x_offset + c_x_off, cy + 26), badge, font=f_badge, fill=(8, 14, 30))
                
                draw.text((195 + p_left_x_offset + c_x_off, cy + 14), name, font=f_name, fill=(255, 255, 255))
                draw.text((195 + p_left_x_offset + c_x_off, cy + 44), desc, font=f_desc, fill=(190, 215, 245))

        # Right Column: Built-In VPN
        p_right_prog = min(1.0, max(0.0, (f_idx - 5) / 25.0))
        p_right_x_offset = int((1.0 - ease_out_cubic(p_right_prog)) * 100)

        if p_right_prog > 0:
            draw.rounded_rectangle([990 + p_right_x_offset, 145, 1860 + p_right_x_offset, 685], radius=22, fill=(14, 25, 55, panel_alpha), outline=(0, 255, 140, int(180 * p_right_prog)), width=3)
            draw.rounded_rectangle([1020 + p_right_x_offset, 165, 1310 + p_right_x_offset, 210], radius=12, fill=(0, 255, 140, 230))
            draw.text((1038 + p_right_x_offset, 172), "BUILT-IN SECURE VPN", font=f_col_title, fill=(8, 14, 30))
            draw.text((1330 + p_right_x_offset, 178), "100% PRIVATE • ANONYMOUS • NO LOGS", font=f_sub, fill=(200, 255, 220))

            for idx, (badge, name, desc, accent) in enumerate(vpn_features):
                c_delay = 12 + idx * 4
                c_prog = min(1.0, max(0.0, (f_idx - c_delay) / 16.0))
                if c_prog <= 0:
                    continue

                c_x_off = int((1.0 - ease_out_cubic(c_prog)) * 120)
                cy = card_start_y + idx * (c_h + c_gap)

                if idx == shimmer_active_idx:
                    card_outline = (255, 255, 255, 255)
                    card_fill = (25, 42, 90, 250)
                    b_w = 3
                else:
                    card_outline = accent
                    card_fill = (18, 30, 64, 220)
                    b_w = 2

                draw.rounded_rectangle([1020 + p_right_x_offset + c_x_off, cy, 1830 + p_right_x_offset + c_x_off, cy + c_h], radius=14, fill=card_fill, outline=card_outline, width=b_w)
                
                draw.rounded_rectangle([1035 + p_right_x_offset + c_x_off, cy + 18, 1125 + p_right_x_offset + c_x_off, cy + c_h - 18], radius=8, fill=accent)
                draw.text((1045 + p_right_x_offset + c_x_off, cy + 26), badge, font=f_badge, fill=(8, 14, 30))
                
                draw.text((1145 + p_right_x_offset + c_x_off, cy + 14), name, font=f_name, fill=(255, 255, 255))
                draw.text((1145 + p_right_x_offset + c_x_off, cy + 44), desc, font=f_desc, fill=(190, 215, 245))

        # Bottom Callouts
        bot_prog = min(1.0, max(0.0, (f_idx - 20) / 20.0))
        bot_y_offset = int((1.0 - ease_out_cubic(bot_prog)) * 120)

        if bot_prog > 0:
            draw.rounded_rectangle([60, 770 + bot_y_offset, 730, 970 + bot_y_offset], radius=20, fill=(0, 140, 255, 235), outline=(255, 255, 255, 220), width=3)
            draw.text((95, 800 + bot_y_offset), "MAXIMUM SPEED", font=f_head, fill=(255, 255, 255))
            draw.text((95, 875 + bot_y_offset), "COMPLETE PRIVACY", font=f_col_title, fill=(255, 221, 0))

            draw.rounded_rectangle([1190, 770 + bot_y_offset, 1860, 970 + bot_y_offset], radius=20, fill=(14, 25, 55, 240), outline=(0, 255, 140, 220), width=3)
            draw.text((1225, 800 + bot_y_offset), "100+ APPS READY", font=f_head, fill=(255, 255, 255))
            draw.text((1225, 875 + bot_y_offset), "NO ISP THROTTLING EVER", font=f_col_title, fill=(0, 255, 140))

        proc.stdin.write(im.tobytes())

    proc.stdin.close()
    proc.wait()
    print(f"Generated animated scene 4 video: {output_mp4}")

def write_perfect_teleprompter_ass():
    """Write precision ASS subtitle file with non-overlapping positioning."""
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
    print("=== STARTING ONN 4K PRO COMMERCIAL PIPELINE V4 ===")
    print("1. Generating graphic overlays & studio vignettes...")
    vignette_png = make_studio_vignette()
    s1_overlay = make_scene1_overlay()
    s2_bg = make_scene2_bg()
    s5_overlay = make_scene5_overlay()
    write_perfect_teleprompter_ass()

    master_audio = REPO_DIR / "master_audio.m4a"
    part1 = REPO_DIR / "part1_v4.mp4"
    part2 = REPO_DIR / "part2_v4.mp4"
    part3 = REPO_DIR / "part3_v4.mp4"
    part4 = REPO_DIR / "part4_v4.mp4"
    part5 = REPO_DIR / "part5_v4.mp4"

    full_stage_filter = (
        "[0:v]crop=720:720:300:20,scale=1080:1080[vcrop];"
        "[vcrop]pad=1920:1080:420:0:color=0x080E20[vpad];"
        "[vpad][1:v]overlay=0:0[vvig];"
        "[vvig][2:v]overlay=0:0[vout]"
    )

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

    print("4. Generating Animated Scene 3 (1000+ Channels & Live Sports Motion Graphics)...")
    scene3_anim_raw = REPO_DIR / "scene3_raw_anim.mp4"
    generate_animated_scene3(scene3_anim_raw, total_frames=390, fps=30)

    print("Compositing Scene 3 with Clean PiP Presenter...")
    cmd_p3 = [
        "ffmpeg", "-y",
        "-i", str(scene3_anim_raw),
        "-ss", "3", "-t", "13", "-i", str(AVATAR_VIDEO),
        "-filter_complex",
        f"[1:v]{pip_filter}[pip];"
        "[0:v][pip]overlay=786:700[vout]",
        "-map", "[vout]",
        "-r", "30", "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
        str(part3),
    ]
    subprocess.run(cmd_p3, check=True)

    print("5. Generating Animated Scene 4 (5 Unlinked Libraries + VPN Cyber HUD)...")
    scene4_anim_raw = REPO_DIR / "scene4_raw_anim.mp4"
    generate_animated_scene4(scene4_anim_raw, total_frames=390, fps=30)

    print("Compositing Scene 4 with Clean PiP Presenter...")
    cmd_p4 = [
        "ffmpeg", "-y",
        "-i", str(scene4_anim_raw),
        "-ss", "8", "-t", "13", "-i", str(AVATAR_VIDEO),
        "-filter_complex",
        f"[1:v]{pip_filter}[pip];"
        "[0:v][pip]overlay=786:700[vout]",
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
    concat_txt = REPO_DIR / "concat_v4.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for p in [part1, part2, part3, part4, part5]:
            f.write(f"file '{p.resolve().as_posix()}'\n")

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
