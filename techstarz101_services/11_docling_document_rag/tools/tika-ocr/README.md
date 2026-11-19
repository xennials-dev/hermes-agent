# 🔍 Apache Tika + Tesseract (`tika-ocr`)

**Stack A · Service #11: Docling Document RAG (`TS101-SRV-11`)**

- **Role:** Fallback parser & OCR engine for 1,000+ legacy Office, email & scanned formats
- **Upstream Repo:** https://github.com/apache/tika
- **License:** Apache-2.0
- **Local App URL:** http://localhost:6730
- **One-Click Hub Launch Link:** `http://localhost:7874/t/tika-ocr`
- **Estimated RAM:** ~700 MB

## Run Standalone (Independent of Hub)

```bash
cp .env.example .env
docker compose up -d
```

## First-Run Notes
PUT any binary file to http://localhost:6730/tika or /rmeta for instant text + metadata extraction.
