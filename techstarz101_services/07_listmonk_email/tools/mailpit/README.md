# 🧪 Mailpit QA Sandbox (Standalone Tool Repo)

- **Role:** Local SMTP capture, HTML rendering & link/spam QA before live blasts
- **Stack:** Stack A
- **Upstream Open-Source Repo:** https://github.com/axllent/mailpit (MIT)
- **Dedicated Launch Link (Auto-Boots & Opens):** http://localhost:7871/t/mailpit
- **Direct Application Port:** http://localhost:6120

## Run Individually (One Click via Hub)
1. Start the Service #07 Hub: `python techstarz101_services/07_listmonk_email/hub/app.py`
2. Click **[http://localhost:7871/t/mailpit](http://localhost:7871/t/mailpit)** (or click the 🧪 icon on the Hub).

## Run Individually (Standalone Docker Compose)
```bash
cd techstarz101_services/07_listmonk_email/tools/mailpit
docker compose up -d
```

## First-Run Notes
Point Listmonk test SMTP to host.docker.internal:1025 to inspect rendered emails safely before blasting.
