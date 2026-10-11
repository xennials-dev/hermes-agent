import os
import subprocess
from typing import Any, Dict, Optional

def _is_git_repo(path: str) -> bool:
    try:
        res = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=path, capture_output=True, text=True)
        return "true" in res.stdout.lower()
    except Exception:
        return False

def _on_pre_tool_call(tool_name: str = "", args: Optional[Dict[str, Any]] = None, **_: Any) -> None:
    if tool_name not in ["write_to_file", "replace_file_content", "multi_replace_file_content", "patch_file"]: return
    if not args: return
    path_str = args.get("TargetFile") or args.get("path")
    if not path_str: return
    dir_name = os.path.dirname(path_str)
    if _is_git_repo(dir_name):
        try:
            subprocess.run(["git", "add", path_str], cwd=dir_name, check=True)
            subprocess.run(["git", "commit", "-m", f"hermes-time-travel: Backup {os.path.basename(path_str)} before {tool_name}"], cwd=dir_name)
        except Exception:
            pass

def _handle_rewind(raw_args: str) -> Optional[str]:
    args = raw_args.strip()
    steps = int(args) if args.isdigit() else 1
    cwd = os.getcwd()
    if not _is_git_repo(cwd):
        return "Not a git repository. Cannot rewind."
    try:
        subprocess.run(["git", "reset", "--hard", f"HEAD~{steps}"], cwd=cwd, check=True, capture_output=True)
        return f"Rewound {steps} steps using git reset."
    except Exception as e:
        return f"Failed to rewind: {e}"

def register(ctx) -> None:
    ctx.register_hook("pre_tool_call", _on_pre_tool_call)
    ctx.register_command("rewind", handler=_handle_rewind, description="Revert recent edits using git. Usage: /rewind [N]")
