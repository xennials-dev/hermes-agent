# ⚡ Strapi (Standalone Tool Repo)

- **Role:** Open-source headless CMS & API builder for custom React/Next.js/Astro sites
- **Stack:** Stack B
- **Upstream Open-Source Repo:** https://github.com/strapi/strapi (MIT)
- **Dedicated Launch Link (Auto-Boots & Opens):** http://localhost:7868/t/strapi
- **Direct Application Port:** http://localhost:5620/admin

## Run Individually (One Click via Hub)
1. Start the Service #04 Hub: `python techstarz101_services/04_brand_web_launch/hub/app.py`
2. Click **[http://localhost:7868/t/strapi](http://localhost:7868/t/strapi)** (or click the ⚡ icon on the Hub).

## Run Individually (Standalone Docker Compose)
```bash
cd techstarz101_services/04_brand_web_launch/tools/strapi
docker compose up -d
```

## First-Run Notes
First boot installs Strapi into the volume (~60s), then open /admin to create your super admin.
