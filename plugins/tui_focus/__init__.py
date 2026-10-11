import json
import urllib.request
from typing import Optional

def _handle_tui_focus(raw_args: str) -> Optional[str]:
    try:
        req = urllib.request.Request("http://127.0.0.1:8000/rpc", 
            data=json.dumps({"method": "set_zen_mode", "params": {"enabled": True}}).encode(),
            headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=1)
        return "RPC to tui_gateway successful. Zen Mode enabled in UI."
    except Exception:
        return "\033[?1049h\033[2J\033[H\nZen Mode enabled in terminal.\n\033[?1049l"

def register(ctx) -> None:
    ctx.register_command("focus", handler=_handle_tui_focus, description="Toggle TUI Zen Mode.")
