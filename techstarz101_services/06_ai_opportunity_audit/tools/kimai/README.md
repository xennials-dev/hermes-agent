# 🧾 Kimai Billing (Standalone Tool Repo)

- **Role:** Audit time tracking, $750 flat invoicing & 100% upgrade credit ledger
- **Stack:** Stack B
- **Upstream Open-Source Repo:** https://github.com/kimai/kimai (MIT)
- **Dedicated Launch Link (Auto-Boots & Opens):** http://localhost:7870/t/kimai
- **Direct Application Port:** http://localhost:6030

## Run Individually (One Click via Hub)
1. Start the Service #06 Hub: `python techstarz101_services/06_ai_opportunity_audit/hub/app.py`
2. Click **[http://localhost:7870/t/kimai](http://localhost:7870/t/kimai)** (or click the 🧾 icon on the Hub).

## Run Individually (Standalone Docker Compose)
```bash
cd techstarz101_services/06_ai_opportunity_audit/tools/kimai
docker compose up -d
```

## First-Run Notes
Log in with admin@techstarz101.local and KIMAI_ADMIN_PASSWORD from tools/kimai/.env.
