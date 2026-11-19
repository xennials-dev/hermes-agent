# 🧠 Open WebUI (Standalone Tool Repo)

- **Role:** Executive AI chat command center, private RAG docs & multi-model workspace
- **Stack:** Stack A
- **Upstream Open-Source Repo:** https://github.com/open-webui/open-webui (MIT)
- **Dedicated Launch Link (Auto-Boots & Opens):** http://localhost:7869/t/open-webui
- **Direct Application Port:** http://localhost:5700

## Run Individually (One Click via Hub)
1. Start the Service #05 Hub: `python techstarz101_services/05_autonomous_ai_employee/hub/app.py`
2. Click **[http://localhost:7869/t/open-webui](http://localhost:7869/t/open-webui)** (or click the 🧠 icon on the Hub).

## Run Individually (Standalone Docker Compose)
```bash
cd techstarz101_services/05_autonomous_ai_employee/tools/open-webui
docker compose up -d
```

## First-Run Notes
No login required locally (WEBUI_AUTH=False). Auto-connects to local Ollama on host.docker.internal:11434.
