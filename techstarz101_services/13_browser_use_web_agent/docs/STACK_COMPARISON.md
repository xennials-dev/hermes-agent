# Stack Comparison — Service #13: Browser-Use Web Agent

| Dimension | Stack A: AI Browser Sandbox & Extraction | Stack B: Live noVNC RPA & ERP Sync |
| --- | --- | --- |
| **Browser Runtime** | Browserless CDP (`:7100`) + Steel (`:7120`) | Selenium Standalone + live noVNC (`:7200` / `:7201`) |
| **Extraction / Monitoring** | Crawl4AI (`:7110`) + ChangeDetection (`:7130`) | Windmill Python/TS Scripts (`:7210`) |
| **Workflow Glue** | Direct REST / CDP | Activepieces (`:7220`) + n8n (`:7230`) |
| **Best For** | Autonomous Browser-Use agents, structured LLM scraping, and 24/7 portal change monitoring | Enterprise RPA requiring human 2FA handoff, approval workflows, and scheduled Python jobs |

> **Mix & Match:** Combine **Steel Browser** (`:7120`) + **ChangeDetection** (`:7130`) + **Windmill RPA** (`:7210`) + **n8n RPA** (`:7230`) from the Hub checkboxes.
