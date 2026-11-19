# Production Deployment Guide — Listmonk Email Marketing

## 1. Localhost Hub Review
```powershell
python techstarz101_services/07_listmonk_email/hub/app.py
```
Open **[http://localhost:7871](http://localhost:7871)** to click any tool's repo icon (`/t/<tool>`), stack selected tools, or run the Zero-Contact-Tax Calculator & DNS Auth Builder.

## 2. Standalone Single-Tool CLI Deployment
```bash
cd techstarz101_services/07_listmonk_email/tools/listmonk
docker compose up -d
```

## 3. Production Deliverability Checklist
1. Publish the generated **SPF**, **DKIM**, and **DMARC** TXT records on your sending domain.
2. Test every new campaign HTML template against **Mailpit** (`host.docker.internal:1025`) before switching Listmonk SMTP to **Stalwart** or Amazon SES.
3. Route all new signups through **Reacher** (`:6130/v0/check_email`) to block invalid addresses before they touch your sending IP.
