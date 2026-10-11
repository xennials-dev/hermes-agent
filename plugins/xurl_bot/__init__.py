import threading
import time
import subprocess
import json
from typing import Optional

_BOT_RUNNING = False

def _draft_reply(mention_text: str) -> str:
    if "help" in mention_text.lower():
        return "I can help with that! Let me know what you need."
    return "Thanks for reaching out! I'll get back to you shortly."

def _xurl_bot_loop():
    global _BOT_RUNNING
    last_id = None
    while _BOT_RUNNING:
        try:
            res = subprocess.run(["xurl", "mentions", "-n", "5"], capture_output=True, text=True)
            if res.returncode == 0:
                data = json.loads(res.stdout)
                mentions = data.get("data", [])
                for m in mentions:
                    if last_id and m["id"] == last_id:
                        break
                    reply = _draft_reply(m["text"])
                    subprocess.run(["xurl", "reply", m["id"], reply])
                if mentions:
                    last_id = mentions[0]["id"]
        except Exception as e:
            print(f"[XURL BOT] Error: {e}")
        time.sleep(300)

def _handle_xurl_bot(raw_args: str) -> Optional[str]:
    global _BOT_RUNNING
    args = raw_args.strip().split()
    if not args or args[0] not in ["start", "stop"]: return "Usage: /xurlbot start | stop"
    
    if args[0] == "start":
        if _BOT_RUNNING: return "xurl bot is already running."
        _BOT_RUNNING = True
        threading.Thread(target=_xurl_bot_loop, daemon=True).start()
        return "xurl bot started! It will read timeline and reply periodically."
    else:
        _BOT_RUNNING = False
        return "xurl bot stopped."

def register(ctx) -> None:
    ctx.register_command("xurlbot", handler=_handle_xurl_bot, description="Manage the automated xurl bot.")
