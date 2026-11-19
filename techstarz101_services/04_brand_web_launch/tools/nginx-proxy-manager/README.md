# 🌐 Nginx Proxy Manager (Standalone Tool Repo)

- **Role:** Visual domain routing, reverse proxy & automated Let's Encrypt SSL
- **Stack:** Stack A
- **Upstream Open-Source Repo:** https://github.com/NginxProxyManager/nginx-proxy-manager (MIT)
- **Dedicated Launch Link (Auto-Boots & Opens):** http://localhost:7868/t/nginx-proxy-manager
- **Direct Application Port:** http://localhost:5530

## Run Individually (One Click via Hub)
1. Start the Service #04 Hub: `python techstarz101_services/04_brand_web_launch/hub/app.py`
2. Click **[http://localhost:7868/t/nginx-proxy-manager](http://localhost:7868/t/nginx-proxy-manager)** (or click the 🌐 icon on the Hub).

## Run Individually (Standalone Docker Compose)
```bash
cd techstarz101_services/04_brand_web_launch/tools/nginx-proxy-manager
docker compose up -d
```

## First-Run Notes
Default admin login: admin@example.com / changeme (prompts immediately to update).
