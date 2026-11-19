# ✂️ Rembg Cutout API (`rembg-api`)

**Stack A · Service #12: ComfyUI Creative Engine (`TS101-SRV-12`)**

- **Role:** Zero-click AI background removal server & web UI for clean e-commerce product cutouts
- **Upstream Repo:** https://github.com/danielgatis/rembg
- **License:** MIT
- **Local App URL:** http://localhost:6910
- **One-Click Hub Launch Link:** `http://localhost:7876/t/rembg-api`
- **Estimated RAM:** ~650 MB

## Run Standalone (Independent of Hub)

```bash
cp .env.example .env
docker compose up -d
```

## First-Run Notes
Upload a product photo in the web UI or POST multipart/form-data to /api/remove for transparent PNGs.
