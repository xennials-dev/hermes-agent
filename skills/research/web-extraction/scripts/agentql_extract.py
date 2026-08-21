#!/usr/bin/env python3
"""
AgentQL Standalone Web Extraction Script for Hermes Agent.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


def extract(url: str, prompt: str, api_key: str, output_path: str = None) -> dict:
    req_data = {
        "url": url,
        "prompt": prompt,
    }
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key,
    }
    req = urllib.request.Request(
        "https://api.agentql.com/v1/query-data",
        data=json.dumps(req_data).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
            if output_path:
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2)
                print(f"Saved results to {output_path}")
            return result
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode("utf-8")
        print(f"HTTP Error {e.code}: {error_msg}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="AgentQL Web Extraction")
    parser.add_argument("--url", required=True, help="Target URL to extract from")
    parser.add_argument("--prompt", required=True, help="Natural language description of data to extract")
    parser.add_argument("--output", help="Optional output JSON file")
    parser.add_argument("--api-key", default=os.getenv("AGENTQL_API_KEY"), help="AgentQL API key")

    args = parser.parse_args()
    if not args.api_key:
        print("Error: AGENTQL_API_KEY is required. Pass --api-key or set in environment.", file=sys.stderr)
        sys.exit(1)

    res = extract(args.url, args.prompt, args.api_key, args.output)
    if not args.output:
        print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
