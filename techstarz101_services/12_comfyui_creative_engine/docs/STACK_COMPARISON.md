# Stack Comparison — Service #12: ComfyUI Creative Engine

| Dimension | Stack A: Node-Based Visual & CDN | Stack B: Canvas, Reels & Batch DAM |
| --- | --- | --- |
| **Generation Engine** | ComfyUI Node Studio (`:6900`) | InvokeAI Infinite Canvas (`:7000`) |
| **Post-Processing** | Rembg Cutout API (`:6910`) + imgproxy (`:6930`) | NCA FFmpeg Video API (`:7010`) |
| **Asset Storage / DAM** | MinIO S3 Vault (`:6920`) | PhotoPrism Visual DAM (`:7020`) |
| **Batch Orchestration** | Direct ComfyUI `/prompt` API | n8n Creative Orchestrator (`:7030`) |
| **Best For** | Programmable headless SKU-to-ad batch generation & CDN delivery | Interactive art direction, inpainting, 9:16 video reel assembly & client galleries |

> **Mix & Match:** Combine **ComfyUI** (`:6900`) + **NCA FFmpeg API** (`:7010`) + **PhotoPrism DAM** (`:7020`) + **n8n Creative** (`:7030`) directly from the Modular Hub checkboxes.
