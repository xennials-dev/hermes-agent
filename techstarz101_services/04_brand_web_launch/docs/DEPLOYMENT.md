# Production Deployment Guide — Brand & Web Launch

## 1. Localhost Hub Review
```powershell
python techstarz101_services/04_brand_web_launch/hub/app.py
```
Open **[http://localhost:7868](http://localhost:7868)** to click any tool's repo icon (`/t/<tool>`), stack selected tools, or use the Instant Brand Kit & Live Site Compiler (`/preview/site`).

## 2. Standalone Single-Tool CLI Deployment
```bash
cd techstarz101_services/04_brand_web_launch/tools/penpot
docker compose up -d
```

## 3. Domain & SSL Production Rollout
1. Point your domain's `A` record to your VPS IP.
2. Launch `Nginx Proxy Manager` (`/t/nginx-proxy-manager`), add a Proxy Host pointing to your web container, and toggle **Request a new SSL Certificate (Let's Encrypt) + Force SSL**.
3. Launch `Uptime Kuma` (`/t/uptime-kuma`) and add an HTTPS monitor with SSL expiry alerts.
