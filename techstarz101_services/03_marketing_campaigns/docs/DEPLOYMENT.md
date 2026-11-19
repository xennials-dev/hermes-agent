# Production Deployment Guide — Marketing Campaigns

## 1. Localhost Hub Review
```powershell
python techstarz101_services/03_marketing_campaigns/hub/app.py
```
Open **[http://localhost:7867](http://localhost:7867)** to click any tool's repo icon, launch individual apps via `/t/<tool>`, stack selected tools, or run the Multi-Angle A/B Ad Generator.

## 2. Standalone Single-Tool CLI Deployment
Every tool runs independently with its own database:
```bash
cd techstarz101_services/03_marketing_campaigns/tools/growthbook
docker compose up -d
```

## 3. Wiring Stack Automations
- **Stack A:** Import `automations/stack_a_ab_campaign_router.n8n.json` into n8n to connect Shlink/Umami webhooks → GrowthBook experiments → Mautic drip enrollments.
- **Stack B:** Connect Typebot completion webhooks to `automations/stack_b_funnel_broadcast.json` targets (`Listmonk` `:5400` + `Matomo` `:5410`), and add their Postgres/MariaDB connections to `Metabase` `:5430` for live ROAS dashboards.
