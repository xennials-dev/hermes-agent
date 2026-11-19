# 🟢 Uptime Kuma (Standalone Tool Repo)

- **Role:** Real-time website, SSL certificate & DNS uptime monitoring + status pages
- **Stack:** Stack B
- **Upstream Open-Source Repo:** https://github.com/louislam/uptime-kuma (MIT)
- **Dedicated Launch Link (Auto-Boots & Opens):** http://localhost:7868/t/uptime-kuma
- **Direct Application Port:** http://localhost:5630

## Run Individually (One Click via Hub)
1. Start the Service #04 Hub: `python techstarz101_services/04_brand_web_launch/hub/app.py`
2. Click **[http://localhost:7868/t/uptime-kuma](http://localhost:7868/t/uptime-kuma)** (or click the 🟢 icon on the Hub).

## Run Individually (Standalone Docker Compose)
```bash
cd techstarz101_services/04_brand_web_launch/tools/uptime-kuma
docker compose up -d
```

## First-Run Notes
Create your local admin password on first visit and add monitors for your live deployed domains.
