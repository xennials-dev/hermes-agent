# 🦊 Gitea (Standalone Tool Repo)

- **Role:** Self-hosted Git server & CI/CD Actions runner for brand web repos
- **Stack:** Stack A
- **Upstream Open-Source Repo:** https://github.com/go-gitea/gitea (MIT)
- **Dedicated Launch Link (Auto-Boots & Opens):** http://localhost:7868/t/gitea
- **Direct Application Port:** http://localhost:5520

## Run Individually (One Click via Hub)
1. Start the Service #04 Hub: `python techstarz101_services/04_brand_web_launch/hub/app.py`
2. Click **[http://localhost:7868/t/gitea](http://localhost:7868/t/gitea)** (or click the 🦊 icon on the Hub).

## Run Individually (Standalone Docker Compose)
```bash
cd techstarz101_services/04_brand_web_launch/tools/gitea
docker compose up -d
```

## First-Run Notes
Click 'Install Gitea' on first visit (Postgres is pre-wired) and register your local admin account.
