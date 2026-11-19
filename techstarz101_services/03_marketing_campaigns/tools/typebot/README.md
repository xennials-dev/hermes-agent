# 💬 Typebot (Standalone Tool Repo)

- **Role:** Interactive conversational ad-landing funnels & lead qualification
- **Stack:** Stack B
- **Upstream Open-Source Repo:** https://github.com/baptisteArno/typebot.io (AGPL-3.0)
- **Dedicated Launch Link (Auto-Boots & Opens):** http://localhost:7867/t/typebot
- **Direct Application Port:** http://localhost:5420

## Run Individually (One Click via Hub)
1. Start the Service #03 Hub: `python techstarz101_services/03_marketing_campaigns/hub/app.py`
2. Click **[http://localhost:7867/t/typebot](http://localhost:7867/t/typebot)** (or click the 💬 icon on the Hub).

## Run Individually (Standalone Docker Compose)
```bash
cd techstarz101_services/03_marketing_campaigns/tools/typebot
docker compose up -d
```

## First-Run Notes
Open Builder (:5420) to design conversational ad funnels; Viewer serves public bots on :5421.
