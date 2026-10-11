import threading
import time
import subprocess
from typing import Optional

_SENTINEL_RUNNING = False

def _scan_dependencies():
    try:
        res = subprocess.run(["pip-audit"], capture_output=True, text=True)
        if res.returncode != 0 and "No known vulnerabilities" not in res.stdout:
            print(f"\n[SECURITY SENTINEL] Dependency vulnerabilities found!\n{res.stdout[:500]}")
    except FileNotFoundError:
        pass
    
    try:
        cmd = ["netstat", "-ano"] if subprocess.os.name == 'nt' else ["netstat", "-tuln"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if "4444" in res.stdout or "1337" in res.stdout:
            print(f"\n[SECURITY SENTINEL] Suspicious port open!\n")
    except Exception:
        pass

def _sentinel_loop():
    global _SENTINEL_RUNNING
    while _SENTINEL_RUNNING:
        _scan_dependencies()
        time.sleep(1800)

def _handle_sentinel(raw_args: str) -> Optional[str]:
    global _SENTINEL_RUNNING
    args = raw_args.strip().split()
    if not args or args[0] not in ["start", "stop"]: return "Usage: /sentinel start | stop"
    if args[0] == "start":
        if _SENTINEL_RUNNING: return "Sentinel already running."
        _SENTINEL_RUNNING = True
        threading.Thread(target=_sentinel_loop, daemon=True).start()
        return "Autonomous Security Sentinel started."
    else:
        _SENTINEL_RUNNING = False
        return "Sentinel stopped."

def register(ctx) -> None:
    ctx.register_command("sentinel", handler=_handle_sentinel, description="Manage background Security Sentinel. Usage: /sentinel start|stop")
