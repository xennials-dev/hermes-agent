# 📡 Uptime Kuma TLS Watch (`uptime-kuma-sec`)

**Stack A · Service #15: Cyber Security Package (`TS101-SRV-15`)**

- **Role:** 24/7 SSL/TLS certificate expiry, DNS, port & HTTP security availability monitor
- **Upstream Repo:** https://github.com/louislam/uptime-kuma
- **License:** MIT
- **Local App URL:** http://localhost:7530
- **One-Click Hub Launch Link:** `http://localhost:7879/t/uptime-kuma-sec`
- **Estimated RAM:** ~250 MB

## Run Standalone (Independent of Hub)

```bash
cp .env.example .env
docker compose up -d
```

## First-Run Notes
Create your local admin login and add TLS expiry alerts (14d / 7d) + n8n webhook notifications.
