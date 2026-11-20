# 📈 OpenBB Financial API (`openbb-platform`)

**Stack A · Service #14: Claude Finance Agent Suite (`TS101-SRV-14`)**

- **Role:** Open-source market data, SEC EDGAR filings, comps & macro REST API
- **Upstream Repo:** https://github.com/OpenBB-finance/OpenBB
- **License:** AGPL-3.0
- **Local App URL:** http://localhost:7300/docs
- **One-Click Hub Launch Link:** `http://localhost:7878/t/openbb-platform`
- **Estimated RAM:** ~900 MB

## Run Standalone (Independent of Hub)

```bash
cp .env.example .env
docker compose up -d
```

## First-Run Notes
Open Swagger UI at /docs to query equity comps, macro indicators, and SEC filings from finance agents.
