# 📣 Postiz (Standalone Tool Repo)

- **Role:** Social scheduling and auto-posting (30+ networks)
- **Stack:** Stack A
- **Upstream Open-Source Repo:** https://github.com/gitroomhq/postiz-app (AGPL-3.0)
- **Dedicated Launch Link (Auto-Boots & Opens):** http://localhost:7866/t/postiz
- **Direct Application Port:** http://localhost:5100
- **Live Production VPS:** http://2.25.238.185:4200

## Run Individually (One Click via Hub)
1. Start the Service #02 Hub: `python techstarz101_services/02_social_media_closer/hub/app.py`
2. Click **[http://localhost:7866/t/postiz](http://localhost:7866/t/postiz)** (or click the 📣 icon on the Hub).

## Run Individually (Standalone Docker Compose)
```bash
cd techstarz101_services/02_social_media_closer/tools/postiz
docker compose up -d
```

## First-Run Notes
Open the link and click 'Sign up' to create the first local admin account.
