# 📊 Matomo (Standalone Tool Repo)

- **Role:** Full open-source Google Analytics & campaign funnel attribution suite
- **Stack:** Stack B
- **Upstream Open-Source Repo:** https://github.com/matomo-org/matomo (GPL-3.0)
- **Dedicated Launch Link (Auto-Boots & Opens):** http://localhost:7867/t/matomo
- **Direct Application Port:** http://localhost:5410

## Run Individually (One Click via Hub)
1. Start the Service #03 Hub: `python techstarz101_services/03_marketing_campaigns/hub/app.py`
2. Click **[http://localhost:7867/t/matomo](http://localhost:7867/t/matomo)** (or click the 📊 icon on the Hub).

## Run Individually (Standalone Docker Compose)
```bash
cd techstarz101_services/03_marketing_campaigns/tools/matomo
docker compose up -d
```

## First-Run Notes
Follow the quick Matomo setup wizard; DB host is 'matomo-db' with credentials from tools/matomo/.env.
