# 📝 Scriberr Meeting Studio (Standalone Tool Repo)

- **Role:** Self-hosted AI audio transcription, speaker diarization & meeting summary app
- **Stack:** Stack B
- **Upstream Open-Source Repo:** https://github.com/rishikanthc/Scriberr (MIT)
- **Dedicated Launch Link (Auto-Boots & Opens):** http://localhost:7872/t/scriberr
- **Direct Application Port:** http://localhost:6400

## Run Individually (One Click via Hub)
1. Start the Service #09 Hub: `python techstarz101_services/09_whisperx_speech_ai/hub/app.py`
2. Click **[http://localhost:7872/t/scriberr](http://localhost:7872/t/scriberr)** (or click the 📝 icon on the Hub).

## Run Individually (Standalone Docker Compose)
```bash
cd techstarz101_services/09_whisperx_speech_ai/tools/scriberr
docker compose up -d
```

## First-Run Notes
Upload podcasts or sales calls directly in the web UI for diarized transcripts & AI summaries.
