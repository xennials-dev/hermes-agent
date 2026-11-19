# 🔀 n8n Portal Orchestrator (`n8n-rpa`)

**Stack B · Service #13: Browser-Use Web Agent (`TS101-SRV-13`)**

- **Role:** End-to-end RPA workflow scheduler wiring Crawl4AI, ChangeDetection & ERP webhooks
- **Upstream Repo:** https://github.com/n8n-io/n8n
- **License:** Sustainable Use (fair-code)
- **Local App URL:** http://localhost:7230
- **One-Click Hub Launch Link:** `http://localhost:7877/t/n8n-rpa`
- **Estimated RAM:** ~400 MB

## Run Standalone (Independent of Hub)

```bash
cp .env.example .env
docker compose up -d
```

## First-Run Notes
Import /automations/stack_a_portal_extract_sync.n8n.json to run scheduled zero-API portal syncs.
