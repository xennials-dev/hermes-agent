# 🧬 Weaviate Hybrid Search (`weaviate-rag`)

**Stack B · Service #11: Docling Document RAG (`TS101-SRV-11`)**

- **Role:** AI-native vector + BM25 keyword hybrid database for legal & financial RAG
- **Upstream Repo:** https://github.com/weaviate/weaviate
- **License:** BSD-3-Clause
- **Local App URL:** http://localhost:6810/v1/meta
- **One-Click Hub Launch Link:** `http://localhost:7874/t/weaviate-rag`
- **Estimated RAM:** ~650 MB

## Run Standalone (Independent of Hub)

```bash
cp .env.example .env
docker compose up -d
```

## First-Run Notes
Query /v1/graphql with hybrid alpha=0.5 to blend exact SKU/clause matching with semantic search.
