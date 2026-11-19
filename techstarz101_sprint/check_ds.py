import urllib.request
import re

req = urllib.request.Request("https://www.digitalstrike.com/contact/", headers={"User-Agent": "Mozilla/5.0"})
try:
    with urllib.request.urlopen(req, timeout=10) as r:
        html = r.read().decode('utf-8', errors='ignore')
        forms = re.findall(r'<form\b[^>]*>(.*?)</form>', html, re.DOTALL | re.IGNORECASE)
        print(f"Digital strike forms: {len(forms)}")
        for i, f in enumerate(forms):
            inputs = re.findall(r'<(?:input|textarea|select)\b([^>]*)>', f, re.IGNORECASE)
            names = []
            for inp in inputs:
                m = re.search(r'name=["\']([^"\']+)["\']', inp)
                if m and 'hidden' not in inp.lower():
                    names.append(m.group(1))
            print(f"  Form {i+1} field names: {names[:10]}")
except Exception as e:
    print("Error:", e)

