import urllib.request
import re

urls = {
    "abstrakt": "https://abstraktmg.com/contact/",
    "gorilla76": "https://gorilla76.com/contact/",
    "atomicdust": "https://atomicdust.com/contact/",
    "steadyrain": "https://steadyrain.com/more/contact-us",
    "digitalstrike": "https://digitalstrike.com/contact-us/"
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

for name, u in urls.items():
    print(f"\n--- Checking {name} ({u}) ---")
    try:
        req = urllib.request.Request(u, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            html = r.read().decode('utf-8', errors='ignore')
            forms = re.findall(r'<form\b[^>]*>(.*?)</form>', html, re.DOTALL | re.IGNORECASE)
            print(f"Found {len(forms)} form(s)")
            for i, f in enumerate(forms):
                inputs = re.findall(r'<(?:input|textarea|select)\b([^>]*)>', f, re.IGNORECASE)
                names = []
                for inp in inputs:
                    m = re.search(r'name=["\']([^"\']+)["\']', inp)
                    if m and 'hidden' not in inp.lower():
                        names.append(m.group(1))
                print(f"  Form {i+1} field names: {names[:10]}")
    except Exception as e:
        print(f"Error checking {name}: {e}")
