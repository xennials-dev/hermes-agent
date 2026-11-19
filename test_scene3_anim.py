import math
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np

REPO_DIR = Path(r"C:\Users\tee\.gemini\antigravity-ide\scratch\hermes-agent")
LOGOS_DIR = REPO_DIR / "network_logos"

FONTS = {
    "bebas": str(REPO_DIR / "fonts" / "BebasNeue.ttf"),
    "din": r"C:\Windows\Fonts\bahnschrift.ttf",
    "bold": r"C:\Windows\Fonts\segoeuib.ttf",
    "reg": r"C:\Windows\Fonts\segoeui.ttf",
}

def get_font(key: str, size: int):
    path = FONTS.get(key, FONTS["bold"])
    return ImageFont.truetype(path, size)

def ease_out_back(x: float) -> float:
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * math.pow(x - 1, 3) + c1 * math.pow(x - 1, 2)

def ease_out_cubic(x: float) -> float:
    return 1 - math.pow(1 - x, 3)

def generate_scene3_animation(output_mp4: Path, total_frames: int = 390, fps: int = 30):
    """
    Renders animated Scene 3 motion graphics directly to ffmpeg pipe.
    """
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", "1920x1080",
        "-pix_fmt", "rgba",
        "-r", str(fps),
        "-i", "-",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        str(output_mp4)
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    # Preload logos
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

        # 1. Header (Stagger: frames 0..20)
        h_prog = min(1.0, f_idx / 20.0)
        h_y_offset = int((1.0 - ease_out_cubic(h_prog)) * -60)
        
        draw.rounded_rectangle([60, 20 + h_y_offset, 1860, 120 + h_y_offset], radius=20, fill=(13, 23, 52, 245), outline=(0, 212, 255, 220), width=3)
        draw.text((100, 32 + h_y_offset), "OVER 1,000+ LIVE CHANNELS & ALL LIVE SPORTS", font=f_head, fill=(255, 221, 0))

        # Pulsing Live tag in top right
        pulse_alpha = int(180 + 75 * math.sin(t * 4.0))
        draw.rounded_rectangle([1520, 40 + h_y_offset, 1820, 100 + h_y_offset], radius=15, fill=(0, 180, 255, 40), outline=(0, 212, 255, pulse_alpha), width=2)
        draw.text((1545, 54 + h_y_offset), "100% UNLOCKED BROADCAST", font=f_tag, fill=(0, 235, 255))

        # 2. Left Column Panel: Live TV Networks
        p_left_prog = min(1.0, max(0.0, (f_idx - 5) / 25.0))
        p_left_x_offset = int((1.0 - ease_out_cubic(p_left_prog)) * -100)
        panel_alpha = int(240 * p_left_prog)

        if p_left_prog > 0:
            lx1, ly1, lx2, ly2 = 60 + p_left_x_offset, 145, 930 + p_left_x_offset, 685
            draw.rounded_rectangle([lx1, ly1, lx2, ly2], radius=22, fill=(14, 25, 55, panel_alpha), outline=(0, 212, 255, int(180 * p_left_prog)), width=3)
            
            # Left Header pill badge with live red dot
            draw.rounded_rectangle([90 + p_left_x_offset, 165, 340 + p_left_x_offset, 210], radius=12, fill=(0, 212, 255, 230))
            draw.text((108 + p_left_x_offset, 172), "LIVE TV NETWORKS", font=f_col_title, fill=(8, 14, 30))
            draw.text((360 + p_left_x_offset, 178), "ABC, CBS, NBC, FOX, ESPN, CNN & MORE", font=f_sub, fill=(200, 225, 255))

            # 8 TV Logos Stagger
            card_w, card_h = 190, 88
            grid_start_x = 90 + p_left_x_offset
            grid_start_y = 230
            gap_x = 22
            gap_y = 18

            # Shimmer sweep across cards every 3 seconds
            shimmer_cycle = (t % 3.0) / 3.0
            shimmer_active_col = shimmer_cycle * 6.0 - 1.0

            for idx, (logo_fn, name) in enumerate(tv_logos):
                col = idx % 4
                row = idx // 4
                card_delay = 10 + idx * 3
                c_prog = min(1.0, max(0.0, (f_idx - card_delay) / 16.0))
                if c_prog <= 0:
                    continue

                scale = ease_out_back(c_prog) if c_prog < 1.0 else 1.0
                cx = grid_start_x + col * (card_w + gap_x)
                cy = grid_start_y + row * (card_h + gap_y)

                # Shimmer highlight if active
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

            # Bullets
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

        # 3. Right Column Panel: All Live Sports
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

                # Shimmer highlight
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

            # Sports Bullets
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

        # 4. Bottom Callout Cards (Entrance stagger: frames 20..40)
        bot_prog = min(1.0, max(0.0, (f_idx - 20) / 20.0))
        bot_y_offset = int((1.0 - ease_out_cubic(bot_prog)) * 120)

        if bot_prog > 0:
            # Left callout
            draw.rounded_rectangle([60, 770 + bot_y_offset, 730, 970 + bot_y_offset], radius=20, fill=(220, 20, 60, 235), outline=(255, 255, 255, 220), width=3)
            draw.text((95, 800 + bot_y_offset), "NO CONTRACTS", font=f_bot_title, fill=(255, 255, 255))
            draw.text((95, 875 + bot_y_offset), "NO MONTHLY FEES", font=f_bot_sub, fill=(255, 221, 0))

            # Right callout
            draw.rounded_rectangle([1190, 770 + bot_y_offset, 1860, 970 + bot_y_offset], radius=20, fill=(14, 25, 55, 240), outline=(0, 255, 180, 220), width=3)
            draw.text((1225, 800 + bot_y_offset), "ZERO PAYWALLS", font=f_bot_title, fill=(0, 255, 180))
            draw.text((1225, 875 + bot_y_offset), "100% UNLOCKED ENTERTAINMENT", font=f_bot_sub, fill=(255, 221, 0))

        # Write frame to pipe
        proc.stdin.write(im.tobytes())

    proc.stdin.close()
    proc.wait()
    print(f"Generated animated scene 3 video: {output_mp4}")

if __name__ == "__main__":
    test_out = REPO_DIR / "test_scene3_anim.mp4"
    print("Testing animation generation for Scene 3 (13 seconds, 390 frames)...")
    generate_scene3_animation(test_out, total_frames=390, fps=30)
