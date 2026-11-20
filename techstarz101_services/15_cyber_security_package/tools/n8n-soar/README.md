# 🚨 n8n SOAR Playbooks (`n8n-soar`)

**Stack B · Service #15: Cyber Security Package (`TS101-SRV-15`)**

- **Role:** Automated security orchestration wiring Trivy CVEs, CrowdSec blocks & SOC alerts
- **Upstream Repo:** https://github.com/n8n-io/n8n
- **License:** Sustainable Use (fair-code)
- **Local App URL:** http://localhost:7630
- **One-Click Hub Launch Link:** `http://localhost:7879/t/n8n-soar`
- **Estimated RAM:** ~400 MB

## Run Standalone (Independent of Hub)

```bash
cp .env.example .env
docker compose up -d
```

## First-Run Notes
Import /automations/stack_a_cve_triage_soar.n8n.json to automate CVE severity triage & alerts.
