# 👁️ ChangeDetection Monitor (`changedetection`)

**Stack A · Service #13: Browser-Use Web Agent (`TS101-SRV-13`)**

- **Role:** 24/7 portal, pricing & regulatory page monitor with visual diffs & webhook alerts
- **Upstream Repo:** https://github.com/dgtlmoon/changedetection.io
- **License:** Apache-2.0
- **Local App URL:** http://localhost:7130
- **One-Click Hub Launch Link:** `http://localhost:7877/t/changedetection`
- **Estimated RAM:** ~300 MB

## Run Standalone (Independent of Hub)

```bash
cp .env.example .env
docker compose up -d
```

## First-Run Notes
Add any vendor/competitor URL and fire an n8n webhook automatically whenever a value changes.
