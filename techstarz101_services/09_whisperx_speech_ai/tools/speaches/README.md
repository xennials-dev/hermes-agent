# 🎙️ Speaches (Faster-Whisper API) (Standalone Tool Repo)

- **Role:** OpenAI-compatible CTranslate2 Whisper speech-to-text server with word timestamps
- **Stack:** Stack A
- **Upstream Open-Source Repo:** https://github.com/speaches-ai/speaches (MIT)
- **Dedicated Launch Link (Auto-Boots & Opens):** http://localhost:7872/t/speaches
- **Direct Application Port:** http://localhost:6300/docs

## Run Individually (One Click via Hub)
1. Start the Service #09 Hub: `python techstarz101_services/09_whisperx_speech_ai/hub/app.py`
2. Click **[http://localhost:7872/t/speaches](http://localhost:7872/t/speaches)** (or click the 🎙️ icon on the Hub).

## Run Individually (Standalone Docker Compose)
```bash
cd techstarz101_services/09_whisperx_speech_ai/tools/speaches
docker compose up -d
```

## First-Run Notes
Open Swagger UI at /docs or POST audio to /v1/audio/transcriptions (100% OpenAI SDK compatible).
