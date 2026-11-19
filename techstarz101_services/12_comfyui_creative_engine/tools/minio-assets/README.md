# 🪣 MinIO Creative Vault (`minio-assets`)

**Stack A · Service #12: ComfyUI Creative Engine (`TS101-SRV-12`)**

- **Role:** Self-hosted S3-compatible asset storage & web console for raw renders and campaign kits
- **Upstream Repo:** https://github.com/minio/minio
- **License:** AGPL-3.0
- **Local App URL:** http://localhost:6920
- **One-Click Hub Launch Link:** `http://localhost:7876/t/minio-assets`
- **Estimated RAM:** ~350 MB

## Run Standalone (Independent of Hub)

```bash
cp .env.example .env
docker compose up -d
```

## First-Run Notes
Console on :6920 (S3 API on :6921). Default login: minioadmin / minioadmin123 (configurable in .env).
