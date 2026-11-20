# 🕷️ OWASP ZAP DAST (`owasp-zap`)

**Stack A · Service #15: Cyber Security Package (`TS101-SRV-15`)**

- **Role:** Authorized web & API vulnerability scanner with headless REST API & WebSwing UI
- **Upstream Repo:** https://github.com/zaproxy/zaproxy
- **License:** Apache-2.0
- **Local App URL:** http://localhost:7500/zap
- **One-Click Hub Launch Link:** `http://localhost:7879/t/owasp-zap`
- **Estimated RAM:** ~1100 MB

## Run Standalone (Independent of Hub)

```bash
cp .env.example .env
docker compose up -d
```

## First-Run Notes
Open /zap for the interactive OWASP ZAP WebSwing console to run authorized baseline scans.
