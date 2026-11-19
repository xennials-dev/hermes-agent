# 🖥️ Selenium + Live noVNC (`selenium-grid`)

**Stack B · Service #13: Browser-Use Web Agent (`TS101-SRV-13`)**

- **Role:** Interactive Chromium RPA runner with live browser desktop stream for human 2FA handoff
- **Upstream Repo:** https://github.com/SeleniumHQ/docker-selenium
- **License:** Apache-2.0
- **Local App URL:** http://localhost:7200/ui
- **One-Click Hub Launch Link:** `http://localhost:7877/t/selenium-grid`
- **Estimated RAM:** ~950 MB

## Run Standalone (Independent of Hub)

```bash
cp .env.example .env
docker compose up -d
```

## First-Run Notes
Grid UI on :7200 and live interactive noVNC desktop on http://localhost:7201 (password: secret).
