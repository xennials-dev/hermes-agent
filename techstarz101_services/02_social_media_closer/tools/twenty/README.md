# 🗂️ Twenty CRM (Standalone Tool Repo)

- **Role:** System of record for leads and deals closed from DMs
- **Stack:** Stack A
- **Upstream Open-Source Repo:** https://github.com/twentyhq/twenty (AGPL-3.0)
- **Dedicated Launch Link (Auto-Boots & Opens):** http://localhost:7866/t/twenty
- **Direct Application Port:** http://localhost:5140
- **Live Production VPS:** http://2.25.238.185:3002

## Run Individually (One Click via Hub)
1. Start the Service #02 Hub: `python techstarz101_services/02_social_media_closer/hub/app.py`
2. Click **[http://localhost:7866/t/twenty](http://localhost:7866/t/twenty)** (or click the 🗂️ icon on the Hub).

## Run Individually (Standalone Docker Compose)
```bash
cd techstarz101_services/02_social_media_closer/tools/twenty
docker compose up -d
```

## First-Run Notes
Create a workspace on first visit. Settings > APIs & Webhooks > create an API key for the closer automation.
