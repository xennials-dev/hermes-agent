# 📧 Listmonk (Standalone Tool Repo)

- **Role:** High-speed Go self-hosted newsletter & broadcast engine (zero contact tax)
- **Stack:** Stack A
- **Upstream Open-Source Repo:** https://github.com/knadh/listmonk (AGPL-3.0)
- **Dedicated Launch Link (Auto-Boots & Opens):** http://localhost:7871/t/listmonk
- **Direct Application Port:** http://localhost:6100

## Run Individually (One Click via Hub)
1. Start the Service #07 Hub: `python techstarz101_services/07_listmonk_email/hub/app.py`
2. Click **[http://localhost:7871/t/listmonk](http://localhost:7871/t/listmonk)** (or click the 📧 icon on the Hub).

## Run Individually (Standalone Docker Compose)
```bash
cd techstarz101_services/07_listmonk_email/tools/listmonk
docker compose up -d
```

## First-Run Notes
Log in with 'admin' and the generated LISTMONK_ADMIN_PASSWORD in tools/listmonk/.env.
