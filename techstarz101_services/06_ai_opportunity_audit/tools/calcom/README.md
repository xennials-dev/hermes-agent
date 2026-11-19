# 📅 Cal.com (Standalone Tool Repo)

- **Role:** Self-hosted $750 Audit kickoff & discovery session booking engine
- **Stack:** Stack A
- **Upstream Open-Source Repo:** https://github.com/calcom/cal.com (AGPL-3.0)
- **Dedicated Launch Link (Auto-Boots & Opens):** http://localhost:7870/t/calcom
- **Direct Application Port:** http://localhost:5910

## Run Individually (One Click via Hub)
1. Start the Service #06 Hub: `python techstarz101_services/06_ai_opportunity_audit/hub/app.py`
2. Click **[http://localhost:7870/t/calcom](http://localhost:7870/t/calcom)** (or click the 📅 icon on the Hub).

## Run Individually (Standalone Docker Compose)
```bash
cd techstarz101_services/06_ai_opportunity_audit/tools/calcom
docker compose up -d
```

## First-Run Notes
Complete the Cal.com onboarding screen to create your 30-min Audit Kickoff event slug.
