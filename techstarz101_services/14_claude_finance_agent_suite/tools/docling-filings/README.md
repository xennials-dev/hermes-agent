# 📑 Docling 10-K / CIM Parser (`docling-filings`)

**Stack A · Service #14: Claude Finance Agent Suite (`TS101-SRV-14`)**

- **Role:** 93.6% table-accuracy PDF parser for 10-Ks, CIMs, QoE reports & balance sheets
- **Upstream Repo:** https://github.com/docling-project/docling-serve
- **License:** MIT
- **Local App URL:** http://localhost:7320/ui
- **One-Click Hub Launch Link:** `http://localhost:7878/t/docling-filings`
- **Estimated RAM:** ~1600 MB

## Run Standalone (Independent of Hub)

```bash
cp .env.example .env
docker compose up -d
```

## First-Run Notes
Upload multi-column financial statements at /ui or POST to /v1/convert/source from n8n.
