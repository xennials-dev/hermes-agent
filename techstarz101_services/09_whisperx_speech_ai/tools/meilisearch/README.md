# 🔎 Meilisearch Transcripts (Standalone Tool Repo)

- **Role:** Sub-50ms full-text search engine across thousands of diarized transcripts
- **Stack:** Stack A
- **Upstream Open-Source Repo:** https://github.com/meilisearch/meilisearch (MIT)
- **Dedicated Launch Link (Auto-Boots & Opens):** http://localhost:7872/t/meilisearch
- **Direct Application Port:** http://localhost:6330

## Run Individually (One Click via Hub)
1. Start the Service #09 Hub: `python techstarz101_services/09_whisperx_speech_ai/hub/app.py`
2. Click **[http://localhost:7872/t/meilisearch](http://localhost:7872/t/meilisearch)** (or click the 🔎 icon on the Hub).

## Run Individually (Standalone Docker Compose)
```bash
cd techstarz101_services/09_whisperx_speech_ai/tools/meilisearch
docker compose up -d
```

## First-Run Notes
Use MEILI_MASTER_KEY from tools/meilisearch/.env to search spoken phrases & speaker turns instantly.
