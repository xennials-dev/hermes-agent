#!/usr/bin/env python3
"""
Techstarz101 Service #02 - Social Media Closer: Tool Stack Hub.

Every open-source tool in Stack A and Stack B is its own Docker Compose
"repo" under ../tools/<id>/. This hub:
  * launches / stops each tool on demand (one click per tool),
  * gives every tool a dedicated link: http://localhost:7866/t/<id>,
  * launches whole stacks or any custom combination of tools,
  * runs the closer automation (DM -> AI reply -> CRM) across whichever tools are up.

Run:  python techstarz101_services/02_social_media_closer/hub/app.py
Open: http://localhost:7866
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
SETTINGS_PATH = HUB_DIR / "settings.local.json"
REGISTRY = json.loads((TOOLS_DIR / "registry.json").read_text(encoding="utf-8"))
TOOLS: dict[str, dict[str, Any]] = REGISTRY["tools"]
HUB_PORT = 7866

DOCKER_DESKTOP_EXE = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "DockerDesktop" / "Docker Desktop.exe"
CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0

app = FastAPI(title="Techstarz101 - Social Media Closer Hub")

# ---------------------------------------------------------------- state
_state: dict[str, dict[str, Any]] = {
    tid: {"phase": "idle", "log": deque(maxlen=300), "started_at": None, "error": None} for tid in TOOLS
}
_locks: dict[str, threading.Lock] = {tid: threading.Lock() for tid in TOOLS}


def docker_bin() -> str:
    found = shutil.which("docker")
    if found:
        return found
    fallback = DOCKER_DESKTOP_EXE.parent / "resources" / "bin" / "docker.exe"
    return str(fallback)


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


# ---------------------------------------------------------------- secrets / .env
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


def read_env(tid: str) -> dict[str, str]:
    env_path = TOOLS_DIR / tid / ".env"
    if not env_path.exists():
        return {}
    out = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def compose_cmd(tid: str, *args: str) -> list[str]:
    tool_dir = TOOLS_DIR / tid
    return [docker_bin(), "compose", "--env-file", str(tool_dir / ".env"), "-f", str(tool_dir / "docker-compose.yml"), *args]


# ---------------------------------------------------------------- probes
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
    """compose project name -> number of running containers."""
    try:
        res = run([docker_bin(), "ps", "--format", '{{.Label "com.docker.compose.project"}}'], timeout=10)
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


# ---------------------------------------------------------------- lifecycle
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
        _log(tid, f"docker compose up -d  ({TOOLS[tid]['name']})")
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
        _log(tid, "Containers started. Waiting for the web app to answer...")
        deadline = time.time() + 900
        while time.time() < deadline:
            if http_up(TOOLS[tid]["probe"]):
                st["phase"] = "running"
                _log(tid, f"READY -> {TOOLS[tid]['url']}")
                return
            time.sleep(4)
        st.update(phase="error", error="App did not answer within 15 minutes (check container logs).")


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


# ---------------------------------------------------------------- settings
SETTINGS_DEFAULTS = {
    "ollama_model": "",
    "chatwoot_url": "http://localhost:5110",
    "chatwoot_api_token": "",
    "twenty_url": "http://localhost:5140",
    "twenty_api_key": "",
    "espocrm_url": "http://localhost:5230",
    "espocrm_api_key": "",
    "flowise_url": "http://localhost:5210",
    "flowise_chatflow_id": "",
    "offer_url": "https://techstarz101.com/intake.html",
}


def load_settings() -> dict[str, str]:
    data = dict(SETTINGS_DEFAULTS)
    if SETTINGS_PATH.exists():
        data.update(json.loads(SETTINGS_PATH.read_text(encoding="utf-8")))
    return data


def save_settings(new: dict[str, str]) -> dict[str, str]:
    data = load_settings()
    data.update({k: str(v) for k, v in new.items() if k in SETTINGS_DEFAULTS})
    SETTINGS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def masked(settings: dict[str, str]) -> dict[str, str]:
    out = {}
    for k, v in settings.items():
        if ("token" in k or "key" in k) and v:
            out[k] = v[:4] + "..." + v[-4:] if len(v) > 10 else "****"
        else:
            out[k] = v
    return out


# ---------------------------------------------------------------- closer engine
OLLAMA_CANDIDATES = ["http://localhost:11434", "http://localhost:11435"]

CLOSER_SYSTEM = (
    "You are the Techstarz101 Social Media Closer, a friendly, concise sales assistant replying to social DMs. "
    "Techstarz101 builds sovereign, self-hosted AI systems (n8n, Twenty CRM, Postiz, Hermes agents) that remove SaaS seat fees. "
    "Entry offer: flat $390 48-hour starter sprint, 100% money-back guarantee. "
    "Rules: reply in 2-4 short sentences, answer the actual question, never invent prices other than $390 / $1,480 full build / $490 per month retainer, "
    "and end with one clear next step that includes the booking link {offer_url}."
)

INTENT_RULES = [
    ("ready_to_buy", ["buy", "sign up", "invoice", "pay", "start", "let's do", "lets do", "book"]),
    ("pricing", ["price", "cost", "how much", "$", "budget", "rate"]),
    ("demo_request", ["demo", "call", "meeting", "show me", "walkthrough"]),
    ("objection", ["expensive", "not sure", "already use", "too much", "later", "maybe"]),
    ("support", ["broken", "error", "help", "issue", "not working"]),
]


def classify_intent(message: str) -> str:
    low = message.lower()
    for intent, words in INTENT_RULES:
        if any(w in low for w in words):
            return intent
    return "general_inquiry"


def _post_json(url: str, payload: dict, headers: dict | None = None, timeout: float = 60) -> Any:
    body = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=body, method="POST",
                                 headers={"Content-Type": "application/json", **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode() or "{}"
        return json.loads(raw)


def _get_json(url: str, timeout: float = 3) -> Any:
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def find_ollama() -> tuple[str, str] | None:
    preferred = load_settings().get("ollama_model") or ""
    for base in OLLAMA_CANDIDATES:
        try:
            models = [m["name"] for m in _get_json(f"{base}/api/tags").get("models", [])]
        except Exception:
            continue
        if not models:
            continue
        return base, preferred if preferred in models else models[0]
    return None


def template_reply(intent: str, offer_url: str) -> str:
    replies = {
        "ready_to_buy": f"Love it - let's get you started. Grab a kickoff slot here and we'll begin your 48-hour sprint: {offer_url}",
        "pricing": f"Our starter sprint is a flat $390 delivered in 48 hours, with a 100% money-back guarantee. Want to lock in a slot? {offer_url}",
        "demo_request": f"Happy to show you live. Pick any 15-minute slot that works and I'll walk you through it: {offer_url}",
        "objection": f"Totally fair. Most clients replace $500+/mo in SaaS seats with one self-hosted build, and the $390 sprint is fully refundable. Worth a quick look? {offer_url}",
        "support": f"Sorry about that - I've flagged it for the team and someone will follow up shortly. You can also book time directly here: {offer_url}",
    }
    return replies.get(intent, f"Thanks for reaching out! We build self-hosted AI systems that cut SaaS costs. Want to see how it fits your business? {offer_url}")


def generate_reply(message: str, stack: str = "A") -> dict[str, Any]:
    settings = load_settings()
    offer_url = settings["offer_url"]
    intent = classify_intent(message)
    started = time.time()

    if stack == "B" and settings.get("flowise_chatflow_id"):
        try:
            res = _post_json(f"{settings['flowise_url']}/api/v1/prediction/{settings['flowise_chatflow_id']}",
                             {"question": message})
            return {"reply": res.get("text") or json.dumps(res), "intent": intent, "engine": "flowise",
                    "model": settings["flowise_chatflow_id"], "latency_s": round(time.time() - started, 2)}
        except Exception as e:
            flowise_err = str(e)
        else:
            flowise_err = ""
    else:
        flowise_err = ""

    found = find_ollama()
    if found:
        base, model = found
        try:
            res = _post_json(f"{base}/api/chat", {
                "model": model, "stream": False,
                "options": {"temperature": 0.4, "num_predict": 180},
                "messages": [
                    {"role": "system", "content": CLOSER_SYSTEM.format(offer_url=offer_url)},
                    {"role": "user", "content": message},
                ],
            }, timeout=120)
            return {"reply": res["message"]["content"].strip(), "intent": intent, "engine": "ollama",
                    "model": model, "endpoint": base, "latency_s": round(time.time() - started, 2),
                    "note": flowise_err and f"Flowise failed, fell back to Ollama: {flowise_err}"}
        except Exception as e:
            err = str(e)
    else:
        err = "No Ollama endpoint with a pulled model (launch 'Ollama + Open WebUI')."

    return {"reply": template_reply(intent, offer_url), "intent": intent, "engine": "template-fallback",
            "model": None, "latency_s": round(time.time() - started, 2), "note": err}


def split_name(full: str) -> tuple[str, str]:
    parts = (full or "Social Lead").strip().split(" ", 1)
    return parts[0], parts[1] if len(parts) > 1 else "(DM)"


def crm_write(stack: str, name: str, email: str, message: str, intent: str) -> dict[str, Any]:
    s = load_settings()
    first, last = split_name(name)
    if stack == "A":
        if not s["twenty_api_key"]:
            return {"status": "skipped", "detail": "Add a Twenty API key in Settings to log leads."}
        payload: dict[str, Any] = {"name": {"firstName": first, "lastName": last}}
        if email:
            payload["emails"] = {"primaryEmail": email}
        try:
            res = _post_json(f"{s['twenty_url']}/rest/people", payload,
                             {"Authorization": f"Bearer {s['twenty_api_key']}"}, timeout=20)
            pid = (res.get("data") or {}).get("createPerson", {}).get("id") or res.get("id")
            return {"status": "ok", "detail": f"Twenty person created ({pid})"}
        except Exception as e:
            return {"status": "error", "detail": f"Twenty: {e}"}
    if not s["espocrm_api_key"]:
        return {"status": "skipped", "detail": "Add an EspoCRM API key in Settings to log leads."}
    try:
        res = _post_json(f"{s['espocrm_url']}/api/v1/Lead", {
            "firstName": first, "lastName": last, "emailAddress": email or None,
            "source": "Web Site", "status": "New",
            "description": f"[Social DM | intent={intent}] {message}",
        }, {"X-Api-Key": s["espocrm_api_key"]}, timeout=20)
        return {"status": "ok", "detail": f"EspoCRM lead created ({res.get('id')})"}
    except Exception as e:
        return {"status": "error", "detail": f"EspoCRM: {e}"}


# ---------------------------------------------------------------- routes: pages
@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    return HTMLResponse((STATIC_DIR / "index.html").read_text(encoding="utf-8"))


@app.get("/t/{tid}", response_class=HTMLResponse)
def tool_link(tid: str) -> HTMLResponse:
    """Dedicated per-tool link: auto-launches the tool, then redirects into it."""
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


# ---------------------------------------------------------------- routes: API
@app.get("/api/registry")
def api_registry():
    tools = {}
    for tid, meta in TOOLS.items():
        extra = {}
        if tid == "espocrm":
            extra["admin_password"] = read_env("espocrm").get("ESPOCRM_ADMIN_PASSWORD", "(generated on first launch)")
        tools[tid] = {**meta, **extra, "link": f"http://localhost:{HUB_PORT}/t/{tid}"}
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
def api_logs(tid: str, containers: int = 0):
    if tid not in TOOLS:
        raise HTTPException(404)
    out = {"hub": list(_state[tid]["log"])}
    if containers and docker_ready() and (TOOLS_DIR / tid / ".env").exists():
        try:
            res = run(compose_cmd(tid, "logs", "--tail", "60", "--no-color"), cwd=TOOLS_DIR / tid, timeout=30)
            out["containers"] = (res.stdout + res.stderr)[-12000:]
        except Exception as e:
            out["containers"] = str(e)
    return out


@app.post("/api/stack/start")
async def api_stack_start(request: Request):
    body = await request.json()
    ids = body.get("tools") or REGISTRY["stacks"].get(body.get("stack", ""), {}).get("tools", [])
    for tid in ids:
        start_tool(tid)
    return {"ok": True, "started": ids, "est_ram_mb": sum(TOOLS[t]["ram_mb"] for t in ids if t in TOOLS)}


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
        return {"ok": True, "detail": "Docker Desktop is starting (30-90 seconds)."}
    return JSONResponse({"ok": False, "detail": f"Docker Desktop not found at {DOCKER_DESKTOP_EXE}"}, status_code=404)


@app.get("/api/settings")
def api_get_settings():
    return masked(load_settings())


@app.post("/api/settings")
async def api_save_settings(request: Request):
    body = await request.json()
    clean = {k: v for k, v in body.items() if v and "..." not in str(v) and v != "****"}
    return masked(save_settings(clean))


@app.post("/api/closer/reply")
async def api_closer_reply(request: Request):
    body = await request.json()
    return generate_reply(body.get("message", ""), body.get("stack", "A"))


@app.post("/api/pipeline/test")
async def api_pipeline_test(request: Request):
    """Run one DM through the selected stack and report every hop."""
    body = await request.json()
    stack = body.get("stack", "A")
    message = body.get("message") or "How much does it cost to automate our DMs?"
    name = body.get("name") or "Jordan Rivera"
    email = body.get("email") or ""
    trace = []
    status = tool_status_all()["tools"]
    inbox_tool, crm_tool, auto_tool = ("chatwoot", "twenty", "n8n") if stack == "A" else ("mixpost", "espocrm", "activepieces")
    trace.append({"step": f"1. Inbound DM ({TOOLS[inbox_tool]['name']})",
                  "status": "ok" if status[inbox_tool]["phase"] == "running" else "simulated",
                  "detail": f"{name}: \"{message}\""})
    reply = generate_reply(message, stack)
    trace.append({"step": f"2. AI reply ({reply['engine']})", "status": "ok" if reply["engine"] != "template-fallback" else "fallback",
                  "detail": reply["reply"], "meta": {k: reply.get(k) for k in ("intent", "model", "latency_s", "note")}})
    trace.append({"step": f"3. Automation ({TOOLS[auto_tool]['name']})",
                  "status": "ok" if status[auto_tool]["phase"] == "running" else "skipped",
                  "detail": "Workflow engine is up - import the stack workflow from the Automations tab."
                  if status[auto_tool]["phase"] == "running" else f"Launch {TOOLS[auto_tool]['name']} to run this hop in the workflow engine."})
    crm = crm_write(stack, name, email, message, reply["intent"])
    trace.append({"step": f"4. CRM log ({TOOLS[crm_tool]['name']})", **crm})
    return {"stack": stack, "trace": trace}


@app.post("/api/closer/chatwoot-webhook")
async def chatwoot_webhook(request: Request):
    """Register in Chatwoot: Settings > Integrations > Webhooks >
    http://host.docker.internal:7866/api/closer/chatwoot-webhook (event: Message Created)."""
    p = await request.json()
    if p.get("event") != "message_created" or p.get("message_type") != "incoming" or p.get("private"):
        return {"ignored": True}
    content = p.get("content") or ""
    conv = (p.get("conversation") or {}).get("id")
    account = (p.get("account") or {}).get("id")
    sender = p.get("sender") or {}
    reply = generate_reply(content, "A")
    s = load_settings()
    sent = "skipped (no Chatwoot API token in Settings)"
    if s["chatwoot_api_token"] and conv and account:
        try:
            _post_json(f"{s['chatwoot_url']}/api/v1/accounts/{account}/conversations/{conv}/messages",
                       {"content": reply["reply"], "message_type": "outgoing", "private": False},
                       {"api_access_token": s["chatwoot_api_token"]}, timeout=20)
            sent = "ok"
        except Exception as e:
            sent = f"error: {e}"
    crm = crm_write("A", sender.get("name", ""), sender.get("email") or "", content, reply["intent"]) \
        if reply["intent"] in ("ready_to_buy", "pricing", "demo_request") else {"status": "skipped", "detail": "intent not sales-qualified"}
    return {"reply": reply, "chatwoot": sent, "crm": crm}


@app.post("/api/closer/generic-webhook")
async def generic_webhook(request: Request):
    """For n8n / Activepieces: POST {message, name, email, stack} -> reply + CRM write."""
    p = await request.json()
    stack = p.get("stack", "B")
    reply = generate_reply(p.get("message", ""), stack)
    crm = crm_write(stack, p.get("name", ""), p.get("email", ""), p.get("message", ""), reply["intent"]) \
        if p.get("log_to_crm", True) else {"status": "skipped"}
    return {"reply": reply["reply"], "intent": reply["intent"], "engine": reply["engine"], "crm": crm}


if __name__ == "__main__":
    for tid in TOOLS:
        ensure_env(tid)
    print(f"Techstarz101 Social Media Closer hub -> http://localhost:{HUB_PORT}")
    uvicorn.run(app, host="127.0.0.1", port=HUB_PORT, log_level="info")

