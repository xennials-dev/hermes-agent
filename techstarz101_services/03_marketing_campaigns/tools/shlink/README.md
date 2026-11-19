# 🔗 Shlink (Standalone Tool Repo)

- **Role:** Self-hosted campaign shortlinks & multi-angle ad click attribution
- **Stack:** Stack A
- **Upstream Open-Source Repo:** https://github.com/shlinkio/shlink (MIT)
- **Dedicated Launch Link (Auto-Boots & Opens):** http://localhost:7867/t/shlink
- **Direct Application Port:** http://localhost:5330
- **Live Production VPS:** http://2.25.238.185:8090

## Run Individually (One Click via Hub)
1. Start the Service #03 Hub: `python techstarz101_services/03_marketing_campaigns/hub/app.py`
2. Click **[http://localhost:7867/t/shlink](http://localhost:7867/t/shlink)** (or click the 🔗 icon on the Hub).

## Run Individually (Standalone Docker Compose)
```bash
cd techstarz101_services/03_marketing_campaigns/tools/shlink
docker compose up -d
```

## First-Run Notes
Shlink API + Shlink Web Client are wired together; use the INITIAL_API_KEY in tools/shlink/.env.
