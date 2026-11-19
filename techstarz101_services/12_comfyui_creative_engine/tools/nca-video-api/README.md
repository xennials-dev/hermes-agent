# 🎬 NCA FFmpeg Video API (`nca-video-api`)

**Stack B · Service #12: ComfyUI Creative Engine (`TS101-SRV-12`)**

- **Role:** Headless FFmpeg REST API for caption burn-in, reel stitching & 9:16/16:9 reformatting
- **Upstream Repo:** https://github.com/stephengpope/no-code-architects-toolkit
- **License:** GPL-2.0
- **Local App URL:** http://localhost:7010
- **One-Click Hub Launch Link:** `http://localhost:7876/t/nca-video-api`
- **Estimated RAM:** ~550 MB

## Run Standalone (Independent of Hub)

```bash
cp .env.example .env
docker compose up -d
```

## First-Run Notes
POST JSON jobs from n8n to stitch ComfyUI clips, burn subtitles, and normalize audio into ad-ready MP4s.
