# Deployment Guide — Service #11: Docling Document RAG

## 1. Local Modular Hub
```bash
cd techstarz101_services/11_docling_document_rag
python hub/app.py
# Open http://localhost:7874
```

## 2. Boot Any Tool Independently
```bash
cd tools/docling-serve
cp .env.example .env
docker compose up -d
# Open http://localhost:6700/ui
```

## 3. Production Notes
- Allocate at least **8 GB RAM** on your host when running IBM Docling Serve (`:6700`) + Paperless-ngx (`:6800`) simultaneously.
- Enable GPU passthrough (`--gpus all`) on `docling-serve` if processing >500 complex PDF pages/hour.
- Import `automations/stack_a_docling_qdrant_ingest.n8n.json` or `automations/stack_b_paperless_weaviate_sync.n8n.json` into n8n (`:6830`) for automated watch-folder ingestion.
