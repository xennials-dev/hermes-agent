# 🎙️ Speaches Realtime STT (`speaches-stt`)

**Stack A · Service #10: Pipecat 24/7 Voice AI (`TS101-SRV-10`)**

- **Role:** Streaming Faster-Whisper speech-to-text server for sub-250ms turn detection
- **Upstream Repo:** https://github.com/speaches-ai/speaches
- **License:** MIT
- **Local App URL:** http://localhost:6520/docs
- **One-Click Hub Launch Link:** `http://localhost:7873/t/speaches-stt`
- **Estimated RAM:** ~1400 MB

## Run Standalone (Independent of Hub)

```bash
cp .env.example .env
docker compose up -d
```

## First-Run Notes
Swagger UI on /docs; Pipecat connects to http://host.docker.internal:6520/v1 for real-time STT.
