#!/usr/bin/env python3
"""Build 60-Second Onn 4K Pro Commercial - 9:16 Vertical Edition (1080x1920).
Optimized for TikTok, Instagram Reels, and YouTube Shorts.
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
VERTICAL_OUTPUT = OUTPUT_DIR / "Onn_4K_Pro_Commercial_Vertical_9_16.mp4"
VERTICAL_CLEAN = OUTPUT_DIR / "Onn_4K_Pro_Commercial_Vertical_Clean_MusicOnly.mp4"
AVATAR_VIDEO = OUTPUT_DIR / "ScreenRecording_09-05-2026 04-28-18_1(1).mp4"
TV_SHOWCASE = REPO_DIR / "tv_showcase_12s.mp4"
MASTER_AUDIO = REPO_DIR / "master_audio.m4a"
BGM_WAV = REPO_DIR / "bgm.wav"

FONTS = {
    "bebas": str(REPO_DIR / "fonts" / "BebasNeue.ttf"),
    "din": r"C:\Windows\Fonts\bahnschrift.ttf",
    "bold": r"C:\Windows\Fonts\segoeuib.ttf",
    "reg": r"C:\Windows\Fonts\segoeui.ttf",
}

def get_font(key: str, size: int) -> ImageFont.FreeTypeFont:
    path = FONTS.get(key, FONTS["bold"])
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

def draw_star(draw: ImageDraw.Draw, cx: float, cy: float, r_outer: float = 12, r_inner: float = 5, fill=(255, 221, 0)):
    points = []
    for i in range(10):
        r = r_outer if i % 2 == 0 else r_inner
        angle = math.pi / 2 + i * math.pi / 5
        x = cx + r * math.cos(angle)
        y = cy - r * math.sin(angle)
        points.append((x, y))
    draw.polygon(points, fill=fill)

def ease_out_cubic(x: float) -> float:
    return 1 - math.pow(1 - x, 3)

def make_scene1_vertical_overlay() -> str:
    im = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)

    # Top Header Pill
    draw.rounded_rectangle([40, 60, 1040, 150], radius=24, fill=(220, 20, 60, 245), outline=(255, 255, 255, 220), width=3)
    f_warn = get_font("din", 32)
    draw_star(draw, 80, 105, 12, 5, fill=(255, 255, 255))
    draw.text((115, 85), "ATTENTION CABLE & SATELLITE USERS", font=f_warn, fill=(255, 255, 255))
    draw_star(draw, 1000, 105, 12, 5, fill=(255, 255, 255))

    # Top Card: The Pain Point
    draw.rounded_rectangle([40, 175, 1040, 560], radius=24, fill=(12, 22, 52, 245), outline=(0, 212, 255, 200), width=3)
    f_title = get_font("bebas", 58)
    draw.text((70, 195), "TIRED OF PAYING $200+/MONTH?", font=f_title, fill=(255, 221, 0))
    
    f_sub = get_font("din", 26)
    draw.text((72, 275), "• Stop throwing money away on monthly bills", font=f_sub, fill=(255, 255, 255))
    draw.text((72, 325), "• Keep every single live channel forever", font=f_sub, fill=(255, 255, 255))
    draw.text((72, 375), "• Zero contracts, zero equipment rental fees", font=f_sub, fill=(255, 255, 255))

    draw.rounded_rectangle([70, 440, 1010, 530], radius=16, fill=(16, 32, 75, 240), outline=(0, 255, 140, 200), width=2)
    f_stat = get_font("bebas", 36)
    draw.text((95, 460), "★ AVERAGE ANNUAL SAVINGS: $2,400+ PER HOME ★", font=f_stat, fill=(0, 255, 140))

    # Bottom Callout Card
    draw.rounded_rectangle([40, 1530, 1040, 1860], radius=26, fill=(12, 22, 52, 250), outline=(255, 221, 0, 220), width=4)
    f_bot_h = get_font("bebas", 54)
    draw.text((75, 1550), "ELIMINATE YOUR CABLE BILL FOR GOOD!", font=f_bot_h, fill=(255, 221, 0))
    f_bot_sub = get_font("din", 26)
    draw.text((75, 1625), "OVER 1,000+ LIVE CHANNELS • ALL LIVE SPORTS • ZERO PAYWALLS", font=f_bot_sub, fill=(255, 255, 255))

    draw.rounded_rectangle([70, 1710, 1010, 1830], radius=20, fill=(200, 10, 50, 250), outline=(255, 255, 255, 220), width=3)
    f_cta = get_font("bebas", 48)
    draw.text((210, 1735), "TAP TO UPGRADE YOUR TV TODAY!", font=f_cta, fill=(255, 255, 255))

    out = REPO_DIR / "vertical_scene1_overlay.png"
    im.save(out)
    return str(out)

def make_scene2_vertical_overlay() -> str:
    im = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)

    # Top Title
    draw.rounded_rectangle([40, 60, 1040, 150], radius=24, fill=(14, 25, 60, 245), outline=(0, 212, 255, 220), width=3)
    f_h = get_font("bebas", 52)
    draw.text((80, 78), "MEET THE ONN 4K PRO STREAMING POWERHOUSE", font=f_h, fill=(255, 221, 0))

    # Specs Card
    draw.rounded_rectangle([40, 1530, 1040, 1860], radius=26, fill=(12, 22, 52, 250), outline=(0, 212, 255, 220), width=4)
    f_bot_h = get_font("bebas", 44)
    draw.text((75, 1550), "POWERFUL HARDWARE SPECIFICATIONS", font=f_bot_h, fill=(0, 212, 255))
    
    f_spec = get_font("din", 24)
    specs = [
        "✔ 4K Ultra HD & HDR10+ Dolby Audio Output",
        "✔ Ultra-Fast Wi-Fi 6 Streaming with Zero Buffering",
        "✔ 32GB High-Speed Storage Pre-Loaded with Apps",
        "✔ Hands-Free Voice Remote Powered by Google TV",
    ]
    for i, s in enumerate(specs):
        draw.text((75, 1620 + i * 44), s, font=f_spec, fill=(255, 255, 255))

    out = REPO_DIR / "vertical_scene2_overlay.png"
    im.save(out)
    return str(out)

def make_scene5_vertical_overlay() -> str:
    im = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)

    draw.rounded_rectangle([40, 60, 1040, 150], radius=24, fill=(14, 25, 60, 245), outline=(0, 212, 255, 220), width=3)
    f_h = get_font("bebas", 52)
    draw.text((120, 78), "ONN 4K PRO: TOTAL FREEDOM STREAMING", font=f_h, fill=(0, 220, 255))

    # Top benefits
    draw.rounded_rectangle([40, 175, 1040, 560], radius=24, fill=(12, 22, 52, 245), outline=(0, 255, 140, 200), width=3)
    f_title = get_font("bebas", 50)
    draw.text((70, 195), "WHY OVER 50,000+ HOMES MADE THE SWITCH", font=f_title, fill=(0, 255, 140))
    f_sub = get_font("din", 26)
    draw.text((72, 270), "✔ NO CONTRACTS • NO MONTHLY BILLS EVER", font=f_sub, fill=(255, 255, 255))
    draw.text((72, 320), "✔ 1,000+ LIVE BROADCAST CHANNELS WORLDWIDE", font=f_sub, fill=(255, 255, 255))
    draw.text((72, 370), "✔ ALL LIVE SPORTS & PPV FIGHTS INCLUDED", font=f_sub, fill=(255, 255, 255))
    draw.text((72, 420), "✔ 5 UNLINKED LIBRARIES & BUILT-IN ENCRYPTED VPN", font=f_sub, fill=(255, 255, 255))
    draw.text((72, 470), "✔ PLUG & PLAY: CONNECTS IN 60 SECONDS TO ANY TV", font=f_sub, fill=(255, 221, 0))

    # Bottom CTA
    draw.rounded_rectangle([40, 1530, 1040, 1860], radius=26, fill=(12, 22, 52, 250), outline=(255, 221, 0, 220), width=4)
    f_bot_h = get_font("bebas", 58)
    draw.text((130, 1555), "ELIMINATE YOUR CABLE BILL FOREVER!", font=f_bot_h, fill=(255, 221, 0))
    f_bot_sub = get_font("din", 26)
    draw.text((170, 1635), "LIMITED STOCK AVAILABLE • SHIPS NEXT DAY", font=f_bot_sub, fill=(0, 220, 255))

    draw.rounded_rectangle([70, 1710, 1010, 1830], radius=20, fill=(200, 10, 50, 250), outline=(255, 255, 255, 220), width=3)
    f_cta = get_font("bebas", 50)
    draw.text((195, 1735), "UPGRADE TO THE ONN 4K PRO TODAY!", font=f_cta, fill=(255, 255, 255))

    out = REPO_DIR / "vertical_scene5_overlay.png"
    im.save(out)
    return str(out)

def generate_vertical_scene3(output_mp4: Path, total_frames: int = 390, fps: int = 30):
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo", "-s", "1080x1920", "-pix_fmt", "rgba",
        "-r", str(fps), "-i", "-",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
        str(output_mp4)
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    tv_logos = [
        ("abc.png", "ABC"), ("cbs.png", "CBS"), ("nbc.png", "NBC"), ("fox.png", "FOX"),
        ("espn.png", "ESPN"), ("cnn.png", "CNN"), ("hgtv.png", "HGTV"), ("discovery.png", "DISCOVERY"),
    ]
    sports_logos = [
        ("nfl.png", "NFL"), ("nba.png", "NBA"), ("mlb.png", "MLB"),
        ("nhl.png", "NHL"), ("ufc.png", "UFC"), ("ncaa.png", "NCAA"),
    ]
    all_logo_imgs = {}
    for fn, _ in tv_logos + sports_logos:
        p = LOGOS_DIR / fn
        if p.exists():
            im = Image.open(p).convert("RGBA")
            im.thumbnail((190, 68), Image.Resampling.LANCZOS)
            all_logo_imgs[fn] = im

    f_h = get_font("bebas", 48)
    f_sec = get_font("bebas", 34)
    f_bot_h = get_font("bebas", 52)
    f_bot_sub = get_font("bebas", 38)

    w, h = 1080, 1920
    for f_idx in range(total_frames):
        t = f_idx / fps
        im = Image.new("RGBA", (w, h), (8, 14, 30, 255))
        draw = ImageDraw.Draw(im)

        # Top Header
        draw.rounded_rectangle([40, 60, 1040, 150], radius=24, fill=(13, 23, 52, 245), outline=(0, 212, 255, 220), width=3)
        draw.text((70, 80), "OVER 1,000+ LIVE CHANNELS & ALL LIVE SPORTS", font=f_h, fill=(255, 221, 0))

        # Logos Grid Top Area (Y: 175 - 575)
        draw.rounded_rectangle([40, 175, 1040, 575], radius=24, fill=(14, 25, 55, 240), outline=(0, 212, 255, 180), width=3)
        draw.text((70, 190), "MAJOR BROADCAST NETWORKS & SPORTS LEAGUES", font=f_sec, fill=(0, 212, 255))

        # 4 cols x 3 rows grid
        grid_logos = tv_logos[:6] + sports_logos[:6]
        c_w, c_h = 220, 85
        g_x, g_y = 65, 250
        gap_x, gap_y = 20, 16

        for idx, (logo_fn, _) in enumerate(grid_logos):
            col = idx % 4
            row = idx // 4
            cx = g_x + col * (c_w + gap_x)
            cy = g_y + row * (c_h + gap_y)

            draw.rounded_rectangle([cx, cy, cx + c_w, cy + c_h], radius=12, fill=(245, 250, 255, 250), outline=(0, 212, 255, 160), width=2)
            if logo_fn in all_logo_imgs:
                l_im = all_logo_imgs[logo_fn]
                px = cx + (c_w - l_im.width) // 2
                py = cy + (c_h - l_im.height) // 2
                im.alpha_composite(l_im, (px, py))

        # Bottom Callout Cards (Y: 1530 - 1860)
        draw.rounded_rectangle([40, 1530, 525, 1860], radius=24, fill=(220, 20, 60, 235), outline=(255, 255, 255, 220), width=3)
        draw.text((70, 1610), "NO CONTRACTS", font=f_bot_h, fill=(255, 255, 255))
        draw.text((70, 1710), "NO MONTHLY FEES", font=f_bot_sub, fill=(255, 221, 0))

        draw.rounded_rectangle([555, 1530, 1040, 1860], radius=24, fill=(14, 25, 55, 240), outline=(0, 255, 180, 220), width=3)
        draw.text((585, 1610), "ZERO PAYWALLS", font=f_bot_h, fill=(0, 255, 180))
        draw.text((585, 1710), "100% UNLOCKED", font=f_bot_sub, fill=(255, 221, 0))

        proc.stdin.write(im.tobytes())

    proc.stdin.close()
    proc.wait()
    print(f"Generated animated vertical scene 3: {output_mp4}")

def generate_vertical_scene4(output_mp4: Path, total_frames: int = 390, fps: int = 30):
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo", "-s", "1080x1920", "-pix_fmt", "rgba",
        "-r", str(fps), "-i", "-",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
        str(output_mp4)
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    f_h = get_font("bebas", 48)
    f_sec = get_font("bebas", 32)
    f_name = get_font("din", 22)
    f_desc = get_font("reg", 16)
    f_bot_h = get_font("bebas", 52)
    f_bot_sub = get_font("bebas", 34)

    libraries = [
        ("LIB 01", "CINEMA VAULT", "10,000+ Blockbusters, 4K Box Sets", (0, 212, 255)),
        ("LIB 02", "LIVE SPORTS CENTER", "NFL Ticket, NBA Pass, MLB, PPV", (255, 140, 0)),
        ("LIB 03", "CUSTOM APP UNIVERSE", "100+ Pre-Installed Streaming Apps", (0, 255, 180)),
        ("LIB 04", "ON-DEMAND TV HUB", "Full TV Series Binge Vault & Kids", (180, 100, 255)),
        ("LIB 05", "4K ULTRA STREAMING", "Dolby Atmos & 4K Crystal HDR", (255, 221, 0)),
    ]

    w, h = 1080, 1920
    for f_idx in range(total_frames):
        im = Image.new("RGBA", (w, h), (8, 14, 30, 255))
        draw = ImageDraw.Draw(im)

        draw.rounded_rectangle([40, 60, 1040, 150], radius=24, fill=(13, 23, 52, 245), outline=(0, 255, 180, 220), width=3)
        draw.text((80, 80), "5 UNLINKED LIBRARIES + BUILT-IN SECURE VPN", font=f_h, fill=(0, 255, 180))

        # Top area: 5 Libraries (Y: 175 - 575)
        draw.rounded_rectangle([40, 175, 1040, 575], radius=24, fill=(14, 25, 55, 240), outline=(0, 212, 255, 180), width=3)
        draw.text((70, 190), "PRE-CONFIGURED UNLINKED LIBRARIES", font=f_sec, fill=(0, 212, 255))

        for idx, (badge, name, desc, col) in enumerate(libraries):
            cy = 240 + idx * 64
            draw.rounded_rectangle([65, cy, 1015, cy + 56], radius=10, fill=(18, 32, 70, 230), outline=col, width=1)
            draw.rounded_rectangle([75, cy + 8, 175, cy + 48], radius=8, fill=col)
            draw.text((88, cy + 12), badge, font=get_font("bebas", 22), fill=(10, 18, 38))
            draw.text((195, cy + 14), name, font=f_name, fill=(255, 255, 255))
            draw.text((540, cy + 18), desc, font=f_desc, fill=(185, 215, 250))

        # Bottom area: VPN Cyber Security (Y: 1530 - 1860)
        draw.rounded_rectangle([40, 1530, 1040, 1860], radius=26, fill=(12, 22, 52, 250), outline=(0, 255, 180, 220), width=4)
        draw.text((75, 1555), "BUILT-IN MILITARY-GRADE ENCRYPTED VPN", font=f_bot_h, fill=(0, 255, 180))
        f_sub_vpn = get_font("din", 24)
        draw.text((75, 1630), "• 100% Anonymous & Private • Zero Browsing Logs Ever", font=f_sub_vpn, fill=(255, 255, 255))
        draw.text((75, 1680), "• Zero ISP Throttling • Dedicated High-Speed Bandwidth", font=f_sub_vpn, fill=(255, 255, 255))
        draw.text((75, 1730), "• Instant Auto-Protection: Built Directly into the Box", font=f_sub_vpn, fill=(255, 255, 255))

        draw.rounded_rectangle([70, 1785, 1010, 1845], radius=12, fill=(0, 255, 180, 240))
        draw.text((280, 1795), "MAXIMUM SPEED & UNLIMITED CONTENT", font=get_font("bebas", 32), fill=(8, 14, 30))

        proc.stdin.write(im.tobytes())

    proc.stdin.close()
    proc.wait()
    print(f"Generated animated vertical scene 4: {output_mp4}")

def main():
    print("=== STARTING 9:16 VERTICAL COMMERCIAL PIPELINE ===")
    s1_ov = make_scene1_vertical_overlay()
    s2_ov = make_scene2_vertical_overlay()
    s5_ov = make_scene5_vertical_overlay()

    v_p1 = REPO_DIR / "vert_p1.mp4"
    v_p2 = REPO_DIR / "vert_p2.mp4"
    v_p3 = REPO_DIR / "vert_p3.mp4"
    v_p4 = REPO_DIR / "vert_p4.mp4"
    v_p5 = REPO_DIR / "vert_p5.mp4"

    # Presenter centered in vertical middle: crop 640x640 -> scale to 840x840, pad to 1080x1920 at y=620
    vert_presenter_filter = (
        "[0:v]crop=640:640:340:30,scale=840:840,"
        "pad=856:856:8:8:color=0x00D4FF[p_bezel];"
        "[p_bezel]pad=1080:1920:112:620:color=0x080E20[base];"
        "[base][1:v]overlay=0:0[vout]"
    )

    print("1. Encoding Vertical Scene 1 (0-10s)...")
    cmd_p1 = [
        "ffmpeg", "-y",
        "-ss", "0", "-t", "10", "-i", str(AVATAR_VIDEO),
        "-i", s1_ov,
        "-filter_complex", vert_presenter_filter,
        "-map", "[vout]",
        "-r", "30", "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
        str(v_p1)
    ]
    subprocess.run(cmd_p1, check=True)

    print("2. Encoding Vertical Scene 2 (10-22s) with TV Showcase...")
    vert_p2_filter = (
        "[0:v]crop=640:640:340:30,scale=840:840,"
        "pad=856:856:8:8:color=0x00D4FF[p_bezel];"
        "[1:v]scale=760:430,pad=776:446:8:8:color=0x00D4FF[tv_bezel];"
        "[p_bezel]pad=1080:1920:112:620:color=0x080E20[base];"
        "[base][tv_bezel]overlay=152:160[b_tv];"
        "[b_tv][2:v]overlay=0:0[vout]"
    )
    cmd_p2 = [
        "ffmpeg", "-y",
        "-ss", "0", "-t", "12", "-i", str(AVATAR_VIDEO),
        "-i", str(TV_SHOWCASE),
        "-i", s2_ov,
        "-filter_complex", vert_p2_filter,
        "-map", "[vout]",
        "-r", "30", "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
        str(v_p2)
    ]
    subprocess.run(cmd_p2, check=True)

    print("3. Generating Vertical Scene 3 Animated Infographics...")
    s3_raw = REPO_DIR / "vert_s3_raw.mp4"
    generate_vertical_scene3(s3_raw, total_frames=390, fps=30)
    vert_p3_filter = (
        "[1:v]crop=640:640:340:30,scale=840:840,"
        "pad=856:856:8:8:color=0x00D4FF[p_bezel];"
        "[0:v][p_bezel]overlay=112:620[vout]"
    )
    cmd_p3 = [
        "ffmpeg", "-y",
        "-i", str(s3_raw),
        "-ss", "3", "-t", "13", "-i", str(AVATAR_VIDEO),
        "-filter_complex", vert_p3_filter,
        "-map", "[vout]",
        "-r", "30", "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
        str(v_p3)
    ]
    subprocess.run(cmd_p3, check=True)

    print("4. Generating Vertical Scene 4 Animated Infographics...")
    s4_raw = REPO_DIR / "vert_s4_raw.mp4"
    generate_vertical_scene4(s4_raw, total_frames=390, fps=30)
    cmd_p4 = [
        "ffmpeg", "-y",
        "-i", str(s4_raw),
        "-ss", "8", "-t", "13", "-i", str(AVATAR_VIDEO),
        "-filter_complex", vert_p3_filter,
        "-map", "[vout]",
        "-r", "30", "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
        str(v_p4)
    ]
    subprocess.run(cmd_p4, check=True)

    print("5. Encoding Vertical Scene 5 (48-60s)...")
    cmd_p5 = [
        "ffmpeg", "-y",
        "-ss", "10", "-t", "12", "-i", str(AVATAR_VIDEO),
        "-i", s5_ov,
        "-filter_complex", vert_presenter_filter,
        "-map", "[vout]",
        "-r", "30", "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
        str(v_p5)
    ]
    subprocess.run(cmd_p5, check=True)

    print("6. Stitching Vertical Master...")
    concat_txt = REPO_DIR / "concat_vert.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for p in [v_p1, v_p2, v_p3, v_p4, v_p5]:
            f.write(f"file '{p.resolve().as_posix()}'\n")

    cmd_vert_master = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_txt),
        "-i", str(MASTER_AUDIO),
        "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-map", "0:v:0", "-map", "1:a:0",
        "-shortest",
        str(VERTICAL_OUTPUT)
    ]
    subprocess.run(cmd_vert_master, check=True)
    print(f"Rendered Vertical Master: {VERTICAL_OUTPUT}")

    cmd_vert_clean = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_txt),
        "-i", str(BGM_WAV),
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-map", "0:v:0", "-map", "1:a:0",
        "-shortest",
        str(VERTICAL_CLEAN)
    ]
    subprocess.run(cmd_vert_clean, check=True)
    print(f"Rendered Vertical Clean: {VERTICAL_CLEAN}")
    print("=== 9:16 VERTICAL COMMERCIAL COMPLETE! ===")

if __name__ == "__main__":
    main()
