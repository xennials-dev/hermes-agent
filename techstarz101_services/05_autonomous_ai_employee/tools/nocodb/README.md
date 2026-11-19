# 📋 NocoDB Executive Board (Standalone Tool Repo)

- **Role:** Open-source Airtable alternative for AI task queues, SOPs & human approvals
- **Stack:** Stack B
- **Upstream Open-Source Repo:** https://github.com/nocodb/nocodb (AGPL-3.0)
- **Dedicated Launch Link (Auto-Boots & Opens):** http://localhost:7869/t/nocodb
- **Direct Application Port:** http://localhost:5830

## Run Individually (One Click via Hub)
1. Start the Service #05 Hub: `python techstarz101_services/05_autonomous_ai_employee/hub/app.py`
2. Click **[http://localhost:7869/t/nocodb](http://localhost:7869/t/nocodb)** (or click the 📋 icon on the Hub).

## Run Individually (Standalone Docker Compose)
```bash
cd techstarz101_services/05_autonomous_ai_employee/tools/nocodb
docker compose up -d
```

## First-Run Notes
Sign up on first visit to create your local super-admin and executive task approval tables.
