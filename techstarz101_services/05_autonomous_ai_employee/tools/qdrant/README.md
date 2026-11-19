# 🧬 Qdrant Vector Memory (Standalone Tool Repo)

- **Role:** High-speed semantic vector memory storing SOPs, transcripts & company knowledge
- **Stack:** Stack A
- **Upstream Open-Source Repo:** https://github.com/qdrant/qdrant (Apache-2.0)
- **Dedicated Launch Link (Auto-Boots & Opens):** http://localhost:7869/t/qdrant
- **Direct Application Port:** http://localhost:5710/dashboard

## Run Individually (One Click via Hub)
1. Start the Service #05 Hub: `python techstarz101_services/05_autonomous_ai_employee/hub/app.py`
2. Click **[http://localhost:7869/t/qdrant](http://localhost:7869/t/qdrant)** (or click the 🧬 icon on the Hub).

## Run Individually (Standalone Docker Compose)
```bash
cd techstarz101_services/05_autonomous_ai_employee/tools/qdrant
docker compose up -d
```

## First-Run Notes
Open /dashboard to inspect vector collections, semantic search indexes, and memory payloads.
