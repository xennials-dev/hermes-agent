#!/usr/bin/env python3
"""
Techstarz101 Service #06 - AI Opportunity Audit ($750): Modular Tool Stack Hub.

8 standalone open-source tool repos across Stack A & Stack B with dedicated
clickable launch links (http://localhost:7870/t/<id>), custom stack composer,
and a live 360° AI Opportunity Audit & ROI Scorecard Engine.

Run:  python techstarz101_services/06_ai_opportunity_audit/hub/app.py
Open: http://localhost:7870
"""

from __future__ import annotations

import json
import os
import re
import secrets
import shutil
import string
import subprocess
import threading
import time
import urllib.error
import urllib.request
from base64 import b64encode
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

HUB_DIR = Path(__file__).resolve().parent
SERVICE_DIR = HUB_DIR.parent
TOOLS_DIR = SERVICE_DIR / "tools"
STATIC_DIR = HUB_DIR / "static"
REPORTS_DIR = SERVICE_DIR / "generated_reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
REGISTRY = json.loads((TOOLS_DIR / "registry.json").read_text(encoding="utf-8"))
TOOLS: dict[str, dict[str, Any]] = REGISTRY["tools"]
HUB_PORT = 7870

DOCKER_DESKTOP_EXE = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "DockerDesktop" / "Docker Desktop.exe"
CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0

app = FastAPI(title="Techstarz101 - AI Opportunity Audit ($750) Hub")

_state: dict[str, dict[str, Any]] = {
    tid: {"phase": "idle", "log": deque(maxlen=300), "started_at": None, "error": None} for tid in TOOLS
}
_locks: dict[str, threading.Lock] = {tid: threading.Lock() for tid in TOOLS}


def docker_bin() -> str:
    return shutil.which("docker") or str(DOCKER_DESKTOP_EXE.parent / "resources" / "bin" / "docker.exe")


def run(cmd: list[str], cwd: Path | None = None, timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=timeout, creationflags=CREATE_NO_WINDOW,
    )


def docker_ready() -> bool:
    try:
        return run([docker_bin(), "info", "--format", "{{.ServerVersion}}"], timeout=3).returncode == 0
    except Exception:
        return False


def _gen(token: str) -> str:
    if token == "__LARAVEL_KEY__":
        return "base64:" + b64encode(secrets.token_bytes(32)).decode()
    if token == "__PASS16__":
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(16))
    m = re.fullmatch(r"__HEX(\d+)__", token)
    if m:
        return secrets.token_hex(int(m.group(1)) // 2)
    return token


def ensure_env(tid: str) -> Path:
    tool_dir = TOOLS_DIR / tid
    env_path = tool_dir / ".env"
    example = tool_dir / ".env.example"
    if not env_path.exists() and example.exists():
        text = re.sub(r"__[A-Z0-9_]+__", lambda m: _gen(m.group(0)), example.read_text(encoding="utf-8"))
        env_path.write_text(text, encoding="utf-8")
    return env_path


def compose_cmd(tid: str, *args: str) -> list[str]:
    tool_dir = TOOLS_DIR / tid
    return [docker_bin(), "compose", "--env-file", str(tool_dir / ".env"), "-f", str(tool_dir / "docker-compose.yml"), *args]


def http_up(url: str, timeout: float = 0.5) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ts101-hub"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status < 500
    except urllib.error.HTTPError as e:
        return e.code < 500
    except Exception:
        return False


def running_projects() -> dict[str, int]:
    try:
        res = run([docker_bin(), "ps", "--format", '{{.Label "com.docker.compose.project"}}'], timeout=8)
    except Exception:
        return {}
    counts: dict[str, int] = {}
    for line in res.stdout.splitlines():
        if line.strip():
            counts[line.strip()] = counts.get(line.strip(), 0) + 1
    return counts


def tool_status_all() -> dict[str, Any]:
    ready = docker_ready()
    projects = running_projects() if ready else {}
    with ThreadPoolExecutor(max_workers=len(TOOLS)) as pool:
        ups = dict(zip(TOOLS, pool.map(lambda t: http_up(TOOLS[t]["probe"]), TOOLS)))
    out = {}
    for tid, meta in TOOLS.items():
        st = _state[tid]
        containers = projects.get(f"ts101-{tid}", 0)
        if ups[tid]:
            phase = "running"
            st["phase"] = "running"
        elif st["phase"] in ("pulling", "booting", "stopping"):
            phase = st["phase"]
        elif containers:
            phase = "booting"
        else:
            phase = "error" if st["phase"] == "error" else "stopped"
        out[tid] = {
            "phase": phase, "containers": containers, "url": meta["url"],
            "error": st["error"], "started_at": st["started_at"],
        }
    return {"docker_ready": ready, "tools": out}


def _log(tid: str, line: str) -> None:
    _state[tid]["log"].append(f"[{time.strftime('%H:%M:%S')}] {line.rstrip()}")


def _start_worker(tid: str) -> None:
    st = _state[tid]
    with _locks[tid]:
        st.update(phase="pulling", error=None, started_at=time.time())
        st["log"].clear()
        if not docker_ready():
            st.update(phase="error", error="Docker engine is not running. Start Docker Desktop first.")
            _log(tid, st["error"])
            return
        ensure_env(tid)
        _log(tid, f"docker compose up -d ({TOOLS[tid]['name']})")
        proc = subprocess.Popen(
            compose_cmd(tid, "up", "-d", "--remove-orphans"), cwd=TOOLS_DIR / tid,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8",
            errors="replace", creationflags=CREATE_NO_WINDOW,
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            if line.strip():
                _log(tid, line)
        code = proc.wait()
        if code != 0:
            st.update(phase="error", error=f"docker compose exited with code {code}")
            return
        st["phase"] = "booting"
        _log(tid, "Containers started. Waiting for web app...")
        deadline = time.time() + 900
        while time.time() < deadline:
            if http_up(TOOLS[tid]["probe"]):
                st["phase"] = "running"
                _log(tid, f"READY -> {TOOLS[tid]['url']}")
                return
            time.sleep(4)
        st.update(phase="error", error="App did not answer within 15 minutes.")


def start_tool(tid: str) -> None:
    if tid not in TOOLS:
        raise HTTPException(404, f"unknown tool {tid}")
    if _locks[tid].locked():
        return
    threading.Thread(target=_start_worker, args=(tid,), daemon=True).start()


def stop_tool(tid: str) -> None:
    if tid not in TOOLS:
        raise HTTPException(404, f"unknown tool {tid}")

    def worker():
        st = _state[tid]
        st["phase"] = "stopping"
        ensure_env(tid)
        res = run(compose_cmd(tid, "down"), cwd=TOOLS_DIR / tid, timeout=180)
        for line in (res.stdout + res.stderr).splitlines():
            _log(tid, line)
        st.update(phase="stopped", started_at=None)

    threading.Thread(target=worker, daemon=True).start()


# ---------------------------------------------------------------- 360° AI Opportunity Audit & ROI Engine
def compute_audit_scorecard(company: str, team_size: int, saas_monthly: float, manual_hours_week: float, bottleneck: str) -> dict[str, Any]:
    annual_saas = round(saas_monthly * 12, 2)
    projected_saas_savings = round(annual_saas * 0.68, 2)
    reclaimed_hours_year = round(manual_hours_week * 50 * 0.72, 1)
    reclaimed_labor_value = round(reclaimed_hours_year * 55.0, 2)
    total_annual_impact = round(projected_saas_savings + reclaimed_labor_value, 2)
    audit_fee = 750.0
    full_build_price = 3920.0
    net_build_after_credit = full_build_price - audit_fee
    payback_days = max(4, int(round((net_build_after_credit / max(total_annual_impact, 1)) * 365)))

    roadmap = [
        {"phase": "Phase 1 · Days 1–7 (Quick-Win Wedge)", "focus": bottleneck,
         "deliverable": "Deploy sovereign open-source core replacing top 2 rented SaaS subscriptions + live webhook automation."},
        {"phase": "Phase 2 · Days 8–30 (Department Autonomy)", "focus": "CRM + Lead/DM Pipelines",
         "deliverable": "Wire Twenty CRM, n8n/Activepieces, and local Ollama agents with Human-in-the-Loop approval gates."},
        {"phase": "Phase 3 · Days 31–90 (Full 360° Sovereignty)", "focus": "Executive BI & Governance",
         "deliverable": "Roll out Langfuse/Metabase audit dashboards, zero-contact-tax email, and team SOP handoff."},
    ]

    report_md = (
        f"# 360° AI Opportunity Audit Report — {company}\n\n"
        f"- **Audit Investment:** $750 (100% credited toward full system build within 30 days)\n"
        f"- **Team Size:** {team_size} | **Primary Bottleneck:** {bottleneck}\n"
        f"- **Current Annual SaaS Spend:** ${annual_saas:,.2f}\n"
        f"- **Projected Annual SaaS Savings (68%):** ${projected_saas_savings:,.2f}\n"
        f"- **Reclaimed Manual Labor ({reclaimed_hours_year:,.0f} hrs/yr @ $55/hr):** ${reclaimed_labor_value:,.2f}\n"
        f"- **Total Projected Annual Impact:** **${total_annual_impact:,.2f}/yr**\n"
        f"- **Estimated Payback Period:** **{payback_days} days**\n\n"
        f"## 100% Audit Credit Math\n"
        f"- Full Sovereign System Build: $3,920\n"
        f"- Less 100% Credited AI Opportunity Audit: -$750\n"
        f"- **Net Balance Upon Upgrade:** **$3,170**\n\n"
        f"## 90-Day Implementation Roadmap\n"
        + "\n".join(f"- **{r['phase']} ({r['focus']}):** {r['deliverable']}" for r in roadmap)
        + "\n"
    )
    (REPORTS_DIR / "latest_audit_report.md").write_text(report_md, encoding="utf-8")

    return {
        "company": company,
        "team_size": team_size,
        "bottleneck": bottleneck,
        "annual_saas": annual_saas,
        "projected_saas_savings": projected_saas_savings,
        "reclaimed_hours_year": reclaimed_hours_year,
        "reclaimed_labor_value": reclaimed_labor_value,
        "total_annual_impact": total_annual_impact,
        "payback_days": payback_days,
        "audit_fee": audit_fee,
        "net_build_after_credit": net_build_after_credit,
        "roadmap": roadmap,
        "download_url": f"http://localhost:{HUB_PORT}/api/audit/download-report",
    }


compute_audit_scorecard("Midwest B2B Growth Co.", 18, 2800, 32, "Sales & Outbound SDR")


# ---------------------------------------------------------------- routes
@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    return HTMLResponse((STATIC_DIR / "index.html").read_text(encoding="utf-8"))


@app.get("/t/{tid}", response_class=HTMLResponse)
def tool_link(tid: str) -> HTMLResponse:
    if tid not in TOOLS:
        raise HTTPException(404, f"unknown tool {tid}")
    html = (STATIC_DIR / "launch.html").read_text(encoding="utf-8")
    meta = TOOLS[tid]
    return HTMLResponse(html.replace("__TOOL_ID__", tid).replace("__TOOL_NAME__", meta["name"])
                        .replace("__TOOL_ICON__", meta["icon"]).replace("__TOOL_URL__", meta["url"]))


@app.post("/api/audit/score")
async def api_audit_score(request: Request):
    b = await request.json()
    return compute_audit_scorecard(
        company=b.get("company") or "Midwest B2B Growth Co.",
        team_size=int(b.get("team_size") or 18),
        saas_monthly=float(b.get("saas_monthly") or 2800),
        manual_hours_week=float(b.get("manual_hours_week") or 32),
        bottleneck=b.get("bottleneck") or "Sales & Outbound SDR",
    )


@app.get("/api/audit/download-report")
def download_report():
    return FileResponse(REPORTS_DIR / "latest_audit_report.md", media_type="text/markdown", filename="techstarz101_360_ai_audit_report.md")


@app.get("/infographic.svg")
def infographic():
    return FileResponse(SERVICE_DIR / "architecture_infographic.svg", media_type="image/svg+xml")


@app.get("/video/{name}")
def video(name: str):
    path = SERVICE_DIR / "video" / Path(name).name
    if not path.exists():
        raise HTTPException(404)
    return FileResponse(path, media_type="video/mp4")


@app.get("/automations/{name}")
def automation_file(name: str):
    path = SERVICE_DIR / "automations" / Path(name).name
    if not path.exists():
        raise HTTPException(404)
    return FileResponse(path, filename=path.name)


@app.get("/api/registry")
def api_registry():
    tools = {tid: {**meta, "link": f"http://localhost:{HUB_PORT}/t/{tid}"} for tid, meta in TOOLS.items()}
    return {"service": REGISTRY["service"], "stacks": REGISTRY["stacks"], "tools": tools}


@app.get("/api/status")
def api_status():
    return tool_status_all()


@app.post("/api/tools/{tid}/start")
def api_start(tid: str):
    start_tool(tid)
    return {"ok": True, "tool": tid}


@app.post("/api/tools/{tid}/stop")
def api_stop(tid: str):
    stop_tool(tid)
    return {"ok": True, "tool": tid}


@app.get("/api/tools/{tid}/logs")
def api_logs(tid: str):
    if tid not in TOOLS:
        raise HTTPException(404)
    return {"hub": list(_state[tid]["log"])}


@app.post("/api/stack/start")
async def api_stack_start(request: Request):
    body = await request.json()
    ids = body.get("tools") or REGISTRY["stacks"].get(body.get("stack", ""), {}).get("tools", [])
    for tid in ids:
        start_tool(tid)
    return {"ok": True, "started": ids}


@app.post("/api/stack/stop")
async def api_stack_stop(request: Request):
    body = await request.json()
    ids = body.get("tools") or REGISTRY["stacks"].get(body.get("stack", ""), {}).get("tools", [])
    for tid in ids:
        stop_tool(tid)
    return {"ok": True, "stopped": ids}


@app.post("/api/docker/start")
def api_docker_start():
    if docker_ready():
        return {"ok": True, "detail": "Docker engine already running."}
    if DOCKER_DESKTOP_EXE.exists():
        subprocess.Popen([str(DOCKER_DESKTOP_EXE)], creationflags=CREATE_NO_WINDOW)
        return {"ok": True, "detail": "Docker Desktop is starting..."}
    return JSONResponse({"ok": False, "detail": "Docker Desktop not found"}, status_code=404)


if __name__ == "__main__":
    for tid in TOOLS:
        ensure_env(tid)
    print(f"Techstarz101 AI Opportunity Audit ($750) hub -> http://localhost:{HUB_PORT}")
    uvicorn.run(app, host="127.0.0.1", port=HUB_PORT, log_level="info")
