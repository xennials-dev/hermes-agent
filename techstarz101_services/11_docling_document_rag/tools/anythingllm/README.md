# 💬 AnythingLLM RAG Studio (`anythingllm`)

**Stack A · Service #11: Docling Document RAG (`TS101-SRV-11`)**

- **Role:** Turnkey document workspace with citation grounding, permissions & agent skills
- **Upstream Repo:** https://github.com/Mintplex-Labs/anything-llm
- **License:** MIT
- **Local App URL:** http://localhost:6720
- **One-Click Hub Launch Link:** `http://localhost:7874/t/anythingllm`
- **Estimated RAM:** ~850 MB

## Run Standalone (Independent of Hub)

```bash
cp .env.example .env
docker compose up -d
```

## First-Run Notes
Create a workspace, connect Qdrant (:6710) or built-in LanceDB, and chat over Docling Markdown.
