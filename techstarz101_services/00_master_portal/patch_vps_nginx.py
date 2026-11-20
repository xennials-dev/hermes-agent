from pathlib import Path

p = Path("/etc/nginx/sites-available/techstarz101.com")
bak = Path("/etc/nginx/sites-available/techstarz101.com.bak")
if bak.exists():
    txt = bak.read_text(encoding="utf-8")
else:
    txt = p.read_text(encoding="utf-8")
    bak.write_text(txt, encoding="utf-8")

snippet = """    # Techstarz101 Workstation Automatic Fallback Portal
    location = /workstation {
        return 301 /workstation/;
    }
    location ^~ /workstation/ {
        proxy_pass http://127.0.0.1:7860/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }
    location ^~ /apps/cyberchef/ {
        proxy_pass http://127.0.0.1:7620/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    location ^~ /apps/adminer/ {
        proxy_pass http://127.0.0.1:6230/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    location ^~ /apps/mailpit/ {
        proxy_pass http://127.0.0.1:6120/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Twenty CRM reverse proxy"""

if "location ^~ /workstation/" not in txt:
    txt = txt.replace("    # Twenty CRM reverse proxy", snippet, 1)
p.write_text(txt, encoding="utf-8")
print("PATCHED_CLEANLY")
