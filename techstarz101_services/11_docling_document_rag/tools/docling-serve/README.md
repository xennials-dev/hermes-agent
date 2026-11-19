# 📄 IBM Docling Serve (`docling-serve`)

**Stack A · Service #11: Docling Document RAG (`TS101-SRV-11`)**

- **Role:** Layout-aware PDF/DOCX/PPTX parser with 93.6% table structure accuracy & UI
- **Upstream Repo:** https://github.com/docling-project/docling-serve
- **License:** MIT
- **Local App URL:** http://localhost:6700/ui
- **One-Click Hub Launch Link:** `http://localhost:7874/t/docling-serve`
- **Estimated RAM:** ~1600 MB

## Run Standalone (Independent of Hub)

```bash
cp .env.example .env
docker compose up -d
```

## First-Run Notes
Open /ui to drag-and-drop PDFs or POST to /v1/convert/file for structured Markdown & JSON tables.
