# 🧱 CrowdSec IPS & LAPI (`crowdsec-ips`)

**Stack B · Service #15: Cyber Security Package (`TS101-SRV-15`)**

- **Role:** Collaborative open-source intrusion prevention system blocking brute-force & bad IPs
- **Upstream Repo:** https://github.com/crowdsecurity/crowdsec
- **License:** MIT
- **Local App URL:** http://localhost:7600/health
- **One-Click Hub Launch Link:** `http://localhost:7879/t/crowdsec-ips`
- **Estimated RAM:** ~300 MB

## Run Standalone (Independent of Hub)

```bash
cp .env.example .env
docker compose up -d
```

## First-Run Notes
Exposes CrowdSec Local API (LAPI) on :7600 for Nginx/Firewall bouncers and n8n threat alerts.
