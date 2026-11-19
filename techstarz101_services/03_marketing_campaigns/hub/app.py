#!/usr/bin/env python3
"""
Techstarz101 Service #03 - Marketing Campaigns: Modular Tool Stack Hub.

Every open-source tool in Stack A and Stack B is its own Docker Compose repo
under ../tools/<id>/ with a dedicated link: http://localhost:7867/t/<id>.
Also includes a live Multi-Angle A/B Ad Campaign Generator & Bayesian Winner simulator.

Run:  python techstarz101_services/03_marketing_campaigns/hub/app.py
Open: http://localhost:7867
"""

from __future__ import annotations

import json
import os
import random
import re
import secrets
import shutil
import string
import subprocess
import threading
import time
import urllib.error
import urllib.parse
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
REGISTRY = json.loads((TOOLS_DIR / "registry.json").read_text(encoding="utf-8"))
TOOLS: dict[str, dict[str, Any]] = REGISTRY["tools"]
HUB_PORT = 7867

DOCKER_DESKTOP_EXE = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "DockerDesktop" / "Docker Desktop.exe"
CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0

app = FastAPI(title="Techstarz101 - Marketing Campaigns Hub")

_state: dict[str, dict[str, Any]] = {
    tid: {"phase": "idle", "log": deque(maxlen=300), "started_at": None, "error": None} for tid in TOOLS
}
_locks: dict[str, threading.Lock] = {tid: threading.Lock() for tid in TOOLS}


def docker_bin() -> str:
    found = shutil.which("docker")
    if found:
        return found
    return str(DOCKER_DESKTOP_EXE.parent / "resources" / "bin" / "docker.exe")


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
            "phase": phase,
            "containers": containers,
            "url": meta["url"],
            "error": st["error"],
            "started_at": st["started_at"],
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
            st.update(phase="error", error=f"docker compose exited with code {code} (see log)")
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


# ---------------------------------------------------------------- Multi-Angle A/B Ad Engine
def generate_ab_campaign(offer: str, icp: str, channel: str, budget: float, landing_url: str) -> dict[str, Any]:
    angles = [
        {
            "angle": "Angle 1 · Pain / SaaS Tax Elimination",
            "slug": "pain-saas-tax",
            "variant_a": {
                "headline": f"Stop paying $2,000+/mo in seat fees for {icp}",
                "body": f"Most {icp} teams bleed cash on bloated SaaS subscriptions. Switch to {offer} and own your infrastructure 100%.",
                "cta": "Cut Your SaaS Bill Today",
            },
            "variant_b": {
                "headline": f"Why smart {icp} founders are ditching per-seat SaaS",
                "body": f"Zero contact taxes. Zero seat limits. Deploy {offer} in 48 hours with a 100% money-back guarantee.",
                "cta": "See the Sovereign Stack",
            },
        },
        {
            "angle": "Angle 2 · Speed & 48-Hour Guarantee",
            "slug": "speed-48h",
            "variant_a": {
                "headline": f"Live in 48 Hours: {offer}",
                "body": f"Skip 6-week agency retainers. We deploy your production-ready growth stack for {icp} in 48 hours flat.",
                "cta": "Claim Your 48h Sprint",
            },
            "variant_b": {
                "headline": f"From zero to autonomous growth by Friday",
                "body": f"Built specifically for {icp}. Flat $390 starter sprint — fully credited or 100% refunded if you don't love it.",
                "cta": "Book 15-Min Kickoff",
            },
        },
        {
            "angle": "Angle 3 · Sovereign ROI Math",
            "slug": "roi-math",
            "variant_a": {
                "headline": f"Replace $18,000/yr in software with one $390 sprint",
                "body": f"Open-source marketing automation, A/B testing, and analytics running on your own VPS for {icp}.",
                "cta": "Calculate Your Savings",
            },
            "variant_b": {
                "headline": f"The math is simple: Own vs. Rent your AI stack",
                "body": f"Deploy {offer} once and run unlimited campaigns with zero contact overages.",
                "cta": "Start Owning Today",
            },
        },
        {
            "angle": "Angle 4 · Social Proof & Direct Demo",
            "slug": "social-proof",
            "variant_a": {
                "headline": f"How {icp} teams automate A/B ads without agency markups",
                "body": f"See our live open-source campaign engine in action: multi-angle ads, Bayesian winners, and automated CRM follow-ups.",
                "cta": "Watch 60-Sec Demo",
            },
            "variant_b": {
                "headline": f"Inside the sovereign growth stack for {icp}",
                "body": f"Mautic + GrowthBook + Umami + Shlink wired together out of the box. Live review ready on day 2.",
                "cta": "Explore the Stack",
            },
        },
    ]

    results = []
    best_roas = 0.0
    winner_name = ""
    for idx, a in enumerate(angles):
        ctr_a = round(random.uniform(1.8, 3.6), 2)
        ctr_b = round(random.uniform(2.1, 4.4), 2)
        cpa_a = round(random.uniform(24.0, 58.0), 2)
        cpa_b = round(random.uniform(18.0, 46.0), 2)
        roas_a = round(390.0 / cpa_a, 2)
        roas_b = round(390.0 / cpa_b, 2)
        win_var = "B" if roas_b >= roas_a else "A"
        win_roas = max(roas_a, roas_b)
        if win_roas > best_roas:
            best_roas = win_roas
            winner_name = f"{a['angle']} (Variant {win_var})"

        utm_a = f"{landing_url}?{urllib.parse.urlencode({'utm_source': channel.lower(), 'utm_medium': 'paid_social', 'utm_campaign': a['slug'], 'utm_content': 'variant_a'})}"
        utm_b = f"{landing_url}?{urllib.parse.urlencode({'utm_source': channel.lower(), 'utm_medium': 'paid_social', 'utm_campaign': a['slug'], 'utm_content': 'variant_b'})}"

        results.append({
            **a,
            "budget_split": round(budget / len(angles), 2),
            "utm_a": utm_a,
            "utm_b": utm_b,
            "metrics": {
                "ctr_a": ctr_a, "ctr_b": ctr_b,
                "cpa_a": cpa_a, "cpa_b": cpa_b,
                "roas_a": roas_a, "roas_b": roas_b,
                "bayesian_confidence": f"{random.uniform(91.5, 99.1):.1f}%",
                "winning_variant": win_var,
            },
        })

    return {
        "offer": offer,
        "icp": icp,
        "channel": channel,
        "total_budget": budget,
        "recommended_winner": winner_name,
        "top_projected_roas": f"{best_roas:.2f}x",
        "angles": results,
    }


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


@app.post("/api/campaigns/generate")
async def api_campaigns_generate(request: Request):
    body = await request.json()
    return generate_ab_campaign(
        offer=body.get("offer") or "Techstarz101 $390 Sovereign AI Starter Sprint",
        icp=body.get("icp") or "B2B Marketing Agencies & Founders",
        channel=body.get("channel") or "Meta_Ads",
        budget=float(body.get("budget") or 1000),
        landing_url=body.get("landing_url") or "https://techstarz101.com/intake.html",
    )


if __name__ == "__main__":
    for tid in TOOLS:
        ensure_env(tid)
    print(f"Techstarz101 Marketing Campaigns hub -> http://localhost:{HUB_PORT}")
    uvicorn.run(app, host="127.0.0.1", port=HUB_PORT, log_level="info")
