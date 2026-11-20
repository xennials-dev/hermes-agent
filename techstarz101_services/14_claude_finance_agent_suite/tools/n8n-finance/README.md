# 🔀 n8n 10-Agent Orchestrator (`n8n-finance`)

**Stack B · Service #14: Claude Finance Agent Suite (`TS101-SRV-14`)**

- **Role:** End-to-end IB/PE/KYC multi-agent workflow engine wiring filings, KYC & IC memos
- **Upstream Repo:** https://github.com/n8n-io/n8n
- **License:** Sustainable Use (fair-code)
- **Local App URL:** http://localhost:7430
- **One-Click Hub Launch Link:** `http://localhost:7878/t/n8n-finance`
- **Estimated RAM:** ~400 MB

## Run Standalone (Independent of Hub)

```bash
cp .env.example .env
docker compose up -d
```

## First-Run Notes
Import /automations/stack_a_10agent_ic_memo.n8n.json to run automated CIM-to-IC-Memo diligence.
