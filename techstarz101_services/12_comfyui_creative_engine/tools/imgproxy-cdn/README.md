# 🖼️ imgproxy Ad Resizer (`imgproxy-cdn`)

**Stack A · Service #12: ComfyUI Creative Engine (`TS101-SRV-12`)**

- **Role:** Ultra-fast on-the-fly image resizing, smart cropping, WebP/AVIF & watermark processor
- **Upstream Repo:** https://github.com/imgproxy/imgproxy
- **License:** MIT
- **Local App URL:** http://localhost:6930/health
- **One-Click Hub Launch Link:** `http://localhost:7876/t/imgproxy-cdn`
- **Estimated RAM:** ~200 MB

## Run Standalone (Independent of Hub)

```bash
cp .env.example .env
docker compose up -d
```

## First-Run Notes
Transform any MinIO asset URL into 1:1, 9:16, or 16:9 ad creatives via /insecure/rs:fill:1080:1080/plain/<url>.
