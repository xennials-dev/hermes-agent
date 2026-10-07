"""Twenty CRM Native Model Context Protocol (MCP) Server.

Provides stdio and JSON-RPC bridging to Twenty CRM for Hermes Agent:
- Tools: twenty_list_opportunities, twenty_get_opportunity, twenty_list_notes,
         twenty_create_note, twenty_create_task, twenty_semantic_search,
         twenty_create_deal_strategy_brief, twenty_create_competitor_intel,
         twenty_create_risk_assessment, twenty_approve_task
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request

TWENTY_URL = os.environ.get("TWENTY_SERVER_URL", "http://127.0.0.1:3000").rstrip("/")


def call_mcp_http(payload: dict) -> dict:
    url = f"{TWENTY_URL}/mcp"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        return {
            "jsonrpc": "2.0",
            "id": payload.get("id"),
            "error": {"code": -32000, "message": f"Twenty MCP Error: {exc}"},
        }


def main():
    """Stdio loop reading line-delimited JSON-RPC from Hermes Agent."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            res = call_mcp_http(req)
            sys.stdout.write(json.dumps(res) + "\n")
            sys.stdout.flush()
        except Exception as e:
            err_res = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {e}"},
            }
            sys.stdout.write(json.dumps(err_res) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
