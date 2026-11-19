import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

REPO_DIR = Path(r"C:\Users\tee\.gemini\antigravity-ide\scratch\hermes-agent")
LOGOS_DIR = REPO_DIR / "network_logos"

FONTS = {
    "bebas": str(REPO_DIR / "fonts" / "BebasNeue.ttf"),
    "din": r"C:\Windows\Fonts\bahnschrift.ttf",
    "bold": r"C:\Windows\Fonts\segoeuib.ttf",
    "reg": r"C:\Windows\Fonts\segoeui.ttf",
    "impact": r"C:\Windows\Fonts\impact.ttf",
}

def get_font(key: str, size: int):
    path = FONTS.get(key, FONTS["bold"])
    return ImageFont.truetype(path, size)

def render_scene3_frame(progress: float = 1.0, shimmer_phase: float = 0.5) -> Image.Image:
    """
    Renders Scene 3:
    progress: 0.0 to 1.0 (for entry animation)
    shimmer_phase: 0.0 to 1.0 (for looping light reflection)
    """
    w, h = 1920, 1080
    im = Image.new("RGBA", (w, h), (8, 14, 30, 255))
    draw = ImageDraw.Draw(im)

    # 1. Subtle radial gradient glow behind center
    # Top Header
    draw.rounded_rectangle([60, 20, 1860, 120], radius=20, fill=(13, 23, 52, 245), outline=(0, 212, 255, 220), width=3)
    f_head = get_font("bebas", 58)
    draw.text((100, 32), "OVER 1,000+ LIVE CHANNELS & ALL LIVE SPORTS", font=f_head, fill=(255, 221, 0))
    
    # Header tag on right
    f_tag = get_font("din", 22)
    draw.rounded_rectangle([1520, 40, 1820, 100], radius=15, fill=(0, 180, 255, 40), outline=(0, 212, 255, 180), width=2)
    draw.text((1545, 54), "100% UNLOCKED BROADCAST", font=f_tag, fill=(0, 235, 255))

    # Left Column: Live TV Networks (x: 60..930, y: 145..685)
    draw.rounded_rectangle([60, 145, 930, 685], radius=22, fill=(14, 25, 55, 240), outline=(0, 212, 255, 180), width=3)
    
    # Left Header pill badge
    draw.rounded_rectangle([90, 165, 340, 210], radius=12, fill=(0, 212, 255, 230))
    f_col_title = get_font("bebas", 28)
    draw.text((108, 172), "LIVE TV NETWORKS", font=f_col_title, fill=(8, 14, 30))
    
    f_sub = get_font("din", 19)
    draw.text((360, 178), "ABC, CBS, NBC, FOX, ESPN, CNN & MORE", font=f_sub, fill=(200, 225, 255))

    # Grid of 8 official TV network logos (2 rows of 4)
    tv_logos = [
        ("abc.png", "ABC"),
        ("cbs.png", "CBS"),
        ("nbc.png", "NBC"),
        ("fox.png", "FOX"),
        ("espn.png", "ESPN"),
        ("cnn.png", "CNN"),
        ("hgtv.png", "HGTV"),
        ("discovery.png", "DISCOVERY"),
    ]
    
    card_w, card_h = 190, 88
    grid_start_x = 90
    grid_start_y = 230
    gap_x = 22
    gap_y = 18

    for idx, (logo_fn, name) in enumerate(tv_logos):
        col = idx % 4
        row = idx // 4
        cx = grid_start_x + col * (card_w + gap_x)
        cy = grid_start_y + row * (card_h + gap_y)

        # Card container with frosted glass white-bright pill
        draw.rounded_rectangle([cx, cy, cx + card_w, cy + card_h], radius=14, fill=(245, 250, 255, 250), outline=(0, 212, 255, 160), width=2)
        
        logo_path = LOGOS_DIR / logo_fn
        if logo_path.exists():
            l_img = Image.open(logo_path).convert("RGBA")
            # Preserve aspect ratio fitting within card_w-36, card_h-24
            l_img.thumbnail((card_w - 36, card_h - 22), Image.Resampling.LANCZOS)
            px = cx + (card_w - l_img.width) // 2
            py = cy + (card_h - l_img.height) // 2
            im.alpha_composite(l_img, (px, py))

    # Sub-bullet details under TV cards
    f_item_title = get_font("din", 21)
    f_item_desc = get_font("reg", 17)

    # Bullet 1
    draw.rounded_rectangle([90, 440, 900, 510], radius=12, fill=(20, 34, 72, 180), outline=(0, 212, 255, 80), width=1)
    draw.ellipse([110, 460, 126, 476], fill=(0, 255, 180))
    draw.text((140, 448), "OVER 1,000 CHANNELS WORLDWIDE", font=f_item_title, fill=(255, 255, 255))
    draw.text((140, 478), "News, Entertainment, Family, Kids, Documentaries & Local Broadcasts", font=f_item_desc, fill=(185, 210, 245))

    # Bullet 2
    draw.rounded_rectangle([90, 520, 900, 590], radius=12, fill=(20, 34, 72, 180), outline=(0, 212, 255, 80), width=1)
    draw.ellipse([110, 540, 126, 556], fill=(0, 212, 255))
    draw.text((140, 528), "CRYSTAL 4K ULTRA HD & FULL HD STREAMS", font=f_item_title, fill=(255, 255, 255))
    draw.text((140, 558), "Dolby Digital surround sound with lightning-fast instant channel zapping", font=f_item_desc, fill=(185, 210, 245))

    # Bullet 3
    draw.rounded_rectangle([90, 600, 900, 670], radius=12, fill=(20, 34, 72, 180), outline=(0, 212, 255, 80), width=1)
    draw.ellipse([110, 620, 126, 636], fill=(255, 221, 0))
    draw.text((140, 608), "ZERO MONTHLY FEES • NO CONTRACTS EVER", font=f_item_title, fill=(255, 221, 0))
    draw.text((140, 638), "Plug & play on any TV — keep your channels active forever without paying bills", font=f_item_desc, fill=(185, 210, 245))

    # Right Column: All Live Sports (x: 990..1860, y: 145..685)
    draw.rounded_rectangle([990, 145, 1860, 685], radius=22, fill=(14, 25, 55, 240), outline=(255, 140, 0, 180), width=3)
    
    # Right Header pill badge
    draw.rounded_rectangle([1020, 165, 1290, 210], radius=12, fill=(255, 140, 0, 230))
    draw.text((1038, 172), "ALL LIVE SPORTS & PPV", font=f_col_title, fill=(8, 14, 30))
    draw.text((1310, 178), "EVERY GAME • EVERY LEAGUE • ZERO PAYWALLS", font=f_sub, fill=(255, 220, 180))

    # Grid of 6 official sports logos (2 rows of 3)
    sports_logos = [
        ("nfl.png", "NFL"),
        ("nba.png", "NBA"),
        ("mlb.png", "MLB"),
        ("nhl.png", "NHL"),
        ("ufc.png", "UFC"),
        ("ncaa.png", "NCAA"),
    ]
    
    s_card_w, s_card_h = 255, 88
    s_start_x = 1020
    s_start_y = 230
    s_gap_x = 22
    s_gap_y = 18

    for idx, (logo_fn, name) in enumerate(sports_logos):
        col = idx % 3
        row = idx // 3
        cx = s_start_x + col * (s_card_w + s_gap_x)
        cy = s_start_y + row * (s_card_h + s_gap_y)

        draw.rounded_rectangle([cx, cy, cx + s_card_w, cy + s_card_h], radius=14, fill=(245, 250, 255, 250), outline=(255, 140, 0, 160), width=2)
        
        logo_path = LOGOS_DIR / logo_fn
        if logo_path.exists():
            l_img = Image.open(logo_path).convert("RGBA")
            l_img.thumbnail((s_card_w - 40, s_card_h - 22), Image.Resampling.LANCZOS)
            px = cx + (s_card_w - l_img.width) // 2
            py = cy + (s_card_h - l_img.height) // 2
            im.alpha_composite(l_img, (px, py))

    # Sub-bullet details under Sports cards
    # Bullet 1
    draw.rounded_rectangle([1020, 440, 1830, 510], radius=12, fill=(20, 34, 72, 180), outline=(255, 140, 0, 80), width=1)
    draw.ellipse([1040, 460, 1056, 476], fill=(255, 140, 0))
    draw.text((1070, 448), "NFL SUNDAY TICKET & REDZONE PASS", font=f_item_title, fill=(255, 255, 255))
    draw.text((1070, 478), "Catch every out-of-market touchdown live without high-priced satellite packages", font=f_item_desc, fill=(185, 210, 245))

    # Bullet 2
    draw.rounded_rectangle([1020, 520, 1830, 590], radius=12, fill=(20, 34, 72, 180), outline=(255, 140, 0, 80), width=1)
    draw.ellipse([1040, 540, 1056, 556], fill=(0, 212, 255))
    draw.text((1070, 528), "NBA LEAGUE PASS, MLB & NHL CENTER ICE", font=f_item_title, fill=(255, 255, 255))
    draw.text((1070, 558), "Full regular season and playoff access for basketball, baseball, hockey & college sports", font=f_item_desc, fill=(185, 210, 245))

    # Bullet 3
    draw.rounded_rectangle([1020, 600, 1830, 670], radius=12, fill=(20, 34, 72, 180), outline=(255, 140, 0, 80), width=1)
    draw.ellipse([1040, 620, 1056, 636], fill=(255, 40, 60))
    draw.text((1070, 608), "CHAMPIONSHIP UFC & BOXING PAY-PER-VIEWS", font=f_item_title, fill=(255, 221, 0))
    draw.text((1070, 638), "Stream major championship PPV title fights included with zero extra fees", font=f_item_desc, fill=(185, 210, 245))

    # Bottom Callout Cards (positioned left & right of PiP presenter)
    # Left callout (x: 60..730, y: 770..970)
    draw.rounded_rectangle([60, 770, 730, 970], radius=20, fill=(220, 20, 60, 235), outline=(255, 255, 255, 220), width=3)
    f_bot_title = get_font("bebas", 48)
    f_bot_sub = get_font("bebas", 38)
    draw.text((95, 800), "NO CONTRACTS", font=f_bot_title, fill=(255, 255, 255))
    draw.text((95, 875), "NO MONTHLY FEES", font=f_bot_sub, fill=(255, 221, 0))

    # Right callout (x: 1190..1860, y: 770..970)
    draw.rounded_rectangle([1190, 770, 1860, 970], radius=20, fill=(14, 25, 55, 240), outline=(0, 255, 180, 220), width=3)
    draw.text((1225, 800), "ZERO PAYWALLS", font=f_bot_title, fill=(0, 255, 180))
    draw.text((1225, 875), "100% UNLOCKED ENTERTAINMENT", font=f_bot_sub, fill=(255, 221, 0))

    # PiP Placeholder area (x: 786, y: 700, size: 348x348)
    # Just draw border to verify layout
    draw.rounded_rectangle([782, 696, 782 + 356, 696 + 356], radius=16, outline=(0, 212, 255, 180), width=3)

    return im

def render_scene4_frame(progress: float = 1.0) -> Image.Image:
    """
    Renders Scene 4: 5 Unlinked Libraries + Built-In Secure VPN
    """
    w, h = 1920, 1080
    im = Image.new("RGBA", (w, h), (8, 14, 30, 255))
    draw = ImageDraw.Draw(im)

    # Top Header
    draw.rounded_rectangle([60, 20, 1860, 120], radius=20, fill=(13, 23, 52, 245), outline=(0, 255, 180, 220), width=3)
    f_head = get_font("bebas", 58)
    draw.text((100, 32), "5 UNLINKED LIBRARIES + BUILT-IN SECURE VPN", font=f_head, fill=(0, 255, 180))

    f_tag = get_font("din", 22)
    draw.rounded_rectangle([1520, 40, 1820, 100], radius=15, fill=(0, 255, 180, 40), outline=(0, 255, 180, 180), width=2)
    draw.text((1540, 54), "ENTERTAINMENT ECOSYSTEM", font=f_tag, fill=(0, 255, 180))

    # Left Column: 5 Libraries (x: 60..930, y: 145..685)
    draw.rounded_rectangle([60, 145, 930, 685], radius=22, fill=(14, 25, 55, 240), outline=(0, 212, 255, 180), width=3)
    
    f_col_title = get_font("bebas", 28)
    draw.rounded_rectangle([90, 165, 360, 210], radius=12, fill=(0, 212, 255, 230))
    draw.text((108, 172), "5 UNLINKED LIBRARIES", font=f_col_title, fill=(8, 14, 30))
    
    f_sub = get_font("din", 19)
    draw.text((380, 178), "PRE-CONFIGURED & INSTANTLY ACCESSIBLE", font=f_sub, fill=(200, 225, 255))

    libraries = [
        ("LIB 01", "CINEMA VAULT", "10,000+ Blockbuster Releases, 4K Box Sets & Complete Series", (0, 212, 255)),
        ("LIB 02", "LIVE SPORTS CENTER", "NFL Sunday Ticket, NBA League Pass, MLB, NHL & PPV Fights", (255, 140, 0)),
        ("LIB 03", "CUSTOM APP UNIVERSE", "Over 100+ Pre-Installed Streaming Apps & Power User Tools", (0, 255, 180)),
        ("LIB 04", "ON-DEMAND TV HUB", "Full TV Series Binge Vault, Reality Shows & Kids Networks", (180, 100, 255)),
        ("LIB 05", "4K ULTRA STREAMING", "Dolby Atmos Surround Audio & Pure 4K Crystal HDR Playback", (255, 221, 0)),
    ]

    card_start_y = 225
    c_h = 82
    c_gap = 10
    f_badge = get_font("bebas", 22)
    f_name = get_font("din", 22)
    f_desc = get_font("reg", 16)

    for idx, (badge, name, desc, accent) in enumerate(libraries):
        cy = card_start_y + idx * (c_h + c_gap)
        # Card body
        draw.rounded_rectangle([90, cy, 900, cy + c_h], radius=14, fill=(18, 30, 64, 220), outline=accent, width=2)
        
        # Badge pill
        draw.rounded_rectangle([105, cy + 18, 180, cy + c_h - 18], radius=8, fill=accent)
        draw.text((114, cy + 26), badge, font=f_badge, fill=(8, 14, 30))
        
        # Title & description
        draw.text((195, cy + 14), name, font=f_name, fill=(255, 255, 255))
        draw.text((195, cy + 44), desc, font=f_desc, fill=(190, 215, 245))

    # Right Column: Built-In VPN Included (x: 990..1860, y: 145..685)
    draw.rounded_rectangle([990, 145, 1860, 685], radius=22, fill=(14, 25, 55, 240), outline=(0, 255, 140, 180), width=3)
    
    draw.rounded_rectangle([1020, 165, 1310, 210], radius=12, fill=(0, 255, 140, 230))
    draw.text((1038, 172), "BUILT-IN SECURE VPN", font=f_col_title, fill=(8, 14, 30))
    draw.text((1330, 178), "100% PRIVATE • ANONYMOUS • NO LOGS", font=f_sub, fill=(200, 255, 220))

    vpn_features = [
        ("AES-256", "MILITARY-GRADE 256-BIT ENCRYPTION", "Bank-level AES encryption shields all your streaming activity", (0, 255, 140)),
        ("SPEED", "ZERO ISP THROTTLING & BUFFERING", "Bypass Internet provider speed limits for lightning 4K playback", (0, 212, 255)),
        ("PRIVACY", "STRICT ZERO-LOG PRIVACY POLICY", "Total anonymity with zero tracking, logging, or activity records", (255, 221, 0)),
        ("SERVERS", "HIGH-SPEED DEDICATED SERVERS", "Optimized global bandwidth for instant buffer-free streaming", (255, 140, 0)),
        ("AUTO", "INSTANT ONE-CLICK PROTECTION", "Automatic connection built into the box — zero setup needed", (0, 255, 180)),
    ]

    for idx, (badge, name, desc, accent) in enumerate(vpn_features):
        cy = card_start_y + idx * (c_h + c_gap)
        draw.rounded_rectangle([1020, cy, 1830, cy + c_h], radius=14, fill=(18, 30, 64, 220), outline=accent, width=2)
        
        # Badge pill
        draw.rounded_rectangle([1035, cy + 18, 1125, cy + c_h - 18], radius=8, fill=accent)
        draw.text((1045, cy + 26), badge, font=f_badge, fill=(8, 14, 30))
        
        draw.text((1145, cy + 14), name, font=f_name, fill=(255, 255, 255))
        draw.text((1145, cy + 44), desc, font=f_desc, fill=(190, 215, 245))

    # Bottom Callout Cards
    # Left callout (x: 60..730, y: 770..970)
    draw.rounded_rectangle([60, 770, 730, 970], radius=20, fill=(0, 140, 255, 235), outline=(255, 255, 255, 220), width=3)
    draw.text((95, 800), "MAXIMUM SPEED", font=f_head, fill=(255, 255, 255))
    draw.text((95, 875), "COMPLETE PRIVACY", font=f_col_title, fill=(255, 221, 0))

    # Right callout (x: 1190..1860, y: 770..970)
    draw.rounded_rectangle([1190, 770, 1860, 970], radius=20, fill=(14, 25, 55, 240), outline=(0, 255, 140, 220), width=3)
    draw.text((1225, 800), "100+ APPS READY", font=f_head, fill=(255, 255, 255))
    draw.text((1225, 875), "NO ISP THROTTLING EVER", font=f_col_title, fill=(0, 255, 140))

    # PiP Placeholder
    draw.rounded_rectangle([782, 696, 782 + 356, 696 + 356], radius=16, outline=(0, 255, 180, 180), width=3)

    return im

if __name__ == "__main__":
    im3 = render_scene3_frame()
    im3.save(REPO_DIR / "sample_scene3_new.png")
    print("Saved sample_scene3_new.png")

    im4 = render_scene4_frame()
    im4.save(REPO_DIR / "sample_scene4_new.png")
    print("Saved sample_scene4_new.png")
