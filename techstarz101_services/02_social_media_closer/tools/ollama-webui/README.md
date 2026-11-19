# 🧠 Ollama + Open WebUI (Standalone Tool Repo)

- **Role:** Local LLM that writes 24/7 DM sales replies
- **Stack:** Stack A
- **Upstream Open-Source Repo:** https://github.com/ollama/ollama (MIT / BSD-3)
- **Dedicated Launch Link (Auto-Boots & Opens):** http://localhost:7866/t/ollama-webui
- **Direct Application Port:** http://localhost:5130

## Run Individually (One Click via Hub)
1. Start the Service #02 Hub: `python techstarz101_services/02_social_media_closer/hub/app.py`
2. Click **[http://localhost:7866/t/ollama-webui](http://localhost:7866/t/ollama-webui)** (or click the 🧠 icon on the Hub).

## Run Individually (Standalone Docker Compose)
```bash
cd techstarz101_services/02_social_media_closer/tools/ollama-webui
docker compose up -d
```

## First-Run Notes
No login (WEBUI_AUTH disabled locally). The llama3.2:3b model is pulled automatically on first launch (~2 GB).
