#!/usr/bin/env python3
"""
Autonomous Media Player Router for Video Renders
Discovers open-source media players (mpv, MPC-HC, MPC-BE, SMPlayer, VLC),
inspects media metadata via ffprobe, scores candidates based on intent and file attributes,
and routes playback with seamless fallback and non-blocking detached execution.
"""

import sys
import os
import json
import shutil
import argparse
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple, Any

# Player metadata registry
PLAYERS = {
    "mpv": {
        "name": "mpv",
        "winget_id": "shinchiro.mpv",
        "executables": ["mpv.exe", "mpv"],
        "known_paths": [
            r"C:\Program Files\mpv\mpv.exe",
            r"C:\Program Files (x86)\mpv\mpv.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\mpv\mpv.exe"),
            os.path.expandvars(r"%USERPROFILE%\scoop\apps\mpv\current\mpv.exe"),
            os.path.expandvars(r"%USERPROFILE%\scoop\shims\mpv.exe"),
        ],
        "base_score": 55,
        "default_args": ["--keep-open=yes", "--force-window=yes"],
        "loop_arg": "--loop",
    },
    "mpc-hc": {
        "name": "Media Player Classic - Home Cinema (clsid2)",
        "winget_id": "clsid2.mpc-hc",
        "executables": ["mpc-hc64.exe", "mpc-hc.exe"],
        "known_paths": [
            r"C:\Program Files\MPC-HC\mpc-hc64.exe",
            r"C:\Program Files (x86)\MPC-HC\mpc-hc.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\MPC-HC\mpc-hc64.exe"),
            os.path.expandvars(r"%USERPROFILE%\scoop\apps\mpc-hc\current\mpc-hc64.exe"),
        ],
        "base_score": 50,
        "default_args": [],
        "loop_arg": "/loop",
    },
    "mpc-be": {
        "name": "Media Player Classic - Black Edition",
        "winget_id": "MPC-BE.MPC-BE",
        "executables": ["mpc-be64.exe", "mpc-be.exe"],
        "known_paths": [
            r"C:\Program Files\MPC-BE x64\mpc-be64.exe",
            r"C:\Program Files\MPC-BE\mpc-be64.exe",
            r"C:\Program Files (x86)\MPC-BE\mpc-be.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\MPC-BE\mpc-be64.exe"),
        ],
        "base_score": 45,
        "default_args": [],
        "loop_arg": "/loop",
    },
    "smplayer": {
        "name": "SMPlayer",
        "winget_id": "RicardoVillalba.SMPlayer",
        "executables": ["smplayer.exe"],
        "known_paths": [
            r"C:\Program Files\SMPlayer\smplayer.exe",
            r"C:\Program Files (x86)\SMPlayer\smplayer.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\SMPlayer\smplayer.exe"),
        ],
        "base_score": 40,
        "default_args": [],
        "loop_arg": "-loop",
    },
    "vlc": {
        "name": "VLC media player",
        "winget_id": "VideoLAN.VLC",
        "executables": ["vlc.exe", "vlc"],
        "known_paths": [
            r"C:\Program Files\VideoLAN\VLC\vlc.exe",
            r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\VLC\vlc.exe"),
            os.path.expandvars(r"%USERPROFILE%\scoop\apps\vlc\current\vlc.exe"),
        ],
        "base_score": 30,
        "default_args": [],
        "loop_arg": "--loop",
    },
}


def find_player_executable(key: str) -> Optional[str]:
    """Scans PATH and standard system installation paths for a given player."""
    meta = PLAYERS.get(key)
    if not meta:
        return None

    # Check PATH first
    for exe in meta["executables"]:
        found = shutil.which(exe)
        if found and os.path.isfile(found):
            return str(Path(found).resolve())

    # Check known absolute paths
    for p in meta["known_paths"]:
        if os.path.isfile(p):
            return str(Path(p).resolve())

    return None


def scan_installed_players() -> Dict[str, Optional[str]]:
    """Discovers which open-source media players are installed on this machine."""
    results = {}
    for key in PLAYERS:
        results[key] = find_player_executable(key)
    return results


def print_scan_report(installed: Dict[str, Optional[str]]):
    """Prints a formatted report of discovered players with installation commands."""
    print("================ Open-Source Media Player Status ================")
    for key, meta in PLAYERS.items():
        path = installed.get(key)
        if path:
            print(f" * {meta['name']} ({key}): [INSTALLED] -> {path}")
        else:
            print(f" * {meta['name']} ({key}): [NOT FOUND] (Install: winget install {meta['winget_id']})")
    print("=================================================================")


def probe_media_file(file_path: Path) -> Dict[str, Any]:
    """Uses ffprobe to extract technical metadata from the target video."""
    info = {
        "duration": 0.0,
        "width": 0,
        "height": 0,
        "codec": "unknown",
        "bitrate": 0,
        "fps": 0.0,
    }

    if not file_path.exists():
        # Fallback to simulated defaults for dry-run if file doesn't exist yet
        info["duration"] = 25.0
        return info

    ffprobe_cmd = shutil.which("ffprobe")
    if not ffprobe_cmd:
        # Fallback to basic file size heuristic
        return info

    try:
        cmd = [
            ffprobe_cmd,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(file_path)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=8)
        data = json.loads(res.stdout)

        fmt = data.get("format", {})
        info["duration"] = float(fmt.get("duration", 0.0))
        info["bitrate"] = int(fmt.get("bit_rate", 0))

        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                info["codec"] = stream.get("codec_name", "unknown").lower()
                info["width"] = int(stream.get("width", 0))
                info["height"] = int(stream.get("height", 0))
                r_frame_rate = stream.get("r_frame_rate", "0/1")
                if "/" in r_frame_rate:
                    num, den = r_frame_rate.split("/")
                    if float(den) > 0:
                        info["fps"] = round(float(num) / float(den), 2)
                break
    except Exception:
        pass

    return info


def score_players(meta: Dict[str, Any], intent: str) -> Dict[str, int]:
    """Calculates player fit scores based on intent and metadata."""
    scores = {k: PLAYERS[k]["base_score"] for k in PLAYERS}

    # Intent-driven weighting
    if intent == "animation":
        scores["mpv"] += 40
        scores["vlc"] += 10
    elif intent == "prores":
        scores["mpc-hc"] += 50
        scores["mpc-be"] += 35
        scores["vlc"] += 10
    elif intent == "dark-ui":
        scores["mpc-be"] += 55
        scores["mpc-hc"] += 25
    elif intent == "gui":
        scores["smplayer"] += 60
        scores["vlc"] += 20
    elif intent == "inspect":
        scores["vlc"] += 80
        scores["mpc-hc"] += 20
    else:  # 'auto'
        # Heuristics:
        duration = meta.get("duration", 0.0)
        codec = meta.get("codec", "").lower()
        bitrate = meta.get("bitrate", 0)

        # Short animations benefit most from mpv lightweight instant looping
        if 0 < duration < 45.0 or duration == 0:
            scores["mpv"] += 40

        # ProRes or heavy mastering codecs benefit most from MPC-HC scrubbing
        if "prores" in codec or "dnxhd" in codec or bitrate > 25_000_000:
            scores["mpc-hc"] += 50
            scores["mpc-be"] += 30

    return scores


def launch_player_detached(executable: str, args: list, file_paths: list):
    """Launches player executable in a detached, non-blocking background process."""
    cmd = [executable] + args + [str(p) for p in file_paths]
    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP

    subprocess.Popen(
        cmd,
        creationflags=creationflags,
        close_fds=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


def main():
    parser = argparse.ArgumentParser(
        description="Autonomous Media Player Router for Video Renders"
    )
    parser.add_argument("video_paths", nargs="*", default=[], help="Path(s) to the video file(s) to play")
    parser.add_argument(
        "--intent",
        choices=["auto", "animation", "prores", "dark-ui", "gui", "inspect"],
        default="auto",
        help="Target viewing intent (e.g. animation, prores, inspect)"
    )
    parser.add_argument("--loop", action="store_true", help="Force looping playback")
    parser.add_argument("--dry-run", action="store_true", help="Calculate optimal route without launching")
    parser.add_argument("--scan-only", action="store_true", help="Scan and display media player status")

    args = parser.parse_args()

    # Discover installed players
    installed = scan_installed_players()

    if args.scan_only:
        print_scan_report(installed)
        sys.exit(0)

    if not args.video_paths:
        print("Error: No video path provided. Use --scan-only to inspect available players.")
        sys.exit(1)

    video_files = [Path(p).resolve() for p in args.video_paths]
    primary_file = video_files[0]

    # Probe metadata of primary file
    meta = probe_media_file(primary_file)

    # Calculate scores
    scores = score_players(meta, args.intent)

    # Sort candidates by score descending
    sorted_candidates = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_key, top_score = sorted_candidates[0]

    # Find highest-scoring installed candidate
    actual_key = None
    for key, _ in sorted_candidates:
        if installed.get(key):
            actual_key = key
            break

    media_names = ", ".join(f.name for f in video_files)
    print(f"\n[Media Player Router] Media ({len(video_files)} files): {media_names}")
    print(f" * Target Intent: {args.intent}")
    if meta.get("duration"):
        print(f" * Duration: {meta['duration']}s | Codec: {meta['codec']} | Resolution: {meta['width']}x{meta['height']}")
    print(f" * Optimal Player Choice: {PLAYERS[top_key]['name']} ({top_score} pts)")

    if args.dry_run:
        print("\n--- Dry Run Evaluation ---")
        for k, sc in sorted_candidates:
            st = "[INSTALLED]" if installed.get(k) else "[NOT INSTALLED]"
            print(f"  - {PLAYERS[k]['name']} ({k}): {sc} pts {st}")

        if top_key != actual_key and actual_key:
            print(f"\n[Fallback Action] Top pick '{top_key}' not found. Routing to installed '{actual_key}'.")
            print(f"[Tip] To install top pick: winget install {PLAYERS[top_key]['winget_id']}")
        elif not actual_key:
            print("\n[Fallback Action] No open-source players found. Routing to Windows system default.")
        else:
            print(f"\n[Execution Action] Ready to launch {PLAYERS[actual_key]['name']} directly.")
        return

    # Execution path
    target_player_key = actual_key
    if not target_player_key:
        print("\n[Notice] No dedicated open-source media player detected.")
        print("[Tip] Recommended: winget install VideoLAN.VLC or winget install shinchiro.mpv")
        print("[Fallback] Launching system default player via PowerShell Start-Process...")
        for vf in video_files:
            subprocess.run(["powershell.exe", "-NoProfile", "-Command", f'Start-Process -FilePath "{vf}"'])
        return

    exe_path = installed[target_player_key]
    player_meta = PLAYERS[target_player_key]

    player_args = list(player_meta["default_args"])
    if args.loop or args.intent == "animation":
        if player_meta.get("loop_arg"):
            player_args.append(player_meta["loop_arg"])

    if target_player_key != top_key:
        print(f"[Routing] {PLAYERS[top_key]['name']} not installed.")
        print(f"[Routing] Falling back to installed {player_meta['name']} -> {exe_path}")
        print(f"[Tip] Run 'winget install {PLAYERS[top_key]['winget_id']}' for optimal experience.\n")
    else:
        print(f"[Routing] Launching {player_meta['name']} -> {exe_path}\n")

    launch_player_detached(exe_path, player_args, video_files)
    print(f"[Success] Playback launched for {len(video_files)} video(s) in detached background process.")


if __name__ == "__main__":
    main()
