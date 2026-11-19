"""
Techstarz101 — Service #12: ComfyUI Creative Engine Modular Hub
Serves:
  - Main Hub Dashboard on http://localhost:7876
  - Dedicated per-tool launch links: http://localhost:7876/t/<tool_id>
  - Live ComfyUI Node Workflow & Multi-Format Product Creative Generator:
      POST /api/creative/generate-workflow
  - Stackable multi-tool boot & automation workflow downloads
"""

from __future__ import annotations

import json
import os
import random
import secrets
import shutil
import subprocess
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = ROOT / "tools"
REGISTRY_PATH = TOOLS_DIR / "registry.json"
AUTOMATIONS_DIR = ROOT / "automations"
VIDEO_DIR = ROOT / "video"
STATIC_DIR = Path(__file__).resolve().parent / "static"

REGISTRY = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
TOOLS: Dict[str, dict] = REGISTRY["tools"]
STACKS: Dict[str, dict] = REGISTRY["stacks"]

BOOT_LOGS: Dict[str, List[str]] = {tid: [] for tid in TOOLS}
BOOT_STATE: Dict[str, str] = {tid: "idle" for tid in TOOLS}
BOOT_LOCK = threading.Lock()

app = FastAPI(title="Techstarz101 — Service #12: ComfyUI Creative Engine Hub")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def docker_ready() -> bool:
    if not shutil.which("docker"):
        return False
    try:
        r = subprocess.run(
            ["docker", "info"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=3,
        )
        return r.returncode == 0
    except Exception:
        return False


def http_up(url: str) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Techstarz101-Hub/1.0"})
        with urllib.request.urlopen(req, timeout=0.5) as resp:
            return resp.status < 500
    except urllib.error.HTTPError as e:
        return e.code < 500
    except Exception:
        return False


def ensure_env(tool_id: str) -> Path:
    tdir = TOOLS_DIR / tool_id
    env_file = tdir / ".env"
    example = tdir / ".env.example"
    if not env_file.exists() and example.exists():
        lines = []
        for raw in example.read_text(encoding="utf-8").splitlines():
            if "CHANGE_ME" in raw or "AUTO_GENERATED" in raw:
                key = raw.split("=", 1)[0]
                val = secrets.token_hex(24) if any(k in key for k in ("SECRET", "KEY", "PASS", "TOKEN")) else secrets.token_hex(16)
                lines.append(f"{key}={val}")
            else:
                lines.append(raw)
        env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return env_file


def _log(tool_id: str, msg: str) -> None:
    with BOOT_LOCK:
        buf = BOOT_LOGS.setdefault(tool_id, [])
        buf.append(msg)
        if len(buf) > 200:
            del buf[:-200]


def _boot_worker(tool_id: str) -> None:
    tdir = TOOLS_DIR / tool_id
    try:
        BOOT_STATE[tool_id] = "starting"
        _log(tool_id, f"[hub] Preparing standalone repo: tools/{tool_id}")
        ensure_env(tool_id)
        _log(tool_id, "[hub] Verified .env secrets (auto-generated if missing)")
        if not docker_ready():
            BOOT_STATE[tool_id] = "error"
            _log(tool_id, "[error] Docker Desktop is not running. Start Docker Desktop and retry.")
            return
        cmd = ["docker", "compose", "up", "-d"]
        _log(tool_id, f"[hub] Running: {' '.join(cmd)}")
        proc = subprocess.Popen(
            cmd,
            cwd=str(tdir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            _log(tool_id, line.rstrip())
        rc = proc.wait()
        if rc != 0:
            BOOT_STATE[tool_id] = "error"
            _log(tool_id, f"[error] docker compose exited with code {rc}")
            return
        probe = TOOLS[tool_id]["probe"]
        _log(tool_id, f"[hub] Waiting for health check: {probe}")
        for _ in range(90):
            if http_up(probe):
                BOOT_STATE[tool_id] = "running"
                _log(tool_id, f"[ready] {TOOLS[tool_id]['name']} is LIVE at {TOOLS[tool_id]['url']}")
                return
            time.sleep(1.5)
        BOOT_STATE[tool_id] = "starting"
        _log(tool_id, "[hub] Containers started; still warming up. Refresh in a few seconds.")
    except Exception as exc:
        BOOT_STATE[tool_id] = "error"
        _log(tool_id, f"[error] {exc}")


def _stop_worker(tool_id: str) -> None:
    tdir = TOOLS_DIR / tool_id
    try:
        _log(tool_id, "[hub] Stopping container stack...")
        subprocess.run(
            ["docker", "compose", "down"],
            cwd=str(tdir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=45,
        )
        BOOT_STATE[tool_id] = "idle"
        _log(tool_id, "[hub] Stopped.")
    except Exception as exc:
        _log(tool_id, f"[error] Stop failed: {exc}")


# ---------------- Routes ---------------- #

@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    return HTMLResponse((STATIC_DIR / "index.html").read_text(encoding="utf-8"))


@app.get("/t/{tool_id}", response_class=HTMLResponse)
def tool_launch_page(tool_id: str) -> HTMLResponse:
    if tool_id not in TOOLS:
        raise HTTPException(status_code=404, detail=f"Unknown tool: {tool_id}")
    html = (STATIC_DIR / "launch.html").read_text(encoding="utf-8")
    return HTMLResponse(html.replace("__TOOL_ID__", tool_id))


@app.get("/api/registry")
def api_registry() -> JSONResponse:
    return JSONResponse(REGISTRY)


@app.get("/api/status")
def api_status() -> JSONResponse:
    with ThreadPoolExecutor(max_workers=len(TOOLS) + 1) as pool:
        dk_fut = pool.submit(docker_ready)
        probe_futs = {tid: pool.submit(http_up, meta["probe"]) for tid, meta in TOOLS.items()}
        dk = dk_fut.result()
        statuses = {}
        for tid, meta in TOOLS.items():
            up = probe_futs[tid].result()
            state = "running" if up else BOOT_STATE.get(tid, "idle")
            if up:
                BOOT_STATE[tid] = "running"
            statuses[tid] = {
                "up": up,
                "state": state,
                "url": meta["url"],
                "logs": BOOT_LOGS.get(tid, [])[-40:],
            }
    return JSONResponse({"docker_ready": dk, "tools": statuses})


@app.post("/api/tools/{tool_id}/start")
def start_tool(tool_id: str) -> JSONResponse:
    if tool_id not in TOOLS:
        raise HTTPException(status_code=404, detail=f"Unknown tool: {tool_id}")
    if http_up(TOOLS[tool_id]["probe"]):
        BOOT_STATE[tool_id] = "running"
        return JSONResponse({"ok": True, "state": "running", "url": TOOLS[tool_id]["url"]})
    if BOOT_STATE.get(tool_id) != "starting":
        BOOT_LOGS[tool_id] = []
        threading.Thread(target=_boot_worker, args=(tool_id,), daemon=True).start()
    return JSONResponse({"ok": True, "state": "starting"})


@app.post("/api/tools/{tool_id}/stop")
def stop_tool(tool_id: str) -> JSONResponse:
    if tool_id not in TOOLS:
        raise HTTPException(status_code=404, detail=f"Unknown tool: {tool_id}")
    threading.Thread(target=_stop_worker, args=(tool_id,), daemon=True).start()
    return JSONResponse({"ok": True, "state": "stopping"})


class BatchRequest(BaseModel):
    tools: List[str]


@app.post("/api/stack/start")
def start_stack(req: BatchRequest) -> JSONResponse:
    started = []
    for tid in req.tools:
        if tid in TOOLS and not http_up(TOOLS[tid]["probe"]) and BOOT_STATE.get(tid) != "starting":
            BOOT_LOGS[tid] = []
            threading.Thread(target=_boot_worker, args=(tid,), daemon=True).start()
            started.append(tid)
    return JSONResponse({"ok": True, "started": started})


@app.post("/api/stack/stop")
def stop_stack(req: BatchRequest) -> JSONResponse:
    for tid in req.tools:
        if tid in TOOLS:
            threading.Thread(target=_stop_worker, args=(tid,), daemon=True).start()
    return JSONResponse({"ok": True, "stopped": req.tools})


@app.post("/api/docker/launch")
def launch_docker_desktop() -> JSONResponse:
    candidates = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "DockerDesktop" / "Docker Desktop.exe",
        Path("C:/Program Files/Docker/Docker/Docker Desktop.exe"),
    ]
    for exe in candidates:
        if exe.exists():
            subprocess.Popen([str(exe)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return JSONResponse({"ok": True, "launched": str(exe)})
    return JSONResponse({"ok": False, "error": "Docker Desktop executable not found"}, status_code=404)


@app.get("/infographic.svg")
def infographic() -> FileResponse:
    return FileResponse(str(ROOT / "architecture_infographic.svg"), media_type="image/svg+xml")


@app.get("/video/{filename}")
def serve_video(filename: str) -> FileResponse:
    p = VIDEO_DIR / filename
    if not p.exists():
        raise HTTPException(status_code=404, detail="Video not found")
    return FileResponse(str(p), media_type="video/mp4")


@app.get("/automations/{filename}")
def serve_automation(filename: str) -> FileResponse:
    p = AUTOMATIONS_DIR / filename
    if not p.exists():
        raise HTTPException(status_code=404, detail="Automation not found")
    return FileResponse(str(p), media_type="application/json")


# ---------------- Live ComfyUI Workflow & Ad Creative Generator ---------------- #

class CreativeWorkflowRequest(BaseModel):
    product_name: str = "Matte Black Wireless Studio Headphones"
    aesthetic: str = "luxury-dark"  # luxury-dark | studio-minimal | neon-street | editorial-warm
    aspect_ratio: str = "1:1"  # 1:1 | 9:16 | 16:9
    batch_size: int = 4


AESTHETICS = {
    "luxury-dark": {
        "style": "dramatic obsidian slate pedestal, subtle rim lighting, razor-sharp commercial reflections, 85mm macro lens, Phase One XF editorial photography",
        "negative": "cluttered background, cheap plastic, watermark, text overlay, blurry edges, oversaturated",
        "cfg": 4.0,
        "steps": 28,
        "checkpoint": "flux1-dev-fp8.safetensors",
    },
    "studio-minimal": {
        "style": "clean architectural cyclorama studio, soft diffused key light, gentle contact shadow, Apple-grade industrial design photography, crisp 8k detail",
        "negative": "harsh shadows, busy props, distorted geometry, watermark, text, grain",
        "cfg": 3.5,
        "steps": 24,
        "checkpoint": "flux1-dev-fp8.safetensors",
    },
    "neon-street": {
        "style": "urban night rain reflections, cyan and magenta rim highlights, cinematic shallow depth of field, high-energy streetwear campaign photography",
        "negative": "muddy darks, flat lighting, low-res, watermark, deformed logo, artifacts",
        "cfg": 4.5,
        "steps": 30,
        "checkpoint": "sd_xl_base_1.0.safetensors",
    },
    "editorial-warm": {
        "style": "golden-hour travertine stone surface, natural linen shadows, warm lifestyle magazine editorial, medium format film color science",
        "negative": "cold clinical lighting, neon colors, artificial CGI look, watermark, blurry",
        "cfg": 3.8,
        "steps": 26,
        "checkpoint": "flux1-dev-fp8.safetensors",
    },
}

ASPECTS = {
    "1:1": (1024, 1024, "Instagram Feed / Meta Square Ad"),
    "9:16": (768, 1344, "TikTok / Reels / Shorts Vertical"),
    "16:9": (1344, 768, "YouTube Hero / Landing Page Banner"),
}


@app.post("/api/creative/generate-workflow")
def generate_comfyui_workflow(req: CreativeWorkflowRequest) -> JSONResponse:
    """
    Generates a real, API-ready ComfyUI JSON node graph (POSTable to :6900/prompt)
    plus engineered positive/negative prompts, imgproxy resize URLs, and cost economics.
    """
    product = (req.product_name or "").strip()
    if not product:
        raise HTTPException(status_code=400, detail="product_name is required.")

    preset = AESTHETICS.get(req.aesthetic, AESTHETICS["luxury-dark"])
    width, height, placement = ASPECTS.get(req.aspect_ratio, ASPECTS["1:1"])
    seed = random.randint(100000, 999999999)
    batch = max(1, min(16, req.batch_size))

    positive_prompt = f"Commercial hero product shot of {product}, {preset['style']}, ultra-crisp focus, studio color grading"
    negative_prompt = preset["negative"]

    comfy_api_graph = {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "seed": seed,
                "steps": preset["steps"],
                "cfg": preset["cfg"],
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1.0,
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0],
            },
        },
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": preset["checkpoint"]}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": width, "height": height, "batch_size": batch}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": positive_prompt, "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": negative_prompt, "clip": ["4", 1]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": f"ts101_{req.aesthetic}", "images": ["8", 0]}},
    }

    return JSONResponse(
        {
            "ok": True,
            "product_name": product,
            "aesthetic": req.aesthetic,
            "placement": placement,
            "dimensions": f"{width}x{height}",
            "batch_size": batch,
            "positive_prompt": positive_prompt,
            "negative_prompt": negative_prompt,
            "endpoints": {
                "comfyui_submit": "POST http://localhost:6900/prompt",
                "rembg_cutout": "POST http://localhost:6910/api/remove",
                "minio_bucket": "http://localhost:6920/browser/creative-assets",
                "imgproxy_resize": f"http://localhost:6930/insecure/rs:fill:{width}:{height}/plain/http://host.docker.internal:6921/creative-assets/output.png@webp",
            },
            "economics": {
                "local_gpu_batch_cost_usd": round(batch * 0.002, 4),
                "commercial_saas_batch_cost_usd": round(batch * 0.35, 2),
                "savings_pct": 99.4,
            },
            "comfyui_api_workflow": comfy_api_graph,
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7876)
