import urllib.request
import re

req = urllib.request.Request("https://digitalstrike.com/", headers={"User-Agent": "Mozilla/5.0"})
try:
    with urllib.request.urlopen(req, timeout=10) as r:
        html = r.read().decode('utf-8', errors='ignore')
        links = re.findall(r'href=["\'](https?://[^"\']*contact[^"\']*)["\']', html, re.I)
        print("Digital Strike contact links:", set(links))
        if not links:
            links2 = re.findall(r'href=["\'](/[^"\']*contact[^"\']*)["\']', html, re.I)
            print("Relative links:", set(links2))
except Exception as e:
    print("Error:", e)

