---
name: sherlock-osint
description: "Search usernames across 400+ platforms for OSINT analysis."
version: 1.0.0
author: Terrance (tee), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [OSINT, Reconnaissance, Sherlock, Research, Investigation]
    related_skills: [web-extraction, find-clients]
---

# Sherlock OSINT Username Investigation

Perform open-source intelligence (OSINT) username discovery across 400+ social networks, forums, and developer platforms.

---

## 1. Quick Reference

| Action | Command |
|---|---|
| **Install Sherlock** | `pip install sherlock-project` |
| **Search Single Target** | `sherlock target_username` |
| **Search Multiple Targets** | `sherlock user1 user2 user3` |
| **Export to CSV / JSON** | `sherlock target_username --csv --json results.json` |
| **Filter by Category** | `sherlock target_username --site github,twitter,reddit` |

---

## 2. Python Automation

```python
import subprocess
import json

def search_username(username: str, timeout: int = 60) -> list[str]:
    cmd = ["sherlock", username, "--print-found", "--timeout", str(timeout)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    found_urls = [line.strip() for line in res.stdout.splitlines() if line.startswith("http")]
    return found_urls
```
