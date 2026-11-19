# 🚦 LiteLLM Gateway (Standalone Tool Repo)

- **Role:** Unified OpenAI-compatible router across 100+ local & cloud LLMs with spend caps
- **Stack:** Stack B
- **Upstream Open-Source Repo:** https://github.com/BerriAI/litellm (MIT)
- **Dedicated Launch Link (Auto-Boots & Opens):** http://localhost:7869/t/litellm
- **Direct Application Port:** http://localhost:5820/ui

## Run Individually (One Click via Hub)
1. Start the Service #05 Hub: `python techstarz101_services/05_autonomous_ai_employee/hub/app.py`
2. Click **[http://localhost:7869/t/litellm](http://localhost:7869/t/litellm)** (or click the 🚦 icon on the Hub).

## Run Individually (Standalone Docker Compose)
```bash
cd techstarz101_services/05_autonomous_ai_employee/tools/litellm
docker compose up -d
```

## First-Run Notes
Admin UI at /ui — log in with LITELLM_MASTER_KEY from tools/litellm/.env to manage model keys & budgets.
