# 🎨 ComfyUI Node Studio (`comfyui`)

**Stack A · Service #12: ComfyUI Creative Engine (`TS101-SRV-12`)**

- **Role:** Programmable node-graph engine for Flux/SDXL product photography & AI video generation
- **Upstream Repo:** https://github.com/comfyanonymous/ComfyUI
- **License:** GPL-3.0
- **Local App URL:** http://localhost:6900
- **One-Click Hub Launch Link:** `http://localhost:7876/t/comfyui`
- **Estimated RAM:** ~2400 MB

## Run Standalone (Independent of Hub)

```bash
cp .env.example .env
docker compose up -d
```

## First-Run Notes
Load any generated JSON workflow from the Hub or POST directly to /prompt for automated batch rendering.
