# 📇 EspoCRM (Standalone Tool Repo)

- **Role:** Lightweight CRM for leads, opportunities and follow-up tasks
- **Stack:** Stack B
- **Upstream Open-Source Repo:** https://github.com/espocrm/espocrm (AGPL-3.0)
- **Dedicated Launch Link (Auto-Boots & Opens):** http://localhost:7866/t/espocrm
- **Direct Application Port:** http://localhost:5230

## Run Individually (One Click via Hub)
1. Start the Service #02 Hub: `python techstarz101_services/02_social_media_closer/hub/app.py`
2. Click **[http://localhost:7866/t/espocrm](http://localhost:7866/t/espocrm)** (or click the 📇 icon on the Hub).

## Run Individually (Standalone Docker Compose)
```bash
cd techstarz101_services/02_social_media_closer/tools/espocrm
docker compose up -d
```

## First-Run Notes
Log in with username 'admin' and the generated password shown on the hub card (stored in tools/espocrm/.env).
