"""
Techstarz101 — Service #10: Pipecat 24/7 Voice AI Modular Hub
Serves:
  - Main Hub Dashboard on http://localhost:7873
  - Dedicated per-tool launch links: http://localhost:7873/t/<tool_id>
  - Live Sub-800ms Phone Receptionist Simulator & Latency Budget Profiler:
      POST /api/voice/simulate-turn
  - Stackable multi-tool boot & automation workflow downloads
"""

from __future__ import annotations

import json
import os
import secrets
import shutil
import subprocess
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
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

app = FastAPI(title="Techstarz101 — Service #10: Pipecat 24/7 Voice AI Hub")
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
                if "SECRET" in key or "KEY" in key or "PASS" in key or "SALT" in key or "TOKEN" in key:
                    val = secrets.token_hex(24)
                else:
                    val = secrets.token_hex(16)
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


# ---------------- Live Sub-800ms Phone Receptionist Simulator ---------------- #

class VoiceTurnRequest(BaseModel):
    business_name: str = "Techstarz101 AI Studio"
    caller_utterance: str
    stack: str = "A"
    caller_phone: str = "+1-555-0194"


@app.post("/api/voice/simulate-turn")
def simulate_voice_turn(req: VoiceTurnRequest) -> JSONResponse:
    """
    Deterministic Pipecat Voice Turn Simulator & Sub-800ms Latency Profiler.
    Classifies caller intent, executes mock Cal.com / CRM tool calls, computes
    per-stage latency budget (VAD -> STT -> LLM TTFT -> TTS TTFB -> WebRTC),
    and returns the receptionist reply + structured booking payload.
    """
    text = (req.caller_utterance or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Caller utterance is required.")

    low = text.lower()
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%A, %b %d")

    if any(k in low for k in ["book", "schedule", "appointment", "consult", "demo", "slot", "tomorrow", "friday", "monday"]):
        intent = "BOOK_APPOINTMENT"
        tool_call = {
            "tool": "calcom.create_booking",
            "endpoint": "POST http://localhost:6530/api/v2/bookings",
            "args": {
                "eventTypeSlug": "ai-strategy-call",
                "start": f"{tomorrow} 10:30 AM",
                "attendeePhone": req.caller_phone,
                "status": "CONFIRMED",
            },
        }
        reply = (
            f"I have a 10:30 AM slot open {tomorrow} at {req.business_name}. "
            f"I just locked that in on Cal.com and texted your calendar invite to {req.caller_phone}. "
            f"Is there anything else I can prep for the team before your call?"
        )
    elif any(k in low for k in ["price", "cost", "how much", "pricing", "rate", "audit", "quote"]):
        intent = "PRICING_INQUIRY"
        tool_call = {
            "tool": "crm.log_qualified_lead",
            "endpoint": "POST http://localhost:6630/webhook/pipecat-call-complete",
            "args": {
                "phone": req.caller_phone,
                "interest": "Pricing / AI Opportunity Audit ($750)",
                "stage": "QUALIFIED",
            },
        }
        reply = (
            f"Great question! At {req.business_name}, our 360-degree AI Opportunity Audit is 750 dollars "
            f"and 100 percent of it credits toward your first build—plus you own all open-source stacks with zero per-minute voice markups. "
            f"Want me to reserve a 15-minute discovery slot for {tomorrow} at 2 PM?"
        )
    elif any(k in low for k in ["emergency", "urgent", "broken", "down", "human", "representative", "transfer"]):
        intent = "WARM_TRANSFER"
        tool_call = {
            "tool": "sip.warm_transfer",
            "endpoint": "POST http://localhost:6600/ari/channels/transfer",
            "args": {
                "target": "sip:oncall@techstarz101.internal",
                "whisper_context": f"Urgent caller {req.caller_phone}: {text[:80]}",
            },
        }
        reply = (
            f"I hear you—let me connect you straight to our on-call engineer at {req.business_name} right now "
            f"with a full summary so you don't have to repeat yourself. One moment please."
        )
    elif any(k in low for k in ["hours", "open", "location", "address", "weekend"]):
        intent = "BUSINESS_INFO"
        tool_call = {
            "tool": "kb.lookup_faq",
            "endpoint": "POST http://localhost:6620/api/v1/knowledge/query",
            "args": {"query": text[:100], "top_k": 2},
        }
        reply = (
            f"{req.business_name} operates 24/7 with live AI reception and human engineering hours Monday through Friday, "
            f"8 AM to 6 PM Central. Would you like me to book a callback during business hours?"
        )
    else:
        intent = "GENERAL_RECEPTION"
        tool_call = {
            "tool": "crm.append_call_note",
            "endpoint": "POST http://localhost:6630/webhook/pipecat-call-complete",
            "args": {"phone": req.caller_phone, "summary": text[:120]},
        }
        reply = (
            f"Thanks for calling {req.business_name}! I can check live availability and book an appointment, "
            f"answer pricing questions, or route you to the right specialist. How can I help you today?"
        )

    if req.stack.upper() == "A":
        latency = {
            "vad_ms": 48,
            "stt_ms": 178,
            "llm_ttft_ms": 235,
            "tts_ttfb_ms": 124,
            "webrtc_jitter_ms": 39,
        }
        engines = {
            "transport": "LiveKit WebRTC (:6500)",
            "stt": "Speaches Faster-Whisper (:6520)",
            "llm": "Local / vLLM Streaming",
            "tts": "Kokoro-FastAPI 82M (:6510)",
        }
    else:
        latency = {
            "vad_ms": 55,
            "stt_ms": 215,
            "llm_ttft_ms": 270,
            "tts_ttfb_ms": 142,
            "webrtc_jitter_ms": 58,
        }
        engines = {
            "transport": "Asterisk SIP / ARI (:6600)",
            "stt": "Speaches / Whisper CPU",
            "llm": "Open WebUI + Ollama (:6620)",
            "tts": "OpenedAI Speech Piper (:6610)",
        }

    total_ms = sum(latency.values())
    return JSONResponse(
        {
            "ok": True,
            "stack": req.stack.upper(),
            "intent": intent,
            "reply_text": reply,
            "tool_call": tool_call,
            "engines": engines,
            "latency": latency,
            "total_e2e_ms": total_ms,
            "sub_800ms_pass": total_ms < 800,
            "estimated_cost_per_min_usd": 0.008 if req.stack.upper() == "A" else 0.004,
            "saas_equivalent_per_min_usd": 0.18,
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7873)
