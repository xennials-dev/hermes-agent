"""
Techstarz101 Hybrid Workstation Tunnel Bridge (Option A — $0 Extra Cloud Cost)
Boots any Wave 2 / Wave 3 heavy or GPU open-source app in local Docker Desktop
and opens a secure SSH reverse tunnel to the Hostinger VPS (2.25.238.185) so
https://<app>.workstation.techstarz101.com serves the live open-source app.

Usage:
  python techstarz101_services/00_master_portal/hybrid_tunnel.py 12 comfyui
  python techstarz101_services/00_master_portal/hybrid_tunnel.py 11 docling-serve
"""

from __future__ import annotations

import json
import secrets
import subprocess
import sys
from pathlib import Path

SERVICES_ROOT = Path(__file__).resolve().parent.parent
VPS_HOST = "root@2.25.238.185"


def ensure_env(tdir: Path) -> None:
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


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python hybrid_tunnel.py <service_num> <tool_id>")
        print("Example: python hybrid_tunnel.py 12 comfyui")
        sys.exit(1)

    svc_num, tool_id = sys.argv[1].zfill(2), sys.argv[2]
    matches = list(SERVICES_ROOT.glob(f"{svc_num}_*"))
    if not matches:
        sys.exit(f"Service #{svc_num} not found.")
    svc_dir = matches[0]
    reg = json.loads((svc_dir / "tools" / "registry.json").read_text(encoding="utf-8"))
    meta = reg["tools"].get(tool_id)
    if not meta:
        sys.exit(f"Tool '{tool_id}' not found in Service #{svc_num}.")

    port = int(meta["url"].split(":")[2].split("/")[0])
    tdir = svc_dir / "tools" / tool_id
    ensure_env(tdir)

    print(f"[hybrid] Starting local Docker app: {meta['name']} on localhost:{port} ...")
    subprocess.run(["docker", "compose", "up", "-d"], cwd=str(tdir), check=True)

    print(f"[hybrid] Opening reverse SSH tunnel -> {VPS_HOST} (127.0.0.1:{port} -> local :{port}) ...")
    print(f"[hybrid] Live at: https://{tool_id}.workstation.techstarz101.com  (Ctrl+C to close tunnel)")
    subprocess.run(
        [
            "ssh",
            "-o", "ServerAliveInterval=30",
            "-o", "ExitOnForwardFailure=yes",
            "-N",
            "-R", f"127.0.0.1:{port}:127.0.0.1:{port}",
            VPS_HOST,
        ],
        check=True,
    )


if __name__ == "__main__":
    main()

