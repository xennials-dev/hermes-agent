# 🗂️ Paperless-ngx Vault (`paperless-ngx`)

**Stack B · Service #11: Docling Document RAG (`TS101-SRV-11`)**

- **Role:** Self-hosted document management system with auto-OCR, tagging & full-text search
- **Upstream Repo:** https://github.com/paperless-ngx/paperless-ngx
- **License:** GPL-3.0
- **Local App URL:** http://localhost:6800
- **One-Click Hub Launch Link:** `http://localhost:7874/t/paperless-ngx`
- **Estimated RAM:** ~950 MB

## Run Standalone (Independent of Hub)

```bash
cp .env.example .env
docker compose up -d
```

## First-Run Notes
Default local login: admin / admin12345 (customizable in .env). Drop PDFs to auto-archive & tag.
