# 📥 Roundcube Webmail (Standalone Tool Repo)

- **Role:** Self-hosted reply inbox for managing warm newsletter & campaign responses
- **Stack:** Stack B
- **Upstream Open-Source Repo:** https://github.com/roundcube/roundcubemail (GPL-3.0)
- **Dedicated Launch Link (Auto-Boots & Opens):** http://localhost:7871/t/roundcube
- **Direct Application Port:** http://localhost:6210

## Run Individually (One Click via Hub)
1. Start the Service #07 Hub: `python techstarz101_services/07_listmonk_email/hub/app.py`
2. Click **[http://localhost:7871/t/roundcube](http://localhost:7871/t/roundcube)** (or click the 📥 icon on the Hub).

## Run Individually (Standalone Docker Compose)
```bash
cd techstarz101_services/07_listmonk_email/tools/roundcube
docker compose up -d
```

## First-Run Notes
Connects via IMAP/SMTP to Stalwart or your custom domain mailbox for unified reply handling.
