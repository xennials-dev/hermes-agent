# 🧠 Open WebUI Doc Chat (`open-webui-rag`)

**Stack B · Service #11: Docling Document RAG (`TS101-SRV-11`)**

- **Role:** Multi-model knowledge base chat UI wired to local Ollama & Docling loaders
- **Upstream Repo:** https://github.com/open-webui/open-webui
- **License:** MIT
- **Local App URL:** http://localhost:6820
- **One-Click Hub Launch Link:** `http://localhost:7874/t/open-webui-rag`
- **Estimated RAM:** ~900 MB

## Run Standalone (Independent of Hub)

```bash
cp .env.example .env
docker compose up -d
```

## First-Run Notes
No login required locally (WEBUI_AUTH=False). Attach Knowledge collections to any model.
