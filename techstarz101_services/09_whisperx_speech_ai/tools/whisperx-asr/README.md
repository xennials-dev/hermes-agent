# ⚡ WhisperX ASR Webservice (Standalone Tool Repo)

- **Role:** Turnkey REST ASR & diarization API with Swagger UI and SRT/VTT/JSON export
- **Stack:** Stack A
- **Upstream Open-Source Repo:** https://github.com/ahmetoner/whisper-asr-webservice (MIT)
- **Dedicated Launch Link (Auto-Boots & Opens):** http://localhost:7872/t/whisperx-asr
- **Direct Application Port:** http://localhost:6310/docs

## Run Individually (One Click via Hub)
1. Start the Service #09 Hub: `python techstarz101_services/09_whisperx_speech_ai/hub/app.py`
2. Click **[http://localhost:7872/t/whisperx-asr](http://localhost:7872/t/whisperx-asr)** (or click the ⚡ icon on the Hub).

## Run Individually (Standalone Docker Compose)
```bash
cd techstarz101_services/09_whisperx_speech_ai/tools/whisperx-asr
docker compose up -d
```

## First-Run Notes
Open /docs to upload any MP3/WAV/MP4 and export word-aligned SRT, VTT, or JSON transcripts.
