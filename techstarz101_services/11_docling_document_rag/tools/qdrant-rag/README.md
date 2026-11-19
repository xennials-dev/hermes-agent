# 🔷 Qdrant Vector DB (`qdrant-rag`)

**Stack A · Service #11: Docling Document RAG (`TS101-SRV-11`)**

- **Role:** Sub-10ms dense + sparse hybrid vector store with built-in Web Dashboard
- **Upstream Repo:** https://github.com/qdrant/qdrant
- **License:** Apache-2.0
- **Local App URL:** http://localhost:6710/dashboard
- **One-Click Hub Launch Link:** `http://localhost:7874/t/qdrant-rag`
- **Estimated RAM:** ~500 MB

## Run Standalone (Independent of Hub)

```bash
cp .env.example .env
docker compose up -d
```

## First-Run Notes
Inspect collections, payload filters, and HNSW vector graphs directly at /dashboard.
