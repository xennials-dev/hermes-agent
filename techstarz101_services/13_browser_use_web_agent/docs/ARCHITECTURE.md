# System Architecture — Service #13: Browser-Use Web Agent

## 1. Governed Zero-API Portal Automation Flow
```
Trigger (Cron / ChangeDetection :7130 / Webhook)
   │
   ▼
Orchestrator (Windmill :7210 / n8n :7230 / Activepieces :7220)
   │
   ├─► Browser-Use / Playwright -> Steel (:7120) or Browserless CDP (:7100)
   ├─► Structured Public Extraction -> Crawl4AI (:7110)
   └─► Live 2FA / Login Handoff -> Selenium noVNC (:7201)
   │
   ▼
Audit Screenshots + Structured JSON -> CRM / ERP / Accounting Webhook
```

## 2. Port & Network Isolation
- **Modular Hub:** `http://localhost:7877`
- **Stack A:** `:7100` (Browserless CDP), `:7110` (Crawl4AI), `:7120` (Steel Browser), `:7130` (ChangeDetection)
- **Stack B:** `:7200`/`:7201` (Selenium Grid + noVNC), `:7210` (Windmill), `:7220` (Activepieces), `:7230` (n8n RPA)
