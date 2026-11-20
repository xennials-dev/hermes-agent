"""
Techstarz101 — Master Command Portal (Root Dashboard for All 15 Core Services)
Runs on http://localhost:7860

Capabilities:
  - Indexes all 15 Techstarz101 services + 100+ standalone open-source tools
  - Concurrent real-time LIVE/OFFLINE health probes for every service hub
  - On-demand auto-launch: clicking any service card (/s/<num>) spawns its hub
    process if stopped, waits for HTTP 200, and redirects straight into the app
  - One-click Start All Hubs / Stop Managed Hubs
  - Global tool search across all Stack A & Stack B standalone Docker repos
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

PORTAL_DIR = Path(__file__).resolve().parent
SERVICES_ROOT = PORTAL_DIR.parent
STATIC_DIR = PORTAL_DIR / "static"

SERVICES_CATALOG = [
    {
        "num": "01",
        "id": "TS101-SRV-01",
        "name": "Lead Generator (<60s)",
        "category": "Growth & Sales",
        "tagline": "Sub-60s B2B lead discovery, enrichment & outreach automation",
        "icon": "🎯",
        "folder": "01_lead_generator",
        "entry": "app.py",
        "port": 7865,
        "url": "http://localhost:7865",
        "tool_ports": "Built-in",
        "external": False,
    },
    {
        "num": "02",
        "id": "TS101-SRV-02",
        "name": "Social Media Closer",
        "category": "Growth & Sales",
        "tagline": "Autonomous DM/comment closing, CRM sync & omnichannel booking",
        "icon": "💬",
        "folder": "02_social_media_closer",
        "entry": "hub/app.py",
        "port": 7866,
        "url": "http://localhost:7866",
        "tool_ports": ":5100–:5230",
        "external": False,
    },
    {
        "num": "03",
        "id": "TS101-SRV-03",
        "name": "Marketing Campaigns",
        "category": "Growth & Sales",
        "tagline": "Autonomous growth, multi-angle A/B testing & attribution",
        "icon": "📣",
        "folder": "03_marketing_campaigns",
        "entry": "hub/app.py",
        "port": 7867,
        "url": "http://localhost:7867",
        "tool_ports": ":5300–:5430",
        "external": False,
    },
    {
        "num": "04",
        "id": "TS101-SRV-04",
        "name": "Brand & Web Launch",
        "category": "Creative & Web",
        "tagline": "From initial idea to live deployed web, CMS & analytics",
        "icon": "🚀",
        "folder": "04_brand_web_launch",
        "entry": "hub/app.py",
        "port": 7868,
        "url": "http://localhost:7868",
        "tool_ports": ":5500–:5630",
        "external": False,
    },
    {
        "num": "05",
        "id": "TS101-SRV-05",
        "name": "Autonomous AI Employee",
        "category": "Operations & Agents",
        "tagline": "Full-stack AI teammate, executive orchestrator & multi-agent workflows",
        "icon": "🤖",
        "folder": "05_autonomous_ai_employee",
        "entry": "hub/app.py",
        "port": 7869,
        "url": "http://localhost:7869",
        "tool_ports": ":5700–:5830",
        "external": False,
    },
    {
        "num": "06",
        "id": "TS101-SRV-06",
        "name": "AI Opportunity Audit ($750)",
        "category": "Operations & Agents",
        "tagline": "360° operational ROI audit, bottleneck mapping & 100% build credit",
        "icon": "🧭",
        "folder": "06_ai_opportunity_audit",
        "entry": "hub/app.py",
        "port": 7870,
        "url": "http://localhost:7870",
        "tool_ports": ":5900–:6030",
        "external": False,
    },
    {
        "num": "07",
        "id": "TS101-SRV-07",
        "name": "Listmonk Email Marketing",
        "category": "Growth & Sales",
        "tagline": "Self-hosted high-throughput email engine with zero contact tax",
        "icon": "✉️",
        "folder": "07_listmonk_email",
        "entry": "hub/app.py",
        "port": 7871,
        "url": "http://localhost:7871",
        "tool_ports": ":6100–:6230",
        "external": False,
    },
    {
        "num": "08",
        "id": "TS101-SRV-08",
        "name": "Postiz Social Hub",
        "category": "Growth & Sales",
        "tagline": "Buffer alternative for 30+ social networks with AI (Live on VPS)",
        "icon": "📱",
        "folder": None,
        "entry": None,
        "port": 4200,
        "url": "http://2.25.238.185:4200",
        "tool_ports": "VPS :4200",
        "external": True,
    },
    {
        "num": "09",
        "id": "TS101-SRV-09",
        "name": "WhisperX Speech AI",
        "category": "Voice & Media AI",
        "tagline": "Speaker-diarized transcription, word timestamps & SRT/VTT subtitles",
        "icon": "🎙️",
        "folder": "09_whisperx_speech_ai",
        "entry": "hub/app.py",
        "port": 7872,
        "url": "http://localhost:7872",
        "tool_ports": ":6300–:6430",
        "external": False,
    },
    {
        "num": "10",
        "id": "TS101-SRV-10",
        "name": "Pipecat 24/7 Voice AI",
        "category": "Voice & Media AI",
        "tagline": "Sub-800ms autonomous phone receptionist, SIP PBX & live Cal.com booking",
        "icon": "📞",
        "folder": "10_pipecat_voice_ai",
        "entry": "hub/app.py",
        "port": 7873,
        "url": "http://localhost:7873",
        "tool_ports": ":6500–:6630",
        "external": False,
    },
    {
        "num": "11",
        "id": "TS101-SRV-11",
        "name": "Docling Document RAG",
        "category": "Data & Intelligence",
        "tagline": "93.6% table structure accuracy, layout-aware PDF parser & hybrid RAG",
        "icon": "📄",
        "folder": "11_docling_document_rag",
        "entry": "hub/app.py",
        "port": 7874,
        "url": "http://localhost:7874",
        "tool_ports": ":6700–:6830",
        "external": False,
    },
    {
        "num": "12",
        "id": "TS101-SRV-12",
        "name": "ComfyUI Creative Engine",
        "category": "Creative & Web",
        "tagline": "Automated Flux/SDXL product shoots, cutouts & 9:16 video reel pipeline",
        "icon": "🎨",
        "folder": "12_comfyui_creative_engine",
        "entry": "hub/app.py",
        "port": 7876,
        "url": "http://localhost:7876",
        "tool_ports": ":6900–:7030",
        "external": False,
    },
    {
        "num": "13",
        "id": "TS101-SRV-13",
        "name": "Browser-Use Web Agent",
        "category": "Operations & Agents",
        "tagline": "Zero-API portal RPA, isolated CDP sandboxes & live noVNC 2FA handoff",
        "icon": "🌐",
        "folder": "13_browser_use_web_agent",
        "entry": "hub/app.py",
        "port": 7877,
        "url": "http://localhost:7877",
        "tool_ports": ":7100–:7230",
        "external": False,
    },
    {
        "num": "14",
        "id": "TS101-SRV-14",
        "name": "Claude Finance Agent Suite",
        "category": "Data & Intelligence",
        "tagline": "Official 10-agent IB, PE, DCF/LBO & OpenSanctions KYC/AML architecture",
        "icon": "🏦",
        "folder": "14_claude_finance_agent_suite",
        "entry": "hub/app.py",
        "port": 7878,
        "url": "http://localhost:7878",
        "tool_ports": ":7300–:7430",
        "external": False,
    },
    {
        "num": "15",
        "id": "TS101-SRV-15",
        "name": "Cyber Security Package",
        "category": "Security & Infra",
        "tagline": "SAST, authorized DAST, Trivy CVEs, CrowdSec IPS, Vaultwarden & SOAR",
        "icon": "🛡️",
        "folder": "15_cyber_security_package",
        "entry": "hub/app.py",
        "port": 7879,
        "url": "http://localhost:7879",
        "tool_ports": ":7500–:7630",
        "external": False,
    },
]

SERVICE_MAP: Dict[str, dict] = {s["num"]: s for s in SERVICES_CATALOG}
MANAGED_PROCS: Dict[str, subprocess.Popen] = {}
PROC_LOCK = threading.Lock()

app = FastAPI(title="Techstarz101 — Master Command Portal")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def _probe_url(url: str, timeout: float = 0.6) -> bool:
    try:
        probe = url.replace("http://localhost", "http://127.0.0.1")
        req = urllib.request.Request(probe, headers={"User-Agent": "Techstarz101-MasterPortal/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status < 500
    except urllib.error.HTTPError as e:
        return e.code < 500
    except Exception:
        return False


def _load_all_tools() -> List[dict]:
    all_tools: List[dict] = []
    for svc in SERVICES_CATALOG:
        if not svc["folder"]:
            continue
        reg_path = SERVICES_ROOT / svc["folder"] / "tools" / "registry.json"
        if not reg_path.exists():
            continue
        try:
            reg = json.loads(reg_path.read_text(encoding="utf-8"))
            for tid, meta in reg.get("tools", {}).items():
                all_tools.append(
                    {
                        "service_num": svc["num"],
                        "service_name": svc["name"],
                        "hub_url": svc["url"],
                        "tool_id": tid,
                        "name": meta.get("name", tid),
                        "role": meta.get("role", ""),
                        "icon": meta.get("icon", "🔧"),
                        "stack": meta.get("stack", "A"),
                        "license": meta.get("license", "Open Source"),
                        "repo": meta.get("repo", ""),
                        "direct_url": meta.get("url", ""),
                        "launch_url": f"{svc['url']}/t/{tid}",
                    }
                )
        except Exception:
            continue
    return all_tools


def _spawn_service(num: str) -> dict:
    svc = SERVICE_MAP.get(num)
    if not svc:
        raise HTTPException(status_code=404, detail=f"Unknown service: {num}")
    if svc["external"]:
        return {"ok": True, "state": "external", "url": svc["url"]}
    if _probe_url(svc["url"]):
        return {"ok": True, "state": "running", "url": svc["url"]}

    script_path = SERVICES_ROOT / svc["folder"] / svc["entry"]
    if not script_path.exists():
        raise HTTPException(status_code=404, detail=f"Entrypoint missing: {script_path}")

    with PROC_LOCK:
        existing = MANAGED_PROCS.get(num)
        if existing is None or existing.poll() is not None:
            proc = subprocess.Popen(
                [sys.executable, str(script_path)],
                cwd=str(SERVICES_ROOT.parent),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            MANAGED_PROCS[num] = proc
    return {"ok": True, "state": "starting", "url": svc["url"]}


# ---------------- Routes ---------------- #

@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    return HTMLResponse((STATIC_DIR / "index.html").read_text(encoding="utf-8"))


@app.get("/s/{num}", response_class=HTMLResponse)
def launch_service_page(num: str) -> HTMLResponse:
    if num not in SERVICE_MAP:
        raise HTTPException(status_code=404, detail=f"Unknown service: {num}")
    html = (STATIC_DIR / "launch_service.html").read_text(encoding="utf-8")
    return HTMLResponse(html.replace("__SVC_NUM__", num))


@app.get("/api/portal/catalog")
def api_catalog() -> JSONResponse:
    tools = _load_all_tools()
    by_svc: Dict[str, int] = {}
    for t in tools:
        by_svc[t["service_num"]] = by_svc.get(t["service_num"], 0) + 1
    enriched = []
    for svc in SERVICES_CATALOG:
        item = dict(svc)
        item["tool_count"] = by_svc.get(svc["num"], 0)
        enriched.append(item)
    return JSONResponse(
        {
            "portal": "Techstarz101 Master Command Portal",
            "vps_host": "2.25.238.185",
            "total_services": len(enriched),
            "total_standalone_tools": len(tools),
            "services": enriched,
        }
    )


@app.get("/api/portal/tools")
def api_tools() -> JSONResponse:
    return JSONResponse({"tools": _load_all_tools()})


@app.get("/api/portal/status")
def api_status() -> JSONResponse:
    with ThreadPoolExecutor(max_workers=len(SERVICES_CATALOG)) as pool:
        futs = {s["num"]: pool.submit(_probe_url, s["url"], 0.7 if not s["external"] else 1.2) for s in SERVICES_CATALOG}
        statuses = {}
        live_count = 0
        for s in SERVICES_CATALOG:
            up = futs[s["num"]].result()
            if up:
                live_count += 1
            statuses[s["num"]] = {
                "up": up,
                "url": s["url"],
                "external": s["external"],
                "managed": s["num"] in MANAGED_PROCS and MANAGED_PROCS[s["num"]].poll() is None,
            }
    return JSONResponse({"live_count": live_count, "total": len(SERVICES_CATALOG), "services": statuses})


@app.post("/api/portal/service/{num}/start")
def api_start_service(num: str) -> JSONResponse:
    return JSONResponse(_spawn_service(num))


@app.post("/api/portal/service/{num}/stop")
def api_stop_service(num: str) -> JSONResponse:
    with PROC_LOCK:
        proc = MANAGED_PROCS.pop(num, None)
        if proc and proc.poll() is None:
            proc.terminate()
            return JSONResponse({"ok": True, "stopped": num})
    return JSONResponse({"ok": True, "note": "Service was not spawned by this portal (or already stopped)."})


@app.post("/api/portal/start-all")
def api_start_all() -> JSONResponse:
    started = []
    for svc in SERVICES_CATALOG:
        if not svc["external"]:
            res = _spawn_service(svc["num"])
            if res.get("state") == "starting":
                started.append(svc["num"])
    return JSONResponse({"ok": True, "started": started})


@app.post("/api/portal/stop-all")
def api_stop_all() -> JSONResponse:
    stopped = []
    with PROC_LOCK:
        for num, proc in list(MANAGED_PROCS.items()):
            if proc.poll() is None:
                proc.terminate()
                stopped.append(num)
            MANAGED_PROCS.pop(num, None)
    return JSONResponse({"ok": True, "stopped": stopped})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7860)
