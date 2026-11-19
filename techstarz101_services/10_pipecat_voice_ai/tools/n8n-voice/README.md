# 🔀 n8n Call Router (`n8n-voice`)

**Stack B · Service #10: Pipecat 24/7 Voice AI (`TS101-SRV-10`)**

- **Role:** Post-call SMS confirmations, Cal.com webhooks & Twenty CRM call logging
- **Upstream Repo:** https://github.com/n8n-io/n8n
- **License:** Sustainable Use (fair-code)
- **Local App URL:** http://localhost:6630
- **One-Click Hub Launch Link:** `http://localhost:7873/t/n8n-voice`
- **Estimated RAM:** ~400 MB

## Run Standalone (Independent of Hub)

```bash
cp .env.example .env
docker compose up -d
```

## First-Run Notes
Import /automations/stack_a_pipecat_call_booking.n8n.json to automate post-call booking SMS & CRM sync.
