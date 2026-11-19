# 🔀 n8n (Standalone Tool Repo)

- **Role:** Workflow automation glue between every tool
- **Stack:** Stack A
- **Upstream Open-Source Repo:** https://github.com/n8n-io/n8n (Sustainable Use (fair-code))
- **Dedicated Launch Link (Auto-Boots & Opens):** http://localhost:7866/t/n8n
- **Direct Application Port:** http://localhost:5120

## Run Individually (One Click via Hub)
1. Start the Service #02 Hub: `python techstarz101_services/02_social_media_closer/hub/app.py`
2. Click **[http://localhost:7866/t/n8n](http://localhost:7866/t/n8n)** (or click the 🔀 icon on the Hub).

## Run Individually (Standalone Docker Compose)
```bash
cd techstarz101_services/02_social_media_closer/tools/n8n
docker compose up -d
```

## First-Run Notes
Create the owner account, then Workflows > Import from File > /automations/stack_a_dm_closer.n8n.json.
