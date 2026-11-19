#!/usr/bin/env python3
"""
Techstarz101 Service #04 - Brand & Web Launch: Modular Tool Stack Hub.

8 standalone open-source tool repos across Stack A & Stack B with dedicated
clickable launch links (http://localhost:7868/t/<id>), custom stack composer,
and a live Instant Brand Kit & Deployable Landing Page Generator.

Run:  python techstarz101_services/04_brand_web_launch/hub/app.py
Open: http://localhost:7868
"""

from __future__ import annotations

import html as html_lib
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
SITE_DIR = SERVICE_DIR / "generated_site"
SITE_DIR.mkdir(parents=True, exist_ok=True)
REGISTRY = json.loads((TOOLS_DIR / "registry.json").read_text(encoding="utf-8"))
TOOLS: dict[str, dict[str, Any]] = REGISTRY["tools"]
HUB_PORT = 7868

DOCKER_DESKTOP_EXE = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "DockerDesktop" / "Docker Desktop.exe"
CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0

app = FastAPI(title="Techstarz101 - Brand & Web Launch Hub")

_state: dict[str, dict[str, Any]] = {
    tid: {"phase": "idle", "log": deque(maxlen=300), "started_at": None, "error": None} for tid in TOOLS
}
_locks: dict[str, threading.Lock] = {tid: threading.Lock() for tid in TOOLS}


def docker_bin() -> str:
    found = shutil.which("docker")
    return found or str(DOCKER_DESKTOP_EXE.parent / "resources" / "bin" / "docker.exe")


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


# ---------------------------------------------------------------- Instant Brand & Web Launch Engine
def build_brand_and_site(brand: str, niche: str, value_prop: str, accent: str = "#38bdf8", cta_url: str = "https://techstarz101.com/intake.html") -> dict[str, Any]:
    b_safe = html_lib.escape(brand)
    n_safe = html_lib.escape(niche)
    v_safe = html_lib.escape(value_prop)
    initials = "".join(w[0].upper() for w in brand.split()[:2]) or "TS"

    logo_svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">'
        f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0%" stop-color="{accent}"/><stop offset="100%" stop-color="#818cf8"/>'
        f'</linearGradient></defs>'
        f'<rect width="64" height="64" rx="16" fill="url(#g)"/>'
        f'<text x="32" y="41" text-anchor="middle" fill="#070a13" font-family="Arial,sans-serif" font-size="26" font-weight="900">{html_lib.escape(initials)}</text>'
        f'</svg>'
    )

    site_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{b_safe} — {n_safe}</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>body{{background:#070a13;color:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}}</style>
</head>
<body class="min-h-screen flex flex-col">
  <nav class="max-w-6xl w-full mx-auto px-6 py-6 flex justify-between items-center border-b border-slate-800/80">
    <div class="flex items-center gap-3">{logo_svg}<span class="text-xl font-extrabold tracking-tight">{b_safe}</span></div>
    <a href="{html_lib.escape(cta_url)}" class="px-5 py-2.5 rounded-xl font-bold text-slate-950 text-sm" style="background:{accent}">Launch Now →</a>
  </nav>
  <main class="flex-1 max-w-5xl mx-auto px-6 py-20 text-center space-y-8">
    <div class="inline-block px-4 py-1.5 rounded-full text-xs font-bold border border-slate-700 bg-slate-900" style="color:{accent}">{n_safe.upper()} · PRODUCTION READY</div>
    <h1 class="text-4xl md:text-6xl font-extrabold tracking-tight leading-tight text-white">{b_safe}: Own Your Growth Stack.</h1>
    <p class="text-lg md:text-xl text-slate-400 max-w-2xl mx-auto">{v_safe}</p>
    <div class="flex flex-wrap justify-center gap-4 pt-4">
      <a href="{html_lib.escape(cta_url)}" class="px-8 py-4 rounded-xl font-extrabold text-slate-950 text-base shadow-lg" style="background:{accent}">Book Your 48-Hour Launch →</a>
      <a href="#features" class="px-8 py-4 rounded-xl font-bold text-white border border-slate-700 bg-slate-900 text-base">Explore Architecture</a>
    </div>
    <section id="features" class="grid grid-cols-1 md:grid-cols-3 gap-6 pt-16 text-left">
      <div class="p-6 rounded-2xl bg-slate-900 border border-slate-800"><div class="text-2xl mb-2">🎨</div><h3 class="font-bold text-white text-lg">Sovereign Brand System</h3><p class="text-sm text-slate-400 mt-1">Vector identity, responsive tokens, and Penpot/CMS ready assets owned 100% by {b_safe}.</p></div>
      <div class="p-6 rounded-2xl bg-slate-900 border border-slate-800"><div class="text-2xl mb-2">⚡</div><h3 class="font-bold text-white text-lg">Zero-Tax Web Hosting</h3><p class="text-sm text-slate-400 mt-1">Automated SSL via Nginx Proxy Manager, Git CI via Gitea, and headless CMS speed.</p></div>
      <div class="p-6 rounded-2xl bg-slate-900 border border-slate-800"><div class="text-2xl mb-2">🟢</div><h3 class="font-bold text-white text-lg">24/7 Uptime &amp; SSL Guard</h3><p class="text-sm text-slate-400 mt-1">Continuous Uptime Kuma probes watching every route and certificate automatically.</p></div>
    </section>
  </main>
  <footer class="border-t border-slate-800 py-8 text-center text-xs text-slate-500">Built &amp; deployed with Techstarz101 Brand &amp; Web Launch · 100% Open Source</footer>
</body>
</html>"""

    (SITE_DIR / "index.html").write_text(site_html, encoding="utf-8")
    (SITE_DIR / "logo.svg").write_text(logo_svg, encoding="utf-8")
    return {
        "brand": brand,
        "niche": niche,
        "palette": {"primary": accent, "secondary": "#818cf8", "surface": "#0d1322", "canvas": "#070a13", "success": "#10b981"},
        "typography": {"display": "Inter / Plus Jakarta Sans (800)", "body": "Inter (400/500)", "mono": "JetBrains Mono"},
        "logo_svg": logo_svg,
        "preview_url": f"http://localhost:{HUB_PORT}/preview/site",
        "download_url": f"http://localhost:{HUB_PORT}/api/brand/download-site",
    }


build_brand_and_site(
    brand="Techstarz101 Sovereign Cloud",
    niche="Sovereign AI & Open-Source Web Systems",
    value_prop="From initial brand identity to live SSL-secured web deployment in 48 hours flat — zero SaaS lock-in.",
)


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


@app.get("/preview/site", response_class=HTMLResponse)
def preview_site():
    return HTMLResponse((SITE_DIR / "index.html").read_text(encoding="utf-8"))


@app.get("/api/brand/download-site")
def download_site():
    return FileResponse(SITE_DIR / "index.html", media_type="text/html", filename="index.html")


@app.post("/api/brand/generate")
async def api_brand_generate(request: Request):
    b = await request.json()
    return build_brand_and_site(
        brand=b.get("brand") or "Techstarz101 Sovereign Cloud",
        niche=b.get("niche") or "Sovereign AI & Open-Source Web Systems",
        value_prop=b.get("value_prop") or "From initial brand concept to live SSL-secured production web in 48 hours.",
        accent=b.get("accent") or "#38bdf8",
        cta_url=b.get("cta_url") or "https://techstarz101.com/intake.html",
    )


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
    print(f"Techstarz101 Brand & Web Launch hub -> http://localhost:{HUB_PORT}")
    uvicorn.run(app, host="127.0.0.1", port=HUB_PORT, log_level="info")
