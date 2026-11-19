# 🌐 Browserless Chromium CDP (`browserless-chrome`)

**Stack A · Service #13: Browser-Use Web Agent (`TS101-SRV-13`)**

- **Role:** Headless Chromium fleet with Chrome DevTools Protocol (CDP) & live Debugger UI
- **Upstream Repo:** https://github.com/browserless/browserless
- **License:** SSPL-1.0
- **Local App URL:** http://localhost:7100
- **One-Click Hub Launch Link:** `http://localhost:7877/t/browserless-chrome`
- **Estimated RAM:** ~900 MB

## Run Standalone (Independent of Hub)

```bash
cp .env.example .env
docker compose up -d
```

## First-Run Notes
Connect Browser-Use or Playwright directly to ws://localhost:7100?token=<TOKEN> for isolated runs.
