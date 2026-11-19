import subprocess
from pathlib import Path
from PIL import Image

ARTIFACTS = Path(r"C:\Users\tee\.gemini\antigravity-ide\brain\1365cf60-be83-4bc5-874c-bcc1f81613de")
REPO = Path(r"C:\Users\tee\.gemini\antigravity-ide\scratch\hermes-agent")
LOGOS = REPO / "tv_logos"

# The 5 generated images
clips_data = [
    {
        "img": ARTIFACTS / "nba_dunk_cinematic_1791859621131.jpg",
        "logo": LOGOS / "logo_nba.png",
        "dur": 2.4,
        "zoom": "min(zoom+0.0015,1.15)",
        "out": REPO / "clip_nba.mp4"
    },
    {
        "img": ARTIFACTS / "nfl_touchdown_cinematic_1791859639757.jpg",
        "logo": LOGOS / "logo_nfl.png",
        "dur": 2.4,
        "zoom": "min(zoom+0.0015,1.15)",
        "out": REPO / "clip_nfl.mp4"
    },
    {
        "img": ARTIFACTS / "ncaa_action_cinematic_1791859658831.jpg",
        "logo": LOGOS / "logo_ncaa.png",
        "dur": 2.4,
        "zoom": "min(zoom+0.0015,1.15)",
        "out": REPO / "clip_ncaa.mp4"
    },
    {
        "img": ARTIFACTS / "nhl_hockey_cinematic_1791859677587.jpg",
        "logo": LOGOS / "logo_nhl.png",
        "dur": 2.4,
        "zoom": "min(zoom+0.0015,1.15)",
        "out": REPO / "clip_nhl.mp4"
    },
    {
        "img": ARTIFACTS / "movie_blockbuster_cinematic_1791859696714.jpg",
        "logo": LOGOS / "logo_cinema.png",
        "dur": 2.4,
        "zoom": "min(zoom+0.0015,1.15)",
        "out": REPO / "clip_cinema.mp4"
    }
]

# Resolution of TV display area is 880x500
W, H = 880, 500

for item in clips_data:
    # 1. First overlay the logo onto the top-right of the image
    base = Image.open(item["img"]).convert("RGBA").resize((W, H), Image.Resampling.LANCZOS)
    lg = Image.open(item["logo"]).convert("RGBA")
    # scale logo to 220x62
    lg = lg.resize((220, 62), Image.Resampling.LANCZOS)
    base.paste(lg, (W - 240, 20), lg)
    stamped_path = REPO / f"stamped_{item['out'].stem}.png"
    base.save(stamped_path)
    
    # 2. Render dynamic motion video clip with ffmpeg zoompan
    # 2.4 seconds at 30fps = 72 frames
    frames = int(item["dur"] * 30)
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(stamped_path),
        "-vf", f"zoompan=z='{item['zoom']}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps=30",
        "-t", str(item["dur"]),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        str(item["out"])
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    print(f"Rendered {item['out'].name}")

# Concat all 5 clips into tv_showcase_12s.mp4
concat_list = REPO / "tv_clips_concat.txt"
with open(concat_list, "w", encoding="utf-8") as f:
    for item in clips_data:
        f.write(f"file '{item['out'].resolve().as_posix()}'\n")

tv_showcase_mp4 = REPO / "tv_showcase_12s.mp4"
cmd_concat = [
    "ffmpeg", "-y",
    "-f", "concat", "-safe", "0", "-i", str(concat_list),
    "-c:v", "libx264", "-pix_fmt", "yuv420p",
    str(tv_showcase_mp4)
]
subprocess.run(cmd_concat, check=True, capture_output=True)
print(f"SUCCESS: Generated {tv_showcase_mp4}")
