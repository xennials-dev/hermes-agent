# 🔀 n8n Creative Orchestrator (`n8n-creative`)

**Stack B · Service #12: ComfyUI Creative Engine (`TS101-SRV-12`)**

- **Role:** Automated SKU-to-Ad pipeline wiring ComfyUI, Rembg, FFmpeg Video API & MinIO storage
- **Upstream Repo:** https://github.com/n8n-io/n8n
- **License:** Sustainable Use (fair-code)
- **Local App URL:** http://localhost:7030
- **One-Click Hub Launch Link:** `http://localhost:7876/t/n8n-creative`
- **Estimated RAM:** ~400 MB

## Run Standalone (Independent of Hub)

```bash
cp .env.example .env
docker compose up -d
```

## First-Run Notes
Import /automations/stack_a_comfyui_product_batch.n8n.json to turn product briefs into ready ad packs.
