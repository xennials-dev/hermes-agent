# 🔀 n8n Document Pipeline (`n8n-ingest`)

**Stack B · Service #11: Docling Document RAG (`TS101-SRV-11`)**

- **Role:** Automated watch-folder, Gmail & S3 -> Docling -> Vector DB ingestion orchestrator
- **Upstream Repo:** https://github.com/n8n-io/n8n
- **License:** Sustainable Use (fair-code)
- **Local App URL:** http://localhost:6830
- **One-Click Hub Launch Link:** `http://localhost:7874/t/n8n-ingest`
- **Estimated RAM:** ~400 MB

## Run Standalone (Independent of Hub)

```bash
cp .env.example .env
docker compose up -d
```

## First-Run Notes
Import /automations/stack_a_docling_qdrant_ingest.n8n.json to automate zero-touch PDF indexing.
