# 📣 Mautic (Standalone Tool Repo)

- **Role:** Open-source marketing automation, drip campaigns, segments & landing pages
- **Stack:** Stack A
- **Upstream Open-Source Repo:** https://github.com/mautic/mautic (GPL-3.0)
- **Dedicated Launch Link (Auto-Boots & Opens):** http://localhost:7867/t/mautic
- **Direct Application Port:** http://localhost:5300

## Run Individually (One Click via Hub)
1. Start the Service #03 Hub: `python techstarz101_services/03_marketing_campaigns/hub/app.py`
2. Click **[http://localhost:7867/t/mautic](http://localhost:7867/t/mautic)** (or click the 📣 icon on the Hub).

## Run Individually (Standalone Docker Compose)
```bash
cd techstarz101_services/03_marketing_campaigns/tools/mautic
docker compose up -d
```

## First-Run Notes
Complete the 3-step Mautic web installer using the generated MySQL credentials in tools/mautic/.env.
