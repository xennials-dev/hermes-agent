# 🗣️ Kokoro-FastAPI TTS (`kokoro-tts`)

**Stack A · Service #10: Pipecat 24/7 Voice AI (`TS101-SRV-10`)**

- **Role:** Human-grade OpenAI-compatible neural TTS with <150ms first-byte latency + Web UI
- **Upstream Repo:** https://github.com/remsky/Kokoro-FastAPI
- **License:** Apache-2.0
- **Local App URL:** http://localhost:6510/web/
- **One-Click Hub Launch Link:** `http://localhost:7873/t/kokoro-tts`
- **Estimated RAM:** ~1200 MB

## Run Standalone (Independent of Hub)

```bash
cp .env.example .env
docker compose up -d
```

## First-Run Notes
Open /web/ to audition voices or POST to /v1/audio/speech from Pipecat at <150ms TTFB.
