#!/usr/bin/env python3
"""
CapRover Automation Helper for Hermes Agent.

Provides a unified interface to authenticate, inspect, manage apps,
and deploy one-click database services to CapRover via the v2 REST API.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional


class CapRoverClient:
    """Lightweight CapRover HTTP Client using standard library urllib."""

    def __init__(self, base_url: str, password: Optional[str] = None, token: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.password = password
        self.token = token
        if not self.token and self.password:
            self.login()

    def _request(self, endpoint: str, method: str = "GET", data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v2{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "x-namespace": "captain",
        }
        if self.token:
            headers["x-captain-auth"] = self.token

        body = json.dumps(data).encode("utf-8") if data else None
        req = urllib.request.Request(url, data=body, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                if res_data.get("status") != 100:
                    raise RuntimeError(f"CapRover API Error: {res_data.get('description', 'Unknown error')}")
                return res_data.get("data", {})
        except urllib.error.HTTPError as exc:
            err_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code}: {err_body}") from exc

    def login(self) -> str:
        """Authenticate with CapRover password and get auth token."""
        res = self._request("/login", method="POST", data={"password": self.password})
        self.token = res.get("token")
        return self.token

    def list_apps(self) -> list[Dict[str, Any]]:
        """List all deployed applications."""
        res = self._request("/user/apps/appDefinitions", method="GET")
        return res.get("appDefinitions", [])

    def create_app(self, app_name: str, has_persistent_data: bool = False) -> Dict[str, Any]:
        """Create a new CapRover app definition."""
        return self._request(
            "/user/apps/appDefinitions/register",
            method="POST",
            data={
                "appName": app_name,
                "hasPersistentData": has_persistent_data,
            },
        )

    def set_env_vars(self, app_name: str, env_vars: Dict[str, str]) -> Dict[str, Any]:
        """Update or set environment variables on an existing app."""
        formatted_vars = [{"key": k, "value": v} for k, v in env_vars.items()]
        return self._request(
            "/user/apps/appDefinitions/update",
            method="POST",
            data={
                "appName": app_name,
                "envVars": formatted_vars,
            },
        )

    def enable_ssl(self, app_name: str) -> Dict[str, Any]:
        """Enable HTTPS / Let's Encrypt SSL certificate for default subdomain."""
        return self._request(
            "/user/apps/appDefinitions/enableSsl",
            method="POST",
            data={"appName": app_name},
        )


def generate_captain_definition(template_type: str, output_path: str = "./captain-definition") -> None:
    """Generate a boilerplate captain-definition file."""
    templates = {
        "dockerfile": {"schemaVersion": 2, "dockerfilePath": "./Dockerfile"},
        "node": {"schemaVersion": 2, "template": "node/20"},
        "python": {"schemaVersion": 2, "template": "python/3.11"},
        "static": {"schemaVersion": 2, "template": "static/latest"},
    }
    definition = templates.get(template_type.lower(), templates["dockerfile"])
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(definition, f, indent=2)
    print(f"Generated {output_path} with template '{template_type}'")


def main() -> None:
    parser = argparse.ArgumentParser(description="CapRover Helper CLI for Hermes Agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Init definition
    init_parser = subparsers.add_parser("init-definition", help="Generate captain-definition file")
    init_parser.add_argument("--type", choices=["dockerfile", "node", "python", "static"], default="dockerfile")
    init_parser.add_argument("--output", default="./captain-definition")

    # List apps
    list_parser = subparsers.add_parser("list", help="List deployed apps")
    list_parser.add_argument("--url", default=os.getenv("CAPROVER_URL", "http://captain.localhost:3000"))
    list_parser.add_argument("--password", default=os.getenv("CAPROVER_PASSWORD", ""))

    # Create app
    create_parser = subparsers.add_parser("create-app", help="Register a new app")
    create_parser.add_argument("--name", required=True)
    create_parser.add_argument("--persistent", action="store_true")
    create_parser.add_argument("--url", default=os.getenv("CAPROVER_URL", "http://captain.localhost:3000"))
    create_parser.add_argument("--password", default=os.getenv("CAPROVER_PASSWORD", ""))

    # Set env
    env_parser = subparsers.add_parser("set-env", help="Set environment variables")
    env_parser.add_argument("--name", required=True)
    env_parser.add_argument("--vars", required=True, help="JSON dictionary of env vars, e.g. '{\"PORT\":\"80\"}'")
    env_parser.add_argument("--url", default=os.getenv("CAPROVER_URL", "http://captain.localhost:3000"))
    env_parser.add_argument("--password", default=os.getenv("CAPROVER_PASSWORD", ""))

    args = parser.parse_args()

    if args.command == "init-definition":
        generate_captain_definition(args.type, args.output)
        return

    client = CapRoverClient(base_url=args.url, password=args.password)

    if args.command == "list":
        apps = client.list_apps()
        print(json.dumps(apps, indent=2))
    elif args.command == "create-app":
        res = client.create_app(args.name, has_persistent_data=args.persistent)
        print(f"Created app '{args.name}' successfully.")
    elif args.command == "set-env":
        env_dict = json.loads(args.vars)
        client.set_env_vars(args.name, env_dict)
        print(f"Updated environment variables for '{args.name}'.")


if __name__ == "__main__":
    main()
