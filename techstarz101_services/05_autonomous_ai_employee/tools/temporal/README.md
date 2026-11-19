# ⏱️ Temporal Orchestrator (Standalone Tool Repo)

- **Role:** Durable long-running autonomous task & multi-step workflow execution engine
- **Stack:** Stack A
- **Upstream Open-Source Repo:** https://github.com/temporalio/temporal (MIT)
- **Dedicated Launch Link (Auto-Boots & Opens):** http://localhost:7869/t/temporal
- **Direct Application Port:** http://localhost:5720

## Run Individually (One Click via Hub)
1. Start the Service #05 Hub: `python techstarz101_services/05_autonomous_ai_employee/hub/app.py`
2. Click **[http://localhost:7869/t/temporal](http://localhost:7869/t/temporal)** (or click the ⏱️ icon on the Hub).

## Run Individually (Standalone Docker Compose)
```bash
cd techstarz101_services/05_autonomous_ai_employee/tools/temporal
docker compose up -d
```

## First-Run Notes
Temporal Server (:7233) + Temporal Web UI (:5720) boot automatically with zero manual DB setup.
