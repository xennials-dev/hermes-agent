# 🧠 Open WebUI Voice Brain (`voice-llm`)

**Stack B · Service #10: Pipecat 24/7 Voice AI (`TS101-SRV-10`)**

- **Role:** Local LLM receptionist prompt studio & objection-handling knowledge base
- **Upstream Repo:** https://github.com/open-webui/open-webui
- **License:** MIT
- **Local App URL:** http://localhost:6620
- **One-Click Hub Launch Link:** `http://localhost:7873/t/voice-llm`
- **Estimated RAM:** ~900 MB

## Run Standalone (Independent of Hub)

```bash
cp .env.example .env
docker compose up -d
```

## First-Run Notes
No login locally (WEBUI_AUTH=False). Test receptionist system prompts against local Ollama.
