# 🔀 n8n Speech Automator (Standalone Tool Repo)

- **Role:** Auto-watch MinIO audio uploads -> transcribe -> index in Meilisearch -> CRM
- **Stack:** Stack B
- **Upstream Open-Source Repo:** https://github.com/n8n-io/n8n (Sustainable Use (fair-code))
- **Dedicated Launch Link (Auto-Boots & Opens):** http://localhost:7872/t/n8n-speech
- **Direct Application Port:** http://localhost:6430

## Run Individually (One Click via Hub)
1. Start the Service #09 Hub: `python techstarz101_services/09_whisperx_speech_ai/hub/app.py`
2. Click **[http://localhost:7872/t/n8n-speech](http://localhost:7872/t/n8n-speech)** (or click the 🔀 icon on the Hub).

## Run Individually (Standalone Docker Compose)
```bash
cd techstarz101_services/09_whisperx_speech_ai/tools/n8n-speech
docker compose up -d
```

## First-Run Notes
Import /automations/stack_a_audio_to_search_index.n8n.json to automate end-to-end call processing.
