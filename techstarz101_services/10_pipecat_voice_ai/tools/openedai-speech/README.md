# 🔊 OpenedAI Speech (Piper) (`openedai-speech`)

**Stack B · Service #10: Pipecat 24/7 Voice AI (`TS101-SRV-10`)**

- **Role:** Drop-in OpenAI /v1/audio/speech server powered by ultra-fast CPU Piper voices
- **Upstream Repo:** https://github.com/matatonic/openedai-speech
- **License:** GPL-3.0
- **Local App URL:** http://localhost:6610/docs
- **One-Click Hub Launch Link:** `http://localhost:7873/t/openedai-speech`
- **Estimated RAM:** ~650 MB

## Run Standalone (Independent of Hub)

```bash
cp .env.example .env
docker compose up -d
```

## First-Run Notes
Runs blazingly fast on CPU-only VPS nodes; test voices via Swagger UI at /docs.
