# 🔍 Langfuse Observability (Standalone Tool Repo)

- **Role:** AI employee audit traces, prompt versioning, latency & token cost governance
- **Stack:** Stack A
- **Upstream Open-Source Repo:** https://github.com/langfuse/langfuse (MIT)
- **Dedicated Launch Link (Auto-Boots & Opens):** http://localhost:7869/t/langfuse
- **Direct Application Port:** http://localhost:5730

## Run Individually (One Click via Hub)
1. Start the Service #05 Hub: `python techstarz101_services/05_autonomous_ai_employee/hub/app.py`
2. Click **[http://localhost:7869/t/langfuse](http://localhost:7869/t/langfuse)** (or click the 🔍 icon on the Hub).

## Run Individually (Standalone Docker Compose)
```bash
cd techstarz101_services/05_autonomous_ai_employee/tools/langfuse
docker compose up -d
```

## First-Run Notes
Create your local workspace account on first visit to inspect live agent traces and cost ledgers.
