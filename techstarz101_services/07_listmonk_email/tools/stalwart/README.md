# 📮 Stalwart Mail Server (Standalone Tool Repo)

- **Role:** Modern Rust all-in-one self-hosted SMTP/JMAP/DKIM/DMARC mail server
- **Stack:** Stack A
- **Upstream Open-Source Repo:** https://github.com/stalwartlabs/mail-server (AGPL-3.0)
- **Dedicated Launch Link (Auto-Boots & Opens):** http://localhost:7871/t/stalwart
- **Direct Application Port:** http://localhost:6110

## Run Individually (One Click via Hub)
1. Start the Service #07 Hub: `python techstarz101_services/07_listmonk_email/hub/app.py`
2. Click **[http://localhost:7871/t/stalwart](http://localhost:7871/t/stalwart)** (or click the 📮 icon on the Hub).

## Run Individually (Standalone Docker Compose)
```bash
cd techstarz101_services/07_listmonk_email/tools/stalwart
docker compose up -d
```

## First-Run Notes
Open the web admin console on :6110; check container logs for the initial generated admin password.
