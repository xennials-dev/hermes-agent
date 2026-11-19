# Product Requirements Document (PRD) — Listmonk Email Marketing

**Service ID:** `TS101-SRV-07`  
**Product Name:** Techstarz101 Listmonk Email Marketing (Self-Hosted Email Engine; Zero Contact Tax)  
**Status:** Production Ready  
**Localhost Hub:** `http://localhost:7871`  
**Live Catalog Reference:** `https://techstarz101.com/agents/listmonk-email`

---

## 1. Executive Summary
Legacy email SaaS (Mailchimp, Klaviyo, ActiveCampaign) penalizes growth by charging $500–$1,500+/month purely for storing your own subscriber list.
The **Techstarz101 Listmonk Email Marketing** suite replaces rented email platforms with **8 standalone, click-to-launch open-source app repos** across 2 composable stacks:
- Unlimited contacts at $0 contact tax (Listmonk / Keila)
- Self-hosted Rust SMTP/DKIM/DMARC delivery (Stalwart) + pre-send QA sandbox (Mailpit)
- Automated MX/SMTP bounce scrubbing (Reacher) keeping bounce rates < 1%
- Unified reply inbox (Roundcube), behavioral drips (n8n), and SQL segmentation (Adminer)
