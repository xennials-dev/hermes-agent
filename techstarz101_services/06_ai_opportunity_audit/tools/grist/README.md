# 📊 Grist (Standalone Tool Repo)

- **Role:** Open-source relational spreadsheet & interactive SaaS-savings ROI modeler
- **Stack:** Stack B
- **Upstream Open-Source Repo:** https://github.com/gristlabs/grist-core (Apache-2.0)
- **Dedicated Launch Link (Auto-Boots & Opens):** http://localhost:7870/t/grist
- **Direct Application Port:** http://localhost:6010

## Run Individually (One Click via Hub)
1. Start the Service #06 Hub: `python techstarz101_services/06_ai_opportunity_audit/hub/app.py`
2. Click **[http://localhost:7870/t/grist](http://localhost:7870/t/grist)** (or click the 📊 icon on the Hub).

## Run Individually (Standalone Docker Compose)
```bash
cd techstarz101_services/06_ai_opportunity_audit/tools/grist
docker compose up -d
```

## First-Run Notes
Opens directly into your local Grist workspace — import CSVs or build live ROI & payback calculators.
