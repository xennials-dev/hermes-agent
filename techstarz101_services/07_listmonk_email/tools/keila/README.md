# ✉️ Keila (Standalone Tool Repo)

- **Role:** Visual block-editor Mailchimp/ConvertKit alternative with segments & forms
- **Stack:** Stack B
- **Upstream Open-Source Repo:** https://github.com/pentacent/keila (AGPL-3.0)
- **Dedicated Launch Link (Auto-Boots & Opens):** http://localhost:7871/t/keila
- **Direct Application Port:** http://localhost:6200

## Run Individually (One Click via Hub)
1. Start the Service #07 Hub: `python techstarz101_services/07_listmonk_email/hub/app.py`
2. Click **[http://localhost:7871/t/keila](http://localhost:7871/t/keila)** (or click the ✉️ icon on the Hub).

## Run Individually (Standalone Docker Compose)
```bash
cd techstarz101_services/07_listmonk_email/tools/keila
docker compose up -d
```

## First-Run Notes
Log in with admin@techstarz101.local and KEILA_USER_PASSWORD from tools/keila/.env.
