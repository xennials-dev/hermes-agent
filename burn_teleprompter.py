import subprocess
from pathlib import Path

video_in = Path(r"D:\AI-Avatars\Onn_4K_Pro_Commercial_Clean_MusicOnly.mp4")
ass_file = Path(r"D:\AI-Avatars\Onn_4K_Pro_Commercial_Voiceover.ass")
video_out = Path(r"D:\AI-Avatars\Onn_4K_Pro_Commercial_Teleprompter_Guide.mp4")

# Construct exact, pixel-perfect 1920x1080 ASS subtitle script
ass_content = """[Script Info]
Title: Onn 4K Pro Commercial Teleprompter Guide
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Hook,Arial,28,&H00FFFFFF,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,3,2,0,8,60,60,115,1
Style: Scene2,Arial,24,&H0000FFFF,&H000000FF,&H00000000,&H900B1430,-1,0,0,0,100,100,0,0,3,2,0,2,460,60,35,1
Style: Scene3,Arial,26,&H00FFFFFF,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,3,2,0,8,60,60,775,1
Style: Scene4,Arial,25,&H0000FF88,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,3,2,0,8,60,60,775,1
Style: Scene5,Arial,28,&H00FFFFFF,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,3,2,0,8,60,60,645,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.50,0:00:09.50,Hook,,0,0,0,,Are you tired of paying hundreds of dollars every month for cable and streaming services? There is a better way.
Dialogue: 0,0:00:10.50,0:00:21.50,Scene2,,0,0,0,,{\\pos(1160,940)}Meet the Onn 4K Pro streaming box. It turns any television into an ultimate entertainment powerhouse.
Dialogue: 0,0:00:22.50,0:00:34.50,Scene3,,0,0,0,,{\\pos(960,780)}Get over one thousand live channels, live sports, pay-per-view events, and thousands of movies and TV shows.
Dialogue: 0,0:00:35.50,0:00:47.50,Scene4,,0,0,0,,{\\pos(960,780)}With five unlinked libraries and a built-in VPN, you get unlimited content with complete privacy and lightning speed.
Dialogue: 0,0:00:48.50,0:00:59.50,Scene5,,0,0,0,,{\\pos(960,650)}No contracts, no monthly fees, and no hassles. Eliminate your cable bill forever and upgrade to the Onn 4K Pro today!
"""

with open(ass_file, "w", encoding="utf-8") as f:
    f.write(ass_content)

ass_escaped = str(ass_file).replace("\\", "/").replace(":", "\\:")

cmd = [
    "ffmpeg", "-y",
    "-i", str(video_in),
    "-vf", f"ass='{ass_escaped}'",
    "-c:v", "libx264", "-preset", "fast", "-crf", "19",
    "-c:a", "copy",
    str(video_out)
]

print("Rendering teleprompter guide video with precise ASS styling...")
res = subprocess.run(cmd, capture_output=True, text=True)
if res.returncode == 0:
    print(f"SUCCESS: Rendered {video_out}")
else:
    print("Error:", res.stderr[-500:])
