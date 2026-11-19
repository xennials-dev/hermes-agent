# 🔀 n8n Email Automator (Standalone Tool Repo)

- **Role:** Behavioral drip sequences, bounce webhook handling & CRM subscriber sync
- **Stack:** Stack B
- **Upstream Open-Source Repo:** https://github.com/n8n-io/n8n (Sustainable Use (fair-code))
- **Dedicated Launch Link (Auto-Boots & Opens):** http://localhost:7871/t/n8n-email
- **Direct Application Port:** http://localhost:6220

## Run Individually (One Click via Hub)
1. Start the Service #07 Hub: `python techstarz101_services/07_listmonk_email/hub/app.py`
2. Click **[http://localhost:7871/t/n8n-email](http://localhost:7871/t/n8n-email)** (or click the 🔀 icon on the Hub).

## Run Individually (Standalone Docker Compose)
```bash
cd techstarz101_services/07_listmonk_email/tools/n8n-email
docker compose up -d
```

## First-Run Notes
Create owner account and import /automations/stack_a_listmonk_hygiene_blast.n8n.json.
