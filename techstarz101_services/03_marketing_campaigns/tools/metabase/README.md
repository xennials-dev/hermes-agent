# 📉 Metabase (Standalone Tool Repo)

- **Role:** Executive ROAS, CAC & multi-angle A/B ad performance BI dashboards
- **Stack:** Stack B
- **Upstream Open-Source Repo:** https://github.com/metabase/metabase (AGPL-3.0)
- **Dedicated Launch Link (Auto-Boots & Opens):** http://localhost:7867/t/metabase
- **Direct Application Port:** http://localhost:5430

## Run Individually (One Click via Hub)
1. Start the Service #03 Hub: `python techstarz101_services/03_marketing_campaigns/hub/app.py`
2. Click **[http://localhost:7867/t/metabase](http://localhost:7867/t/metabase)** (or click the 📉 icon on the Hub).

## Run Individually (Standalone Docker Compose)
```bash
cd techstarz101_services/03_marketing_campaigns/tools/metabase
docker compose up -d
```

## First-Run Notes
Create your local admin account on first visit and connect your campaign PostgreSQL / MySQL DBs.
