# Deployment Guide — Service #13: Browser-Use Web Agent

## 1. Local Modular Hub
```bash
cd techstarz101_services/13_browser_use_web_agent
python hub/app.py
# Open http://localhost:7877
```

## 2. Boot Any Tool Independently
```bash
cd tools/steel-browser
cp .env.example .env
docker compose up -d
# Open http://localhost:7120/ui
```

## 3. Security & Governance Best Practices
- Always scope RPA agents to an explicit **domain allowlist** and least-privilege portal service accounts.
- Route interactive 2FA/login steps through **Selenium noVNC** (`http://localhost:7201`) or **Steel Live Viewer** (`http://localhost:7120/ui`).
- Keep `shm_size: "1gb"`–`"2gb"` on Chromium containers to prevent tab crashes on heavy SPAs.
