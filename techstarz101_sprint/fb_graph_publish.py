#!/usr/bin/env python3
"""
Direct Meta Graph API Publisher for Techstarz101 Facebook Page.
Page ID: 1378188408719025 (techstarz101)
"""

import sys
import json
import urllib.request
import urllib.parse

PAGE_ID = "1378188408719025"

DEFAULT_POST = (
    "Stop renting your software. Own your AI stack.\n\n"
    "At Techstarz101.com, we build sovereign AI systems (n8n, Twenty CRM, Listmonk, Hermes) "
    "that cut SaaS bloat.\n\n"
    "Flat $390 48-hour starter sprint: https://techstarz101.com/intake.html"
)

def publish(token: str, message: str = DEFAULT_POST, link: str = "https://techstarz101.com/intake.html"):
    url = f"https://graph.facebook.com/v19.0/{PAGE_ID}/feed"
    payload = urllib.parse.urlencode({
        "message": message,
        "link": link,
        "access_token": token
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            print("\n🎉 SUCCESS! Published to Facebook Page:")
            print(f"Post ID: {data.get('id')}")
            print(f"View Post: https://www.facebook.com/{data.get('id')}")
            return data
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        print(f"\n❌ Meta API Error: {err}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python techstarz101_sprint/fb_graph_publish.py <PAGE_ACCESS_TOKEN>")
        sys.exit(1)
    publish(sys.argv[1].strip())

