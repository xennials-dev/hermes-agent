# 🕷️ Crawl4AI Extractor (`crawl4ai`)

**Stack A · Service #13: Browser-Use Web Agent (`TS101-SRV-13`)**

- **Role:** LLM-ready headless web crawler outputting clean Markdown & structured JSON schemas
- **Upstream Repo:** https://github.com/unclecode/crawl4ai
- **License:** Apache-2.0
- **Local App URL:** http://localhost:7110/playground
- **One-Click Hub Launch Link:** `http://localhost:7877/t/crawl4ai`
- **Estimated RAM:** ~1100 MB

## Run Standalone (Independent of Hub)

```bash
cp .env.example .env
docker compose up -d
```

## First-Run Notes
Open /playground to test zero-API extraction or POST URLs to /crawl from n8n.
