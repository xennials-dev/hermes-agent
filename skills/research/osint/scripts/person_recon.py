#!/usr/bin/env python3
"""
OSINT Person Reconnaissance Tool
Aggregates open-source intelligence on persons, usernames, emails, and phone numbers.
Based on the Awesome OSINT taxonomy (https://github.com/jivoi/awesome-osint).
"""

import sys
import os
import json
import re
import hashlib
import argparse
import urllib.request
import urllib.error
from typing import Dict, List, Any, Optional

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

# Major platforms to probe for username existence
PLATFORMS = {
    "GitHub": "https://github.com/{}",
    "Reddit": "https://www.reddit.com/user/{}/about.json",
    "GitLab": "https://gitlab.com/{}",
    "HackerNews": "https://news.ycombinator.com/user?id={}",
    "Keybase": "https://keybase.io/{}",
    "Medium": "https://medium.com/@{}",
    "Dev.to": "https://dev.to/{}",
    "Pinterest": "https://www.pinterest.com/{}/",
    "Steam": "https://steamcommunity.com/id/{}",
    "Telegram": "https://t.me/{}",
    "Gravatar": "https://en.gravatar.com/{}",
    "DockerHub": "https://hub.docker.com/u/{}/",
    "PyPI": "https://pypi.org/user/{}/",
    "npm": "https://www.npmjs.com/~{}",
}

def probe_url(url: str, timeout: int = 4) -> bool:
    """Check if URL exists (returns HTTP 200)."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/json"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except urllib.error.HTTPError as e:
        if e.code in (404, 410):
            return False
        return False
    except Exception:
        return False

def check_username(username: str) -> Dict[str, Any]:
    """Probe username availability and profiles across top platforms."""
    results = {"username": username, "matches": [], "searched": len(PLATFORMS)}
    for platform, url_tmpl in PLATFORMS.items():
        url = url_tmpl.format(username)
        # For Reddit json endpoint
        check_url = f"https://www.reddit.com/user/{username}" if platform == "Reddit" else url
        if probe_url(url):
            results["matches"].append({"platform": platform, "url": check_url, "status": "FOUND"})
    return results

def check_email(email: str) -> Dict[str, Any]:
    """Extract OSINT signals from an email address."""
    results = {"email": email, "gravatar": None, "domain_info": {}}
    if "@" not in email:
        return results
    
    local, domain = email.strip().lower().split("@", 1)
    results["domain_info"]["domain"] = domain
    results["domain_info"]["username_candidate"] = local

    # Gravatar Hash
    md5_hash = hashlib.md5(email.strip().lower().encode("utf-8")).hexdigest()
    gravatar_profile_url = f"https://en.gravatar.com/{md5_hash}.json"
    gravatar_img_url = f"https://www.gravatar.com/avatar/{md5_hash}?d=404"

    if probe_url(gravatar_img_url):
        results["gravatar"] = {
            "avatar_url": f"https://www.gravatar.com/avatar/{md5_hash}",
            "profile_url": f"https://en.gravatar.com/{md5_hash}",
        }
        try:
            req = urllib.request.Request(gravatar_profile_url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=4) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                entry = data.get("entry", [{}])[0]
                results["gravatar"]["display_name"] = entry.get("displayName")
                results["gravatar"]["preferred_username"] = entry.get("preferredUsername")
                results["gravatar"]["about_me"] = entry.get("aboutMe")
                results["gravatar"]["urls"] = entry.get("urls", [])
        except Exception:
            pass
            
    return results

def check_phone(phone: str) -> Dict[str, Any]:
    """Parse and extract country/format information from a phone number."""
    cleaned = re.sub(r"[^\d+]", "", phone)
    return {
        "raw": phone,
        "normalized": cleaned,
        "is_e164": cleaned.startswith("+"),
        "digits_length": len(re.sub(r"[^\d]", "", cleaned)),
        "resources": [
            f"https://freecarrierlookup.com",
            f"https://www.numverify.com",
            f"https://sync.me/search/?number={cleaned}",
            f"https://www.truecaller.com/search/{cleaned}",
        ]
    }

def format_markdown(data: Dict[str, Any]) -> str:
    """Format OSINT findings into an executive intelligence report."""
    md = ["# 🔍 OSINT Intelligence Dossier\n"]
    
    if "username" in data:
        u = data["username"]
        md.append(f"## 👤 Username Recon: `{u.get('username')}`")
        matches = u.get("matches", [])
        if matches:
            md.append(f"Found **{len(matches)}** verified digital profile(s):\n")
            for m in matches:
                md.append(f"- **{m['platform']}**: [{m['url']}]({m['url']})")
        else:
            md.append("No active profiles confirmed on core probed platforms.")
        md.append("")

    if "email" in data:
        e = data["email"]
        md.append(f"## ✉️ Email Intelligence: `{e.get('email')}`")
        if e.get("gravatar"):
            g = e["gravatar"]
            md.append(f"- **Gravatar Found**: [{g['profile_url']}]({g['profile_url']})")
            if g.get("display_name"):
                md.append(f"- **Display Name**: {g['display_name']}")
            if g.get("about_me"):
                md.append(f"- **Bio**: {g['about_me']}")
        else:
            md.append("- No public Gravatar profile linked.")
        md.append("")

    if "phone" in data:
        p = data["phone"]
        md.append(f"## 📞 Phone OSINT: `{p.get('normalized')}`")
        md.append(f"- Format E.164: {'Yes' if p.get('is_e164') else 'No'}")
        md.append(f"- Digits: {p.get('digits_length')}")
        md.append("- External Verification Handlers:")
        for r in p.get("resources", []):
            md.append(f"  - {r}")
        md.append("")

    return "\n".join(md)

def main():
    parser = argparse.ArgumentParser(description="Awesome OSINT Person Reconnaissance Engine")
    parser.add_argument("--username", "-u", help="Username or handle to investigate")
    parser.add_argument("--email", "-e", help="Email address to probe")
    parser.add_argument("--phone", "-p", help="Phone number to analyze")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    if not (args.username or args.email or args.phone):
        parser.print_help()
        sys.exit(1)

    output = {}
    if args.username:
        output["username"] = check_username(args.username)
    if args.email:
        output["email"] = check_email(args.email)
    if args.phone:
        output["phone"] = check_phone(args.phone)

    if args.json:
        print(json.dumps(output, indent=2))
    else:
        print(format_markdown(output))

if __name__ == "__main__":
    main()
