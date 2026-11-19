# 💬 Chatwoot (Standalone Tool Repo)

- **Role:** Omnichannel DM inbox (FB, IG, WhatsApp, X, Telegram, web chat)
- **Stack:** Stack A
- **Upstream Open-Source Repo:** https://github.com/chatwoot/chatwoot (MIT)
- **Dedicated Launch Link (Auto-Boots & Opens):** http://localhost:7866/t/chatwoot
- **Direct Application Port:** http://localhost:5110

## Run Individually (One Click via Hub)
1. Start the Service #02 Hub: `python techstarz101_services/02_social_media_closer/hub/app.py`
2. Click **[http://localhost:7866/t/chatwoot](http://localhost:7866/t/chatwoot)** (or click the 💬 icon on the Hub).

## Run Individually (Standalone Docker Compose)
```bash
cd techstarz101_services/02_social_media_closer/tools/chatwoot
docker compose up -d
```

## First-Run Notes
First visit shows the onboarding form; create the super-admin account, then add inboxes under Settings > Inboxes.
