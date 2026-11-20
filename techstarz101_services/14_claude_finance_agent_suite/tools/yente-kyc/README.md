# 🛡️ OpenSanctions Yente KYC (`yente-kyc`)

**Stack B · Service #14: Claude Finance Agent Suite (`TS101-SRV-14`)**

- **Role:** Real-time OFAC, EU/UN sanctions, PEP & beneficial ownership (UBO) AML API
- **Upstream Repo:** https://github.com/opensanctions/yente
- **License:** MIT
- **Local App URL:** http://localhost:7400/docs
- **One-Click Hub Launch Link:** `http://localhost:7878/t/yente-kyc`
- **Estimated RAM:** ~900 MB

## Run Standalone (Independent of Hub)

```bash
cp .env.example .env
docker compose up -d
```

## First-Run Notes
Test /match/default in Swagger UI at /docs to screen counterparties, directors, and UBOs.
