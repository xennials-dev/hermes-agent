# 📈 Umami Analytics (Standalone Tool Repo)

- **Role:** Privacy-first real-time conversion, campaign & UTM attribution analytics
- **Stack:** Stack A
- **Upstream Open-Source Repo:** https://github.com/umami-software/umami (MIT)
- **Dedicated Launch Link (Auto-Boots & Opens):** http://localhost:7867/t/umami
- **Direct Application Port:** http://localhost:5320

## Run Individually (One Click via Hub)
1. Start the Service #03 Hub: `python techstarz101_services/03_marketing_campaigns/hub/app.py`
2. Click **[http://localhost:7867/t/umami](http://localhost:7867/t/umami)** (or click the 📈 icon on the Hub).

## Run Individually (Standalone Docker Compose)
```bash
cd techstarz101_services/03_marketing_campaigns/tools/umami
docker compose up -d
```

## First-Run Notes
Default local login: username 'admin', password 'umami' (change immediately in Settings).
