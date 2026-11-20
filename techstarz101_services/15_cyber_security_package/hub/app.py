"""
Techstarz101 — Service #15: Cyber Security Package Modular Hub
Serves:
  - Main Hub Dashboard on http://localhost:7879
  - Dedicated per-tool launch links: http://localhost:7879/t/<tool_id>
  - Live Defensive Security Posture, HTTP Header & Config Hardening Auditor:
      POST /api/sec/audit-posture
  - Stackable multi-tool boot & SOAR automation workflow downloads
"""

from __future__ import annotations

import json
import os
import re
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

app = FastAPI(title="Techstarz101 — Service #15: Cyber Security Package Hub")
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
                val = secrets.token_hex(24)
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


# ---------------- Live Defensive Security Posture & Config Auditor ---------------- #

class SecurityAuditRequest(BaseModel):
    asset_name: str = "app.techstarz101.com"
    headers_or_config: str


REQUIRED_HEADERS = [
    ("strict-transport-security", "HIGH", "Enable HSTS (max-age=31536000; includeSubDomains) to enforce HTTPS."),
    ("content-security-policy", "HIGH", "Define a strict Content-Security-Policy to mitigate XSS and script injection."),
    ("x-content-type-options", "MEDIUM", "Set X-Content-Type-Options: nosniff to prevent MIME-sniffing."),
    ("x-frame-options", "MEDIUM", "Set X-Frame-Options: DENY (or CSP frame-ancestors) to block clickjacking."),
    ("referrer-policy", "LOW", "Set Referrer-Policy: strict-origin-when-cross-origin to prevent URL token leakage."),
    ("permissions-policy", "LOW", "Restrict browser features (camera, mic, geolocation) via Permissions-Policy."),
]

SECRET_PATTERNS = [
    (r"AKIA[0-9A-Z]{16}", "CRITICAL", "Exposed AWS Access Key ID detected — rotate immediately and move to Vaultwarden (:7610)."),
    (r"(?i)(password|secret|api_key|token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{8,}", "HIGH", "Hardcoded secret/password detected in config — inject via encrypted secrets manager."),
    (r"(?i)privileged:\s*true", "CRITICAL", "Docker container running with privileged: true — drop capabilities and use least privilege."),
    (r"(?i)debug\s*[:=]\s*true", "MEDIUM", "Production DEBUG=true flag detected — disable verbose tracebacks in production."),
]


@app.post("/api/sec/audit-posture")
def audit_security_posture(req: SecurityAuditRequest) -> JSONResponse:
    """
    Offline defensive HTTP header, container config & secret-leakage auditor.
    Never performs unauthorized external scanning — inspects only user-supplied
    headers/configs and outputs prioritized fixes + Nginx hardening snippet.
    """
    raw = (req.headers_or_config or "").strip()
    if not raw:
        raise HTTPException(status_code=400, detail="headers_or_config is required.")

    low = raw.lower()
    findings = []
    score = 100

    for hdr, sev, fix in REQUIRED_HEADERS:
        if hdr not in low:
            findings.append({"category": "HTTP_HEADER", "severity": sev, "check": hdr, "remediation": fix})
            score -= 14 if sev == "HIGH" else (9 if sev == "MEDIUM" else 5)

    if "x-powered-by:" in low or "server: nginx/" in low or "server: apache/" in low:
        findings.append({
            "category": "INFO_DISCLOSURE",
            "severity": "LOW",
            "check": "server-version-banner",
            "remediation": "Hide server version banners (server_tokens off; proxy_hide_header X-Powered-By;).",
        })
        score -= 4

    for pat, sev, fix in SECRET_PATTERNS:
        if re.search(pat, raw):
            findings.append({"category": "CONFIG_SECRET", "severity": sev, "check": pat[:28], "remediation": fix})
            score -= 22 if sev == "CRITICAL" else (14 if sev == "HIGH" else 8)

    score = max(0, min(100, score))
    grade = "A+" if score >= 95 else ("A" if score >= 88 else ("B" if score >= 75 else ("C" if score >= 60 else ("D" if score >= 45 else "F"))))

    nginx_snippet = """# Techstarz101 Recommended Defensive Nginx Hardening
server_tokens off;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
add_header Content-Security-Policy "default-src 'self'; object-src 'none'; frame-ancestors 'none';" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "DENY" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;"""

    return JSONResponse(
        {
            "ok": True,
            "asset_name": req.asset_name,
            "score": score,
            "grade": grade,
            "findings_count": len(findings),
            "findings": findings,
            "nginx_hardening_snippet": nginx_snippet,
            "recommended_next_tools": ["owasp-zap (:7500)", "trivy-server (:7510)", "crowdsec-ips (:7600)", "vaultwarden-sec (:7610)"],
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7879)
