# 🗄️ Adminer SQL Studio (Standalone Tool Repo)

- **Role:** Instant SQL audience segmentation & subscriber database management UI
- **Stack:** Stack B
- **Upstream Open-Source Repo:** https://github.com/vrana/adminer (Apache-2.0)
- **Dedicated Launch Link (Auto-Boots & Opens):** http://localhost:7871/t/adminer
- **Direct Application Port:** http://localhost:6230

## Run Individually (One Click via Hub)
1. Start the Service #07 Hub: `python techstarz101_services/07_listmonk_email/hub/app.py`
2. Click **[http://localhost:7871/t/adminer](http://localhost:7871/t/adminer)** (or click the 🗄️ icon on the Hub).

## Run Individually (Standalone Docker Compose)
```bash
cd techstarz101_services/07_listmonk_email/tools/adminer
docker compose up -d
```

## First-Run Notes
Lightweight zero-config SQL UI to query, segment, and export subscriber lists directly from Postgres.
