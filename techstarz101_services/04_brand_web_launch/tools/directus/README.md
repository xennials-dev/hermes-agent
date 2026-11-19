# 🧱 Directus (Standalone Tool Repo)

- **Role:** Headless CMS & instant REST/GraphQL backend for brand web apps
- **Stack:** Stack A
- **Upstream Open-Source Repo:** https://github.com/directus/directus (BSL-1.1 / Open Source)
- **Dedicated Launch Link (Auto-Boots & Opens):** http://localhost:7868/t/directus
- **Direct Application Port:** http://localhost:5510

## Run Individually (One Click via Hub)
1. Start the Service #04 Hub: `python techstarz101_services/04_brand_web_launch/hub/app.py`
2. Click **[http://localhost:7868/t/directus](http://localhost:7868/t/directus)** (or click the 🧱 icon on the Hub).

## Run Individually (Standalone Docker Compose)
```bash
cd techstarz101_services/04_brand_web_launch/tools/directus
docker compose up -d
```

## First-Run Notes
Log in with admin@techstarz101.local and the generated ADMIN_PASSWORD in tools/directus/.env.
