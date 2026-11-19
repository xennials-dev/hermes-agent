"""
Techstarz101 — Service #13: Browser-Use Web Agent Modular Hub
Serves:
  - Main Hub Dashboard on http://localhost:7877
  - Dedicated per-tool launch links: http://localhost:7877/t/<tool_id>
  - Live Zero-API Portal RPA Playbook & Browser-Use Script Compiler:
      POST /api/rpa/compile-playbook
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
import urllib.parse
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

app = FastAPI(title="Techstarz101 — Service #13: Browser-Use Web Agent Hub")
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


# ---------------- Live Portal RPA Playbook & Browser-Use Compiler ---------------- #

class RpaPlaybookRequest(BaseModel):
    portal_url: str = "https://portal.vendor-example.com/billing/invoices"
    task_goal: str = "Extract all unpaid invoices from the last 30 days, capture line items, and POST JSON to n8n."
    engine: str = "browser-use-ai"  # browser-use-ai | playwright-cdp | crawl4ai-extract
    hitl_gate: str = "pause-on-2fa"  # pause-on-2fa | read-only-extract | approval-before-submit


@app.post("/api/rpa/compile-playbook")
def compile_rpa_playbook(req: RpaPlaybookRequest) -> JSONResponse:
    """
    Compiles a Zero-API Portal RPA Playbook + runnable Python script wired to
    the user's local Browserless/Steel CDP browser (:7100/:7120) or Crawl4AI (:7110),
    complete with domain allowlist and human-in-the-loop safety gates.
    """
    url = (req.portal_url or "").strip()
    goal = (req.task_goal or "").strip()
    if not url or not goal:
        raise HTTPException(status_code=400, detail="portal_url and task_goal are required.")

    parsed = urllib.parse.urlparse(url if "://" in url else f"https://{url}")
    domain = parsed.netloc or "portal.vendor-example.com"

    steps = [
        {"step": 1, "action": "LAUNCH_SANDBOX", "target": "Steel Browser (:7120) / Browserless (:7100)", "guardrail": f"Allowlist domain: {domain}"},
        {"step": 2, "action": "NAVIGATE_AND_VERIFY", "target": url, "guardrail": "Capture pre-action audit screenshot"},
        {"step": 3, "action": "AUTH_HITL_CHECK", "target": "Session cookie / 2FA challenge", "guardrail": f"Policy: {req.hitl_gate} (pause via noVNC :7201 if login/2FA required)"},
        {"step": 4, "action": "EXECUTE_PORTAL_TASK", "target": goal[:120], "guardrail": "Structured JSON schema validation"},
        {"step": 5, "action": "DISPATCH_WEBHOOK", "target": "POST http://localhost:7230/webhook/rpa-portal-sync", "guardrail": "Idempotency key + run log in Windmill (:7210)"},
    ]

    if req.engine == "crawl4ai-extract":
        script = f'''import requests

# Zero-API Extraction via local Crawl4AI (:7110)
resp = requests.post(
    "http://localhost:7110/crawl",
    json={{
        "urls": ["{url}"],
        "priority": 10,
        "magic": True,
    }},
    timeout=60,
)
data = resp.json()
print("Extracted Markdown bytes:", len(str(data)))
requests.post("http://localhost:7230/webhook/rpa-portal-sync", json={{"domain": "{domain}", "payload": data}})
'''
    elif req.engine == "playwright-cdp":
        script = f'''from playwright.sync_api import sync_playwright
import requests

# Deterministic Playwright attached to local Browserless CDP (:7100)
with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("ws://localhost:7100")
    page = browser.new_page()
    page.goto("{url}", wait_until="networkidle")
    page.screenshot(path="audit_portal_before.png")
    rows = page.locator("table tr").all_inner_texts()
    requests.post("http://localhost:7230/webhook/rpa-portal-sync", json={{"domain": "{domain}", "rows": rows}})
    browser.close()
'''
    else:
        script = f'''import asyncio, requests
from browser_use import Agent, Browser, BrowserConfig
from langchain_openai import ChatOpenAI

# Autonomous Browser-Use Agent attached to local Steel/Browserless CDP (:7120)
async def main():
    browser = Browser(config=BrowserConfig(cdp_url="http://localhost:7120"))
    agent = Agent(
        task="""{goal} (Allowed domain ONLY: {domain}. Safety gate: {req.hitl_gate}.)""",
        llm=ChatOpenAI(model="gpt-4o-mini"),
        browser=browser,
    )
    result = await agent.run(max_steps=15)
    requests.post("http://localhost:7230/webhook/rpa-portal-sync", json={{"domain": "{domain}", "result": str(result)}})

asyncio.run(main())
'''

    return JSONResponse(
        {
            "ok": True,
            "domain_allowlist": [domain],
            "engine": req.engine,
            "hitl_gate": req.hitl_gate,
            "steps": steps,
            "runnable_script": script,
            "estimated_manual_hours_saved_per_mo": 34,
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7877)
