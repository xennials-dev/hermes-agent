#!/usr/bin/env python3
"""
Odoo ERP Python Client & MCP Server for Hermes Agent.

Provides XML-RPC & JSON-RPC communication for querying, creating, and updating
records across Odoo models (CRM, Sales, Invoicing, Inventory, HR, Projects, Helpdesk).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import xmlrpc.client
from typing import Any, Dict, List, Optional, Union


class OdooClient:
    """Synchronous XML-RPC client for Odoo Community, Enterprise, and Odoo.sh."""

    def __init__(
        self,
        url: Optional[str] = None,
        db: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.url = (url or os.getenv("ODOO_URL", "http://localhost:8069")).rstrip("/")
        self.db = db or os.getenv("ODOO_DB", "odoo")
        self.username = username or os.getenv("ODOO_USERNAME", "admin")
        self.password = password or os.getenv("ODOO_PASSWORD", "admin")
        self.uid: Optional[int] = None

        self._common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
        self._models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")

    def authenticate(self) -> int:
        """Authenticate with Odoo and cache the User ID (UID)."""
        try:
            self.uid = self._common.authenticate(
                self.db, self.username, self.password, {}
            )
            if not self.uid:
                raise RuntimeError(
                    f"Authentication failed for user '{self.username}' on database '{self.db}'."
                )
            return self.uid
        except Exception as exc:
            raise RuntimeError(f"Odoo Connection Error: {exc}") from exc

    def ensure_auth(self) -> int:
        """Ensure client is authenticated before API calls."""
        if self.uid is None:
            return self.authenticate()
        return self.uid

    def execute(self, model: str, method: str, *args: Any, **kwargs: Any) -> Any:
        """Execute a method on any Odoo model."""
        uid = self.ensure_auth()
        return self._models.execute_kw(
            self.db, uid, self.password, model, method, list(args), kwargs
        )

    def search_read(
        self,
        model: str,
        domain: Optional[List[Any]] = None,
        fields: Optional[List[str]] = None,
        limit: int = 20,
        offset: int = 0,
        order: str = "id desc",
    ) -> List[Dict[str, Any]]:
        """Search and read records from an Odoo model."""
        kwargs: Dict[str, Any] = {
            "limit": limit,
            "offset": offset,
        }
        if fields:
            kwargs["fields"] = fields
        if order:
            kwargs["order"] = order

        return self.execute(model, "search_read", domain or [], **kwargs)

    def create(self, model: str, values: Dict[str, Any]) -> int:
        """Create a new record in an Odoo model. Returns the new record ID."""
        return self.execute(model, "create", values)

    def write(self, model: str, ids: List[int], values: Dict[str, Any]) -> bool:
        """Update fields on existing record(s)."""
        return self.execute(model, "write", ids, values)

    def unlink(self, model: str, ids: List[int]) -> bool:
        """Delete record(s) from an Odoo model."""
        return self.execute(model, "unlink", ids)


# ---------------------------------------------------------------------------
# MCP Server Implementation (stdio JSON-RPC)
# ---------------------------------------------------------------------------


def run_mcp_server():
    """Lightweight stdio MCP server exposing Odoo operations."""
    client = OdooClient()

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            req = json.loads(line)
            req_id = req.get("id")
            method = req.get("method")

            if method == "initialize":
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "odoo-mcp", "version": "1.0.0"},
                    },
                }
            elif method == "tools/list":
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "tools": [
                            {
                                "name": "odoo_search_read",
                                "description": "Search and read records from any Odoo model (e.g. crm.lead, sale.order, account.move, project.task, stock.quant).",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "model": {"type": "string"},
                                        "domain": {
                                            "type": "array",
                                            "description": "Odoo domain filter list, e.g. [['stage_id', '=', 'New']]",
                                        },
                                        "fields": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                        },
                                        "limit": {"type": "integer", "default": 20},
                                    },
                                    "required": ["model"],
                                },
                            },
                            {
                                "name": "odoo_create_record",
                                "description": "Create a new record in an Odoo model.",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "model": {"type": "string"},
                                        "values": {"type": "object"},
                                    },
                                    "required": ["model", "values"],
                                },
                            },
                            {
                                "name": "odoo_update_record",
                                "description": "Update fields on an existing Odoo record.",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "model": {"type": "string"},
                                        "ids": {"type": "array", "items": {"type": "integer"}},
                                        "values": {"type": "object"},
                                    },
                                    "required": ["model", "ids", "values"],
                                },
                            },
                        ]
                    },
                }
            elif method == "tools/call":
                params = req.get("params", {})
                tool_name = params.get("name")
                args = params.get("arguments", {})

                try:
                    if tool_name == "odoo_search_read":
                        data = client.search_read(
                            model=args["model"],
                            domain=args.get("domain", []),
                            fields=args.get("fields"),
                            limit=args.get("limit", 20),
                        )
                        output_text = json.dumps(data, indent=2, default=str)
                    elif tool_name == "odoo_create_record":
                        rec_id = client.create(args["model"], args["values"])
                        output_text = json.dumps({"success": True, "created_id": rec_id})
                    elif tool_name == "odoo_update_record":
                        success = client.write(args["model"], args["ids"], args["values"])
                        output_text = json.dumps({"success": success})
                    else:
                        output_text = f"Unknown tool: {tool_name}"

                    resp = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": [{"type": "text", "text": output_text}]
                        },
                    }
                except Exception as exc:
                    resp = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": [{"type": "text", "text": f"Error: {exc}"}],
                            "isError": True,
                        },
                    }
            else:
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": "Method not found"},
                }

            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
        except Exception:
            break


# ---------------------------------------------------------------------------
# CLI Command Dispatcher
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Odoo ERP Client & Helper for Hermes Agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # MCP Subcommand
    subparsers.add_parser("mcp", help="Run in MCP Server stdio mode")

    # Test Connection
    test_p = subparsers.add_parser("test-connection", help="Test Odoo authentication")
    test_p.add_argument("--url", default=os.getenv("ODOO_URL"))
    test_p.add_argument("--db", default=os.getenv("ODOO_DB"))
    test_p.add_argument("--username", default=os.getenv("ODOO_USERNAME"))
    test_p.add_argument("--password", default=os.getenv("ODOO_PASSWORD"))

    # Search-Read
    search_p = subparsers.add_parser("search-read", help="Query Odoo model")
    search_p.add_argument("--model", required=True, help="Odoo model, e.g. crm.lead")
    search_p.add_argument("--domain", default="[]", help="JSON domain filter list")
    search_p.add_argument("--fields", help="Comma-separated field list")
    search_p.add_argument("--limit", type=int, default=10)

    # Create Record
    create_p = subparsers.add_parser("create", help="Create new record")
    create_p.add_argument("--model", required=True)
    create_p.add_argument("--values", required=True, help="JSON dictionary of values")

    # Update Record
    update_p = subparsers.add_parser("update", help="Update existing record")
    update_p.add_argument("--model", required=True)
    update_p.add_argument("--ids", required=True, help="Comma-separated record IDs")
    update_p.add_argument("--values", required=True, help="JSON dictionary of values")

    args = parser.parse_args()

    if args.command == "mcp":
        run_mcp_server()
        return

    client = OdooClient(
        url=getattr(args, "url", None),
        db=getattr(args, "db", None),
        username=getattr(args, "username", None),
        password=getattr(args, "password", None),
    )

    if args.command == "test-connection":
        try:
            uid = client.authenticate()
            print(f"Successfully authenticated with Odoo at {client.url} (UID: {uid}, DB: {client.db})")
        except Exception as exc:
            print(f"Failed to connect to Odoo: {exc}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "search-read":
        domain = json.loads(args.domain)
        fields = [f.strip() for f in args.fields.split(",")] if args.fields else None
        res = client.search_read(args.model, domain=domain, fields=fields, limit=args.limit)
        print(json.dumps(res, indent=2, default=str))

    elif args.command == "create":
        vals = json.loads(args.values)
        rec_id = client.create(args.model, vals)
        print(f"Created {args.model} record ID: {rec_id}")

    elif args.command == "update":
        rec_ids = [int(i.strip()) for i in args.ids.split(",")]
        vals = json.loads(args.values)
        success = client.write(args.model, rec_ids, vals)
        print(f"Update status on {args.model} ({rec_ids}): {success}")


if __name__ == "__main__":
    main()
