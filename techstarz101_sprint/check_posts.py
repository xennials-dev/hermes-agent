import urllib.request
import json
import os
from pathlib import Path

env_path = Path.home() / "AppData" / "Local" / "hermes" / ".env"
env = {}
for line in env_path.read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")

api_key = env.get("POSTIZ_API_KEY", "")
base_url = env.get("POSTIZ_BASE_URL", "http://2.25.238.185:4200/public/v1")

req = urllib.request.Request(f"{base_url}/posts", headers={"Authorization": api_key, "Accept": "application/json"})
try:
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read().decode())
        print(json.dumps(data, indent=2)[:1000])
except Exception as e:
    print("Error:", e)

