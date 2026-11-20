"""
Techstarz101 Workstation — Master Command Portal (Hybrid VPS + Local GPU)
Runs on http://127.0.0.1:7860 behind https://workstation.techstarz101.com

Capabilities:
  - Indexes all 15 Techstarz101 services + 105 directory links (83 unique open-source repos)
  - Direct-to-App Wake-on-Click (/open/{svc_num}/{tool_id}):
      * Phase 2 Always-On VPS Apps (n8n, Postiz, Twenty CRM, Shlink) -> instant redirect
      * Wave 1 VPS Lightweight Apps -> auto-runs `docker compose up -d` + 30m idle auto-sleep
      * Wave 2/3 Hybrid Local GPU Tunnel Apps -> routes to reverse-tunneled local Docker app
  - Zero `localhost` redirect leaks, zero browser ERR_CONNECTION_TIMED_OUT dead links
"""

from __future__ import annotations

import json
import os
import secrets
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

PORTAL_DIR = Path(__file__).resolve().parent
SERVICES_ROOT = PORTAL_DIR.parent
STATIC_DIR = PORTAL_DIR / "static"
WORKSTATION_DOMAIN = os.environ.get("WORKSTATION_DOMAIN", "workstation.2-25-238-185.sslip.io")
FALLBACK_BASE = os.environ.get("WORKSTATION_FALLBACK_BASE", "https://techstarz101.com")
IDLE_SLEEP_SECONDS = int(os.environ.get("IDLE_SLEEP_SECONDS", "1800"))  # 30 minutes

SERVICES_CATALOG = [
    {"num": "01", "id": "TS101-SRV-01", "name": "Lead Generator (<60s)", "category": "Growth & Sales", "tagline": "Sub-60s B2B lead discovery, enrichment & outreach automation", "icon": "🎯", "folder": "01_lead_generator", "entry": "app.py", "port": 7865, "tool_ports": "Built-in", "external": False},
    {"num": "02", "id": "TS101-SRV-02", "name": "Social Media Closer", "category": "Growth & Sales", "tagline": "Autonomous DM/comment closing, CRM sync & omnichannel booking", "icon": "💬", "folder": "02_social_media_closer", "entry": "hub/app.py", "port": 7866, "tool_ports": ":5100–:5230", "external": False},
    {"num": "03", "id": "TS101-SRV-03", "name": "Marketing Campaigns", "category": "Growth & Sales", "tagline": "Autonomous growth, multi-angle A/B testing & attribution", "icon": "📣", "folder": "03_marketing_campaigns", "entry": "hub/app.py", "port": 7867, "tool_ports": ":5300–:5430", "external": False},
    {"num": "04", "id": "TS101-SRV-04", "name": "Brand & Web Launch", "category": "Creative & Web", "tagline": "From initial idea to live deployed web, CMS & analytics", "icon": "🚀", "folder": "04_brand_web_launch", "entry": "hub/app.py", "port": 7868, "tool_ports": ":5500–:5630", "external": False},
    {"num": "05", "id": "TS101-SRV-05", "name": "Autonomous AI Employee", "category": "Operations & Agents", "tagline": "Full-stack AI teammate, executive orchestrator & multi-agent workflows", "icon": "🤖", "folder": "05_autonomous_ai_employee", "entry": "hub/app.py", "port": 7869, "tool_ports": ":5700–:5830", "external": False},
    {"num": "06", "id": "TS101-SRV-06", "name": "AI Opportunity Audit ($750)", "category": "Operations & Agents", "tagline": "360° operational ROI audit, bottleneck mapping & 100% build credit", "icon": "🧭", "folder": "06_ai_opportunity_audit", "entry": "hub/app.py", "port": 7870, "tool_ports": ":5900–:6030", "external": False},
    {"num": "07", "id": "TS101-SRV-07", "name": "Listmonk Email Marketing", "category": "Growth & Sales", "tagline": "Self-hosted high-throughput email engine with zero contact tax", "icon": "✉️", "folder": "07_listmonk_email", "entry": "hub/app.py", "port": 7871, "tool_ports": ":6100–:6230", "external": False},
    {"num": "08", "id": "TS101-SRV-08", "name": "Postiz Social Hub", "category": "Growth & Sales", "tagline": "Buffer alternative for 30+ social networks with AI (Live on VPS)", "icon": "📱", "folder": None, "entry": None, "port": 4200, "url": "https://postiz.techstarz101.com", "tool_ports": "VPS :4200", "external": True},
    {"num": "09", "id": "TS101-SRV-09", "name": "WhisperX Speech AI", "category": "Voice & Media AI", "tagline": "Speaker-diarized transcription, word timestamps & SRT/VTT subtitles", "icon": "🎙️", "folder": "09_whisperx_speech_ai", "entry": "hub/app.py", "port": 7872, "tool_ports": ":6300–:6430", "external": False},
    {"num": "10", "id": "TS101-SRV-10", "name": "Pipecat 24/7 Voice AI", "category": "Voice & Media AI", "tagline": "Sub-800ms autonomous phone receptionist, SIP PBX & live Cal.com booking", "icon": "📞", "folder": "10_pipecat_voice_ai", "entry": "hub/app.py", "port": 7873, "tool_ports": ":6500–:6630", "external": False},
    {"num": "11", "id": "TS101-SRV-11", "name": "Docling Document RAG", "category": "Data & Intelligence", "tagline": "93.6% table structure accuracy, layout-aware PDF parser & hybrid RAG", "icon": "📄", "folder": "11_docling_document_rag", "entry": "hub/app.py", "port": 7874, "tool_ports": ":6700–:6830", "external": False},
    {"num": "12", "id": "TS101-SRV-12", "name": "ComfyUI Creative Engine", "category": "Creative & Web", "tagline": "Automated Flux/SDXL product shoots, cutouts & 9:16 video reel pipeline", "icon": "🎨", "folder": "12_comfyui_creative_engine", "entry": "hub/app.py", "port": 7876, "tool_ports": ":6900–:7030", "external": False},
    {"num": "13", "id": "TS101-SRV-13", "name": "Browser-Use Web Agent", "category": "Operations & Agents", "tagline": "Zero-API portal RPA, isolated CDP sandboxes & live noVNC 2FA handoff", "icon": "🌐", "folder": "13_browser_use_web_agent", "entry": "hub/app.py", "port": 7877, "tool_ports": ":7100–:7230", "external": False},
    {"num": "14", "id": "TS101-SRV-14", "name": "Claude Finance Agent Suite", "category": "Data & Intelligence", "tagline": "Official 10-agent IB, PE, DCF/LBO & OpenSanctions KYC/AML architecture", "icon": "🏦", "folder": "14_claude_finance_agent_suite", "entry": "hub/app.py", "port": 7878, "tool_ports": ":7300–:7430", "external": False},
    {"num": "15", "id": "TS101-SRV-15", "name": "Cyber Security Package", "category": "Security & Infra", "tagline": "SAST, authorized DAST, Trivy CVEs, CrowdSec IPS, Vaultwarden & SOAR", "icon": "🛡️", "folder": "15_cyber_security_package", "entry": "hub/app.py", "port": 7879, "tool_ports": ":7500–:7630", "external": False},
]

# Phase 2: Shared Always-On Live VPS Containers (0 MB extra RAM — powers 12 directory links immediately)
SHARED_LIVE_OVERRIDES: Dict[str, dict] = {
    "https://github.com/n8n-io/n8n": {
        "slug": "n8n",
        "tier": "vps_live",
        "local_port": 5679,
        "probe": "http://127.0.0.1:5679",
        "subdomain": f"https://n8n.{WORKSTATION_DOMAIN}",
        "path_proxy": "/apps/n8n/",
    },
    "https://github.com/gitroomhq/postiz-app": {
        "slug": "postiz",
        "tier": "vps_live",
        "local_port": 4200,
        "probe": "http://127.0.0.1:4200",
        "subdomain": "https://postiz.techstarz101.com",
        "path_proxy": "https://postiz.techstarz101.com",
    },
    "https://github.com/twentyhq/twenty": {
        "slug": "crm",
        "tier": "vps_live",
        "local_port": 3002,
        "probe": "http://127.0.0.1:3002",
        "subdomain": f"https://crm.{WORKSTATION_DOMAIN}",
        "path_proxy": "/apps/crm/",
    },
    "https://github.com/shlinkio/shlink": {
        "slug": "shlink",
        "tier": "vps_live",
        "local_port": 8090,
        "probe": "http://127.0.0.1:8090/rest/health",
        "subdomain": f"https://shlink.{WORKSTATION_DOMAIN}",
        "path_proxy": "/apps/shlink/",
    },
}

# Wave 1: Lightweight VPS Wake-on-Click Open-Source Apps (90–450 MB RAM, auto-sleep after 30m idle)
WAVE1_REPOS = {
    "https://github.com/gchq/cyberchef": ("cyberchef", 7620, "15_cyber_security_package/tools/cyberchef-soc"),
    "https://github.com/vrana/adminer": ("adminer", 6230, "07_listmonk_email/tools/adminer"),
    "https://github.com/axllent/mailpit": ("mailpit", 6120, "07_listmonk_email/tools/mailpit"),
    "https://github.com/dani-garcia/vaultwarden": ("vaultwarden", 7610, "15_cyber_security_package/tools/vaultwarden-sec"),
    "https://github.com/excalidraw/excalidraw": ("excalidraw", 6000, "06_ai_opportunity_audit/tools/excalidraw"),
    "https://github.com/louislam/uptime-kuma": ("uptime-kuma", 7530, "15_cyber_security_package/tools/uptime-kuma-sec"),
    "https://github.com/imgproxy/imgproxy": ("imgproxy", 6930, "12_comfyui_creative_engine/tools/imgproxy-cdn"),
    "https://github.com/reacherhq/check-if-email-exists": ("reacher", 6120, "07_listmonk_email/tools/reacher"),
    "https://github.com/meilisearch/meilisearch": ("meilisearch", 6330, "09_whisperx_speech_ai/tools/meilisearch"),
    "https://github.com/dgtlmoon/changedetection.io": ("changedetection", 7130, "13_browser_use_web_agent/tools/changedetection"),
    "https://github.com/minio/minio": ("minio", 6920, "12_comfyui_creative_engine/tools/minio-assets"),
    "https://github.com/go-gitea/gitea": ("gitea", 5630, "04_brand_web_launch/tools/gitea"),
    "https://github.com/knadh/listmonk": ("listmonk", 6100, "07_listmonk_email/tools/listmonk"),
    "https://github.com/qdrant/qdrant": ("qdrant", 6710, "11_docling_document_rag/tools/qdrant-rag"),
    "https://github.com/nocodb/nocodb": ("nocodb", 7410, "14_claude_finance_agent_suite/tools/nocodb-dealroom"),
    "https://github.com/docusealco/docuseal": ("docuseal", 6010, "06_ai_opportunity_audit/tools/docuseal"),
    "https://github.com/gristlabs/grist-core": ("grist", 6020, "06_ai_opportunity_audit/tools/grist"),
}

SERVICE_MAP: Dict[str, dict] = {s["num"]: s for s in SERVICES_CATALOG}
MANAGED_PROCS: Dict[str, subprocess.Popen] = {}
APP_BOOT_STATE: Dict[str, str] = {}
APP_BOOT_LOGS: Dict[str, List[str]] = {}
APP_LAST_TOUCH: Dict[str, float] = {}
APP_COMPOSE_DIRS: Dict[str, Path] = {}
LOCK = threading.Lock()

app = FastAPI(title="Techstarz101 Workstation — Master Command Portal")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def _probe_url(url: str, timeout: float = 0.6) -> bool:
    try:
        probe = url.replace("http://localhost", "http://127.0.0.1")
        req = urllib.request.Request(probe, headers={"User-Agent": "Techstarz101-Workstation/2.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status < 500
    except urllib.error.HTTPError as e:
        return e.code < 500
    except Exception:
        return False


def _ensure_env(tdir: Path) -> None:
    env_file = tdir / ".env"
    example = tdir / ".env.example"
    if not env_file.exists() and example.exists():
        lines = []
        for raw in example.read_text(encoding="utf-8").splitlines():
            if "CHANGE_ME" in raw or "AUTO_GENERATED" in raw:
                key = raw.split("=", 1)[0]
                lines.append(f"{key}={secrets.token_hex(20)}")
            else:
                lines.append(raw)
        env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


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
                repo_norm = meta.get("repo", "").rstrip("/").lower()
                raw_url = meta.get("url", "")
                port_part = 0
                try:
                    port_part = int(raw_url.split(":")[2].split("/")[0])
                except Exception:
                    pass

                if repo_norm in SHARED_LIVE_OVERRIDES:
                    ov = SHARED_LIVE_OVERRIDES[repo_norm]
                    tier = "vps_live"
                    slug = ov["slug"]
                    local_port = ov["local_port"]
                    probe = ov["probe"]
                    subdomain = ov["subdomain"]
                    compose_rel = ""
                elif repo_norm in WAVE1_REPOS:
                    slug, local_port, compose_rel = WAVE1_REPOS[repo_norm]
                    tier = "vps_wave1"
                    probe = f"http://127.0.0.1:{local_port}"
                    subdomain = f"https://{slug}.{WORKSTATION_DOMAIN}"
                else:
                    slug = tid.lower().replace("_", "-")
                    tier = "hybrid_tunnel"
                    local_port = port_part
                    probe = f"http://127.0.0.1:{local_port}" if local_port else ""
                    subdomain = f"https://{slug}.{WORKSTATION_DOMAIN}"
                    compose_rel = f"{svc['folder']}/tools/{tid}"

                all_tools.append(
                    {
                        "service_num": svc["num"],
                        "service_name": svc["name"],
                        "tool_id": tid,
                        "slug": slug,
                        "name": meta.get("name", tid),
                        "role": meta.get("role", ""),
                        "icon": meta.get("icon", "🔧"),
                        "stack": meta.get("stack", "A"),
                        "license": meta.get("license", "Open Source"),
                        "repo": meta.get("repo", ""),
                        "ram_mb": meta.get("ram_mb", 400),
                        "tier": tier,
                        "local_port": local_port,
                        "probe": probe,
                        "subdomain_url": subdomain,
                        "compose_rel": compose_rel,
                        "open_url": f"/open/{svc['num']}/{tid}",
                    }
                )
        except Exception:
            continue
    return all_tools


def _find_tool(svc_num: str, tool_id: str) -> Optional[dict]:
    for t in _load_all_tools():
        if t["service_num"] == svc_num and t["tool_id"] == tool_id:
            return t
    return None


def _app_log(key: str, msg: str) -> None:
    with LOCK:
        buf = APP_BOOT_LOGS.setdefault(key, [])
        buf.append(msg)
        if len(buf) > 150:
            del buf[:-150]


def _wake_wave1_worker(key: str, tool: dict) -> None:
    tdir = SERVICES_ROOT / tool["compose_rel"]
    try:
        APP_BOOT_STATE[key] = "starting"
        APP_LAST_TOUCH[key] = time.time()
        APP_COMPOSE_DIRS[key] = tdir
        _app_log(key, f"[workstation] Waking Wave 1 open-source app: {tool['name']} ({tool['compose_rel']})")
        _ensure_env(tdir)
        if not shutil.which("docker"):
            APP_BOOT_STATE[key] = "error"
            _app_log(key, "[error] Docker CLI not found on host.")
            return
        proc = subprocess.Popen(
            ["docker", "compose", "up", "-d"],
            cwd=str(tdir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            _app_log(key, line.rstrip())
        rc = proc.wait()
        if rc != 0:
            APP_BOOT_STATE[key] = "error"
            _app_log(key, f"[error] docker compose exited with code {rc}")
            return
        _app_log(key, f"[workstation] Waiting for health check on {tool['probe']} ...")
        for _ in range(90):
            if _probe_url(tool["probe"]):
                APP_BOOT_STATE[key] = "running"
                APP_LAST_TOUCH[key] = time.time()
                _app_log(key, f"[ready] {tool['name']} is LIVE!")
                return
            time.sleep(1.5)
        APP_BOOT_STATE[key] = "starting"
        _app_log(key, "[workstation] Container started; still warming up.")
    except Exception as exc:
        APP_BOOT_STATE[key] = "error"
        _app_log(key, f"[error] {exc}")


def _idle_reaper_loop() -> None:
    """Auto-sleeps Wave 1 on-demand containers after IDLE_SLEEP_SECONDS of inactivity to protect VPS RAM."""
    while True:
        time.sleep(120)
        now = time.time()
        for key, last_ts in list(APP_LAST_TOUCH.items()):
            if now - last_ts > IDLE_SLEEP_SECONDS and key in APP_COMPOSE_DIRS:
                tdir = APP_COMPOSE_DIRS.pop(key, None)
                APP_LAST_TOUCH.pop(key, None)
                APP_BOOT_STATE[key] = "idle"
                if tdir and tdir.exists():
                    try:
                        subprocess.run(
                            ["docker", "compose", "down"],
                            cwd=str(tdir),
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            timeout=45,
                        )
                    except Exception:
                        pass


threading.Thread(target=_idle_reaper_loop, daemon=True).start()


def _spawn_service(num: str) -> dict:
    svc = SERVICE_MAP.get(num)
    if not svc:
        raise HTTPException(status_code=404, detail=f"Unknown service: {num}")
    if svc["external"]:
        return {"ok": True, "state": "external", "url": svc["url"]}
    local_url = f"http://127.0.0.1:{svc['port']}"
    if _probe_url(local_url):
        return {"ok": True, "state": "running", "port": svc["port"]}
    script_path = SERVICES_ROOT / svc["folder"] / svc["entry"]
    if not script_path.exists():
        raise HTTPException(status_code=404, detail=f"Entrypoint missing: {script_path}")
    with LOCK:
        existing = MANAGED_PROCS.get(num)
        if existing is None or existing.poll() is not None:
            MANAGED_PROCS[num] = subprocess.Popen(
                [sys.executable, str(script_path)],
                cwd=str(SERVICES_ROOT.parent),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
    return {"ok": True, "state": "starting", "port": svc["port"]}


FALLBACK_PATHS: Dict[str, str] = {
    "n8n": f"{FALLBACK_BASE}/n8n/",
    "crm": f"{FALLBACK_BASE}/crm/",
    "shlink": f"{FALLBACK_BASE}/go/",
    "postiz": "https://postiz.techstarz101.com",
    "cyberchef": f"{FALLBACK_BASE}/apps/cyberchef/",
    "adminer": f"{FALLBACK_BASE}/apps/adminer/",
    "mailpit": f"{FALLBACK_BASE}/apps/mailpit/",
}

# Subdomains that currently hold issued Let's Encrypt certs on sslip.io
SSLIP_CERTIFIED_SLUGS = {"n8n", "crm", "shlink", "cyberchef", "adminer", "mailpit"}


def _resolve_public_app_url(req: Request, tool: dict) -> str:
    host = (req.headers.get("host") or "").split(":")[0].lower()
    slug = tool["slug"]
    if slug == "postiz":
        return "https://postiz.techstarz101.com"
    if host in ("127.0.0.1", "localhost"):
        return f"http://localhost:{tool['local_port']}"
    # If accessed via branded fallback techstarz101.com/workstation/ and a subpath fallback exists, prefer HTTPS
    if host in ("techstarz101.com", "www.techstarz101.com"):
        if slug in SSLIP_CERTIFIED_SLUGS:
            return f"https://{slug}.{WORKSTATION_DOMAIN}"
        if slug in FALLBACK_PATHS:
            return FALLBACK_PATHS[slug]
        return f"http://2.25.238.185:{tool['local_port']}"
    if "sslip.io" in host or "workstation.techstarz101.com" in host:
        if slug in SSLIP_CERTIFIED_SLUGS:
            return f"https://{slug}.{WORKSTATION_DOMAIN}"
        return f"http://{slug}.{WORKSTATION_DOMAIN}"
    return f"http://{host}:{tool['local_port']}"


def _resolve_fallback_app_url(tool: dict) -> Optional[str]:
    return FALLBACK_PATHS.get(tool["slug"])


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


@app.get("/open/{svc_num}/{tool_id}", response_class=HTMLResponse)
def open_app_page(svc_num: str, tool_id: str) -> HTMLResponse:
    tool = _find_tool(svc_num, tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Unknown app: {svc_num}/{tool_id}")
    html = (STATIC_DIR / "open_app.html").read_text(encoding="utf-8")
    return HTMLResponse(html.replace("__SVC_NUM__", svc_num).replace("__TOOL_ID__", tool_id))


@app.get("/api/portal/open-status/{svc_num}/{tool_id}")
def api_open_status(svc_num: str, tool_id: str, request: Request) -> JSONResponse:
    tool = _find_tool(svc_num, tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Unknown app")
    key = tool["slug"]
    up = _probe_url(tool["probe"], timeout=0.8) if tool["probe"] else False
    if up:
        APP_LAST_TOUCH[key] = time.time()
        APP_BOOT_STATE[key] = "running"
    return JSONResponse(
        {
            "ok": True,
            "tool": tool,
            "up": up,
            "state": "running" if up else APP_BOOT_STATE.get(key, "idle"),
            "target_url": _resolve_public_app_url(request, tool),
            "fallback_url": _resolve_fallback_app_url(tool),
            "logs": APP_BOOT_LOGS.get(key, [])[-40:],
            "tunnel_cmd": f"python techstarz101_services/00_master_portal/hybrid_tunnel.py {svc_num} {tool_id}",
        }
    )


@app.post("/api/portal/wake/{svc_num}/{tool_id}")
def api_wake_app(svc_num: str, tool_id: str) -> JSONResponse:
    tool = _find_tool(svc_num, tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Unknown app")
    key = tool["slug"]
    if tool["probe"] and _probe_url(tool["probe"], timeout=0.8):
        APP_LAST_TOUCH[key] = time.time()
        APP_BOOT_STATE[key] = "running"
        return JSONResponse({"ok": True, "state": "running"})
    if tool["tier"] == "vps_wave1":
        if APP_BOOT_STATE.get(key) != "starting":
            APP_BOOT_LOGS[key] = []
            threading.Thread(target=_wake_wave1_worker, args=(key, tool), daemon=True).start()
        return JSONResponse({"ok": True, "state": "starting"})
    return JSONResponse({"ok": True, "state": "awaiting_hybrid_tunnel"})


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
            "portal": "Techstarz101 Workstation",
            "domain": WORKSTATION_DOMAIN,
            "vps_host": "2.25.238.185",
            "total_services": len(enriched),
            "total_standalone_tools": len(tools),
            "services": enriched,
        }
    )


@app.get("/api/portal/tools")
def api_tools() -> JSONResponse:
    tools = _load_all_tools()
    unique_probes = {t["probe"] for t in tools if t["probe"] and t["tier"] in ("vps_live", "vps_wave1")}
    probe_results: Dict[str, bool] = {}
    with ThreadPoolExecutor(max_workers=16) as pool:
        futs = {p: pool.submit(_probe_url, p, 0.4) for p in unique_probes}
        for p, f in futs.items():
            probe_results[p] = f.result()
    for t in tools:
        t["up"] = probe_results.get(t["probe"], False)
    return JSONResponse({"tools": tools})


@app.get("/api/portal/status")
def api_status() -> JSONResponse:
    with ThreadPoolExecutor(max_workers=len(SERVICES_CATALOG)) as pool:
        futs = {}
        for s in SERVICES_CATALOG:
            probe = s["url"] if s["external"] else f"http://127.0.0.1:{s['port']}"
            futs[s["num"]] = pool.submit(_probe_url, probe, 0.7 if not s["external"] else 1.2)
        statuses = {}
        live_count = 0
        for s in SERVICES_CATALOG:
            up = futs[s["num"]].result()
            if up:
                live_count += 1
            statuses[s["num"]] = {
                "up": up,
                "port": s["port"],
                "external": s["external"],
                "managed": s["num"] in MANAGED_PROCS and MANAGED_PROCS[s["num"]].poll() is None,
            }
    return JSONResponse({"live_count": live_count, "total": len(SERVICES_CATALOG), "services": statuses})


@app.post("/api/portal/service/{num}/start")
def api_start_service(num: str) -> JSONResponse:
    return JSONResponse(_spawn_service(num))


@app.post("/api/portal/service/{num}/stop")
def api_stop_service(num: str) -> JSONResponse:
    with LOCK:
        proc = MANAGED_PROCS.pop(num, None)
        if proc and proc.poll() is None:
            proc.terminate()
            return JSONResponse({"ok": True, "stopped": num})
    return JSONResponse({"ok": True})


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
    with LOCK:
        for num, proc in list(MANAGED_PROCS.items()):
            if proc.poll() is None:
                proc.terminate()
                stopped.append(num)
            MANAGED_PROCS.pop(num, None)
    return JSONResponse({"ok": True, "stopped": stopped})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7860)
