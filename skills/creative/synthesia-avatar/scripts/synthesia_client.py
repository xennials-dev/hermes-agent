#!/usr/bin/env python3
"""Synthesia Interactive Avatars client.

Provides CLI commands and programmatic access for managing Synthesia
Interactive Avatars: provisioning avatars from Studio source IDs, polling
generation status, validating API keys, and starting WebRTC/LiveKit sessions.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_BASE_URL = "https://developers.synthesia.io/api"


class SynthesiaError(Exception):
    """Raised when the Synthesia API returns an error response."""

    def __init__(self, status: int, title: str, code: str, detail: Any, request_id: Optional[str] = None):
        super().__init__(f"[{status}] {code}: {detail or title}")
        self.status = status
        self.title = title
        self.code = code
        self.detail = detail
        self.request_id = request_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "title": self.title,
            "code": self.code,
            "detail": self.detail,
            "request_id": self.request_id,
        }


def _load_env_key(key: str) -> Optional[str]:
    """Look up key in os.environ, local .env, and ~/.hermes/.env."""
    if val := os.getenv(key):
        return val
    # Check current directory and parents for .env
    candidates = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parents[4] / ".env",
        Path.home() / ".hermes" / ".env",
    ]
    for env_path in candidates:
        if env_path.is_file():
            try:
                for line in env_path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line.startswith(f"{key}="):
                        val = line.split("=", 1)[1].strip().strip("'\"")
                        if val:
                            return val
            except Exception:
                continue
    return None


class SynthesiaClient:
    """Client for Synthesia Interactive Avatars API."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or _load_env_key("SYNTHESIA_API_KEY")
        if not self.api_key:
            raise ValueError("SYNTHESIA_API_KEY is required. Set it in .env or pass --api-key.")
        self.base_url = (base_url or _load_env_key("SYNTHESIA_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")

    def _request(self, endpoint: str, data: Optional[Dict[str, Any]] = None, method: str = "POST") -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        payload = json.dumps(data).encode("utf-8") if data is not None else None
        headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "Hermes-Agent/1.0",
        }

        req = urllib.request.Request(url, data=payload, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body) if body else {}
        except urllib.error.HTTPError as err:
            err_body = err.read().decode("utf-8")
            request_id = err.headers.get("Request-Id")
            try:
                prob = json.loads(err_body)
                raise SynthesiaError(
                    status=prob.get("status", err.code),
                    title=prob.get("title", err.reason),
                    code=prob.get("code", "unknown_error"),
                    detail=prob.get("detail", err_body),
                    request_id=request_id or prob.get("requestId"),
                ) from err
            except json.JSONDecodeError:
                raise SynthesiaError(
                    status=err.code,
                    title=err.reason,
                    code="http_error",
                    detail=err_body,
                    request_id=request_id,
                ) from err

    def validate_key(self) -> Dict[str, Any]:
        """Validate API key reachability against the sessions endpoint."""
        try:
            self._request("/interactive-avatars/sessions", data={})
            return {"valid": True, "message": "Key is valid and active."}
        except SynthesiaError as err:
            if err.status == 400:
                # 400 indicates authentication was accepted but request body lacked fields
                return {"valid": True, "message": "Key authenticated successfully.", "request_id": err.request_id}
            if err.status in (401, 403):
                return {"valid": False, "status": err.status, "code": err.code, "detail": err.detail}
            raise

    def provision_avatar(self, source_id: str, regenerate: bool = False) -> Dict[str, Any]:
        """Create or fetch an interactive avatar from a Studio source ID."""
        return self._request(
            "/interactive-avatars/avatars",
            data={"sourceId": source_id, "regenerate": regenerate},
        )

    def get_avatar_status(self, source_id: str) -> Dict[str, Any]:
        """Poll the current generation status of an interactive avatar."""
        return self.provision_avatar(source_id=source_id, regenerate=False)

    def start_session(
        self,
        avatar_ids: List[str],
        livekit_url: str,
        livekit_token: str,
    ) -> Dict[str, Any]:
        """Start a real-time interactive avatar streaming session."""
        return self._request(
            "/interactive-avatars/sessions",
            data={
                "avatarIds": avatar_ids,
                "livekitUrl": livekit_url,
                "livekitToken": livekit_token,
            },
        )


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Synthesia Interactive Avatars CLI")
    parser.add_argument("--api-key", help="Synthesia API key (defaults to SYNTHESIA_API_KEY env var)")
    parser.add_argument("--base-url", help="Base URL for Synthesia Interactive Avatars API")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # validate
    subparsers.add_parser("validate-key", help="Validate Synthesia API key authentication")

    # provision-avatar
    prov_parser = subparsers.add_parser("provision-avatar", help="Provision or poll an interactive avatar")
    prov_parser.add_argument("--source-id", required=True, help="Studio avatar ID (e.g. av_6c9edb85a2f947e5)")
    prov_parser.add_argument("--regenerate", action="store_true", help="Force new generation")

    # avatar-status
    stat_parser = subparsers.add_parser("avatar-status", help="Get avatar generation status")
    stat_parser.add_argument("--source-id", required=True, help="Studio avatar ID (e.g. av_6c9edb85a2f947e5)")

    # start-session
    sess_parser = subparsers.add_parser("start-session", help="Start an interactive avatar streaming session")
    sess_parser.add_argument("--avatar-id", action="append", required=True, dest="avatar_ids", help="Avatar ID(s)")
    sess_parser.add_argument("--livekit-url", required=True, help="LiveKit server WebSocket URL (wss://...)")
    sess_parser.add_argument("--livekit-token", required=True, help="LiveKit client access token")

    args = parser.parse_args(argv)

    try:
        client = SynthesiaClient(api_key=args.api_key, base_url=args.base_url)
        if args.command == "validate-key":
            result = client.validate_key()
            print(json.dumps(result, indent=2))
            return 0 if result.get("valid") else 1

        if args.command == "provision-avatar":
            result = client.provision_avatar(args.source_id, regenerate=args.regenerate)
            print(json.dumps(result, indent=2))
            return 0

        if args.command == "avatar-status":
            result = client.get_avatar_status(args.source_id)
            print(json.dumps(result, indent=2))
            return 0

        if args.command == "start-session":
            result = client.start_session(
                avatar_ids=args.avatar_ids,
                livekit_url=args.livekit_url,
                livekit_token=args.livekit_token,
            )
            print(json.dumps(result, indent=2))
            return 0

    except SynthesiaError as err:
        print(json.dumps({"error": err.to_dict()}, indent=2), file=sys.stderr)
        return 1
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, indent=2), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
