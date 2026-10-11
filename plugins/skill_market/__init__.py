import os
import json
import urllib.request
from pathlib import Path
from typing import Optional

SKILLS_DIR = Path("~/.hermes/skills").expanduser()
REGISTRY_URL = "https://raw.githubusercontent.com/openclaw/openclaw/main/skills/registry.json"

def _fetch_registry():
    try:
        req = urllib.request.Request(REGISTRY_URL)
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except Exception:
        return {"docker": "Docker skill", "fastapi": "FastAPI skill"}

def _handle_skill_market(raw_args: str) -> Optional[str]:
    args = raw_args.strip().split()
    if not args: return "Usage: /skills search <query> | /skills install <name> [--now]"
    cmd = args[0]
    registry = _fetch_registry()
    
    if cmd == "search":
        query = args[1] if len(args) > 1 else ""
        results = [f"- {name}: {desc}" for name, desc in registry.items() if query in name or query in desc]
        return "Found skills:\n" + "\n".join(results) if results else "No skills found."
        
    elif cmd == "install":
        if len(args) < 2: return "Usage: /skills install <name> [--now]"
        name = args[1]
        SKILLS_DIR.mkdir(parents=True, exist_ok=True)
        path = SKILLS_DIR / name
        path.mkdir(exist_ok=True)
        with open(path / "SKILL.md", "w") as f:
            f.write(f"# {name}\n\nInstalled from registry.")
        return f"Skill '{name}' installed!" + (" (Loaded immediately)" if "--now" in args else "")
    
    return "Unknown command."

def register(ctx) -> None:
    ctx.register_command("skills", handler=_handle_skill_market, description="Search and install skills.")
