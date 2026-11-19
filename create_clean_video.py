import subprocess
from pathlib import Path

repo = Path(r"C:\Users\tee\.gemini\antigravity-ide\scratch\hermes-agent")
concat_txt = repo / "concat_clean.txt"
with open(concat_txt, "w", encoding="utf-8") as f:
    for i in range(1, 6):
        part = (repo / f"part{i}.mp4").resolve()
        f.write(f"file '{part.as_posix()}'\n")

bgm_wav = repo / "bgm.wav"
clean_output = Path(r"D:\AI-Avatars\Onn_4K_Pro_Commercial_Clean_MusicOnly.mp4")

cmd = [
    "ffmpeg", "-y",
    "-f", "concat", "-safe", "0", "-i", str(concat_txt),
    "-i", str(bgm_wav),
    "-c:v", "copy",
    "-c:a", "aac", "-b:a", "192k",
    "-map", "0:v:0", "-map", "1:a:0",
    "-shortest",
    str(clean_output)
]
print("Running ffmpeg...")
res = subprocess.run(cmd, capture_output=True, text=True)
if res.returncode == 0:
    print(f"SUCCESS: Generated {clean_output}")
else:
    print("Error:", res.stderr[-500:])
