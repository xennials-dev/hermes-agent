# System Architecture — Service #11: Docling Document RAG

## 1. Document Ingestion & Retrieval Pipeline
```
PDF / DOCX / PPTX / Scanned Invoices
   │
   ▼
IBM Docling Serve (:6700)  [Fallback: Apache Tika + Tesseract (:6730)]
   ├─► Layout Analysis (headings, reading order, bounding boxes)
   ├─► TableFormer (93.6% table structure reconstruction -> Markdown/JSON)
   └─► Table-Atomic Semantic Chunker
          │
          ▼
Qdrant (:6710)  /  Weaviate Hybrid BM25+Vector (:6810)
          │
          ▼
AnythingLLM (:6720)  /  Open WebUI (:6820) — Citation-Grounded RAG Chat
```

## 2. Port & Network Isolation
- **Modular Hub:** `http://localhost:7874`
- **Stack A:** `:6700` (Docling Serve), `:6710` (Qdrant), `:6720` (AnythingLLM), `:6730` (Apache Tika)
- **Stack B:** `:6800` (Paperless-ngx), `:6810` (Weaviate), `:6820` (Open WebUI wired to `DOCLING_SERVER_URL=http://host.docker.internal:6700`), `:6830` (n8n Ingest)
