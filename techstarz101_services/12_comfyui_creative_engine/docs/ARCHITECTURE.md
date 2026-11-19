# System Architecture — Service #12: ComfyUI Creative Engine

## 1. Automated Creative Production Pipeline
```
SKU Brief / Product Photo
   │
   ├─► Rembg Cutout API (:6910) — transparent product PNG
   ├─► ComfyUI Node Studio (:6900) / InvokeAI Canvas (:7000) — Flux/SDXL scene & motion
   ├─► MinIO S3 Vault (:6920 / :6921) — durable raw creative storage
   ├─► imgproxy CDN (:6930) — instant 1:1, 9:16, 16:9 WebP/AVIF ad variants
   ├─► NCA FFmpeg Video API (:7010) — multi-shot 9:16 reel stitching & captions
   └─► PhotoPrism Visual DAM (:7020) — AI-tagged client review gallery
```

## 2. Port & Network Isolation
- **Modular Hub:** `http://localhost:7876`
- **Stack A:** `:6900` (ComfyUI), `:6910` (Rembg), `:6920`/`:6921` (MinIO Console/S3), `:6930` (imgproxy)
- **Stack B:** `:7000` (InvokeAI), `:7010` (NCA FFmpeg API), `:7020` (PhotoPrism), `:7030` (n8n Creative)
