# Product Requirements Document (PRD) — Service #12: ComfyUI Creative Engine

## 1. Objective
Deliver a 100% open-source, self-hosted product visual and video creative factory that turns raw SKU descriptions or product cutouts into studio-grade multi-platform ad packs (1:1 Instagram, 9:16 TikTok/Reels, 16:9 YouTube/Web) at ~\$0.002/render instead of \$0.35+ commercial SaaS credits.

## 2. Target Users & Jobs-to-be-Done
- **E-Commerce & DTC Brands:** Generate dozens of on-brand studio product shots per SKU without booking physical photoshoots.
- **Performance Marketing Agencies:** Batch-produce A/B ad creative variants, transparent cutouts, and captioned 9:16 product reels directly from n8n webhooks.
- **In-House Creative Directors:** Retouch lighting and swap backgrounds on InvokeAI's infinite canvas, then review and approve client galleries in PhotoPrism DAM.

## 3. Core Functional Requirements
1. **API-Driven Node Graphs:** Compile reproducible ComfyUI JSON workflows (`POST /api/creative/generate-workflow`) with locked seeds, CFG, sampler, and engineered prompts.
2. **Automated Post-Processing & Resizing:** Wire Rembg background removal (`:6910`), MinIO S3 storage (`:6920`), imgproxy on-the-fly resizing (`:6930`), and NCA FFmpeg video assembly (`:7010`).
3. **Standalone Modularity:** Every tool operates independently under `tools/<id>/` on dedicated ports (`:6900`–`:7030`) with clickable `/t/<id>` launchers.
