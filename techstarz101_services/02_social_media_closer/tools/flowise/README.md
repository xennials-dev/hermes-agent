# 🤖 Flowise (Standalone Tool Repo)

- **Role:** Visual AI agent builder for the DM qualification and closing bot
- **Stack:** Stack B
- **Upstream Open-Source Repo:** https://github.com/FlowiseAI/Flowise (Apache-2.0)
- **Dedicated Launch Link (Auto-Boots & Opens):** http://localhost:7866/t/flowise
- **Direct Application Port:** http://localhost:5210

## Run Individually (One Click via Hub)
1. Start the Service #02 Hub: `python techstarz101_services/02_social_media_closer/hub/app.py`
2. Click **[http://localhost:7866/t/flowise](http://localhost:7866/t/flowise)** (or click the 🤖 icon on the Hub).

## Run Individually (Standalone Docker Compose)
```bash
cd techstarz101_services/02_social_media_closer/tools/flowise
docker compose up -d
```

## First-Run Notes
Create the local admin account, then Chatflows > Load > /automations/stack_b_flowise_closer.json.
