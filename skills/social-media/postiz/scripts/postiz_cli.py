#!/usr/bin/env python3
"""Postiz Public API (/public/v1) CLI for Techstarz 101 & Hermes Agent."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.request


def _load_hermes_env() -> None:
    env_candidates = [
        Path(os.environ.get("HERMES_HOME", "")) / ".env" if os.environ.get("HERMES_HOME") else None,
        Path.home() / "AppData" / "Local" / "hermes" / ".env",
        Path.home() / ".hermes" / ".env",
    ]
    for env_path in env_candidates:
        if env_path and env_path.is_file():
            for raw_line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def _request(method: str, path: str, api_key: str, base_url: str, payload: dict | None = None) -> object:
    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "HermesAgent-Techstarz101/1.0",
    }
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Postiz API HTTP {exc.code} on {method} {url}: {err_body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach Postiz at {url}: {exc.reason}") from exc


def cmd_channels(args: argparse.Namespace, api_key: str, base_url: str) -> int:
    if args.dry_run or not api_key:
        print("⚠ POSTIZ_API_KEY not set (or --dry-run active). Showing simulated Techstarz101 channel roster:")
        sample = [
            {"id": "ch_x_techstarz101", "identifier": "x", "name": "Techstarz 101 (@techstarz101)"},
            {"id": "ch_tiktok_techstarz101", "identifier": "tiktok", "name": "Techstarz 101 (@techstarz101)"},
            {"id": "ch_reddit_techstarz101", "identifier": "reddit", "name": "u/techstarz101"},
            {"id": "ch_discord_techstarz101", "identifier": "discord", "name": "Techstarz 101 Server"},
            {"id": "ch_linkedin_techstarz101", "identifier": "linkedin-page", "name": "Techstarz 101"},
            {"id": "ch_youtube_techstarz101", "identifier": "youtube", "name": "Techstarz 101"},
        ]
        print(json.dumps(sample, indent=2))
        return 0

    integrations = _request("GET", "/integrations", api_key, base_url)
    print(json.dumps(integrations, indent=2))
    return 0


def cmd_post(args: argparse.Namespace, api_key: str, base_url: str) -> int:
    post_date = args.date or (dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    wanted_platforms = [p.strip().lower() for p in args.platforms.split(",") if p.strip()] if args.platforms else []

    if args.dry_run or not api_key:
        integrations = [
            {"id": "ch_x_techstarz101", "identifier": "x", "name": "X (@techstarz101)"},
            {"id": "ch_linkedin_techstarz101", "identifier": "linkedin-page", "name": "LinkedIn (Techstarz 101)"},
            {"id": "ch_reddit_techstarz101", "identifier": "reddit", "name": "Reddit (u/techstarz101)"},
            {"id": "ch_tiktok_techstarz101", "identifier": "tiktok", "name": "TikTok (@techstarz101)"},
            {"id": "ch_discord_techstarz101", "identifier": "discord", "name": "Discord (Techstarz 101)"},
        ]
    else:
        raw = _request("GET", "/integrations", api_key, base_url)
        integrations = raw if isinstance(raw, list) else raw.get("integrations", [])

    if wanted_platforms:
        integrations = [
            ch for ch in integrations
            if any(p in str(ch.get("identifier", "")).lower() or p in str(ch.get("id", "")).lower() for p in wanted_platforms)
        ]

    if not integrations:
        print("✗ No matching Postiz integrations found.", file=sys.stderr)
        return 1

    images = [{"url": u.strip()} for u in (args.media or "").split(",") if u.strip()]
    value_items = [{"content": args.content, "image": images}]
    for follow_up in args.thread or []:
        value_items.append({"content": follow_up, "image": []})

    posts_payload = []
    for ch in integrations:
        provider = str(ch.get("identifier", "x"))
        posts_payload.append({
            "integration": {"id": ch["id"]},
            "value": value_items,
            "settings": {"__type": provider},
        })

    body = {
        "type": args.type,
        "date": post_date,
        "shortLink": False,
        "tags": [],
        "posts": posts_payload,
    }

    if args.dry_run or not api_key:
        print("✓ [DRY-RUN] Generated Postiz /public/v1/posts payload:")
        print(json.dumps(body, indent=2))
        return 0

    result = _request("POST", "/posts", api_key, base_url, payload=body)
    print("✓ Postiz broadcast submitted successfully:")
    print(json.dumps(result, indent=2))
    return 0


def main() -> int:
    _load_hermes_env()
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--api-key", default=os.environ.get("POSTIZ_API_KEY", ""))
    common.add_argument(
        "--base-url",
        default=os.environ.get("POSTIZ_BASE_URL", "http://2.25.238.185:4200/api/public/v1"),
    )
    common.add_argument("--dry-run", action="store_true", help="Print payload without calling remote API")

    parser = argparse.ArgumentParser(
        description="Postiz Multi-Channel Publisher for Techstarz 101",
        parents=[common],
    )

    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("channels", parents=[common], help="List connected Postiz social channels")

    p_post = sub.add_parser("post", parents=[common], help="Publish or schedule a multi-channel post")
    p_post.add_argument("--type", choices=["now", "schedule", "draft"], default="now")
    p_post.add_argument("--date", help="ISO-8601 UTC timestamp (e.g. 2026-11-18T14:00:00.000Z)")
    p_post.add_argument("--platforms", help="Comma-separated filter (e.g. x,linkedin,reddit,tiktok,discord)")
    p_post.add_argument("--content", required=True, help="Primary post copy")
    p_post.add_argument("--thread", action="append", help="Optional threaded follow-up comment(s)")
    p_post.add_argument("--media", help="Comma-separated public media URL(s)")

    args = parser.parse_args()
    if args.command == "channels":
        return cmd_channels(args, args.api_key, args.base_url)
    if args.command == "post":
        return cmd_post(args, args.api_key, args.base_url)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
