# 🎧 Label Studio Audio QA (Standalone Tool Repo)

- **Role:** Interactive audio waveform review, speaker-turn QA & fine-tuning annotation UI
- **Stack:** Stack B
- **Upstream Open-Source Repo:** https://github.com/HumanSignal/label-studio (Apache-2.0)
- **Dedicated Launch Link (Auto-Boots & Opens):** http://localhost:7872/t/label-studio
- **Direct Application Port:** http://localhost:6420

## Run Individually (One Click via Hub)
1. Start the Service #09 Hub: `python techstarz101_services/09_whisperx_speech_ai/hub/app.py`
2. Click **[http://localhost:7872/t/label-studio](http://localhost:7872/t/label-studio)** (or click the 🎧 icon on the Hub).

## Run Individually (Standalone Docker Compose)
```bash
cd techstarz101_services/09_whisperx_speech_ai/tools/label-studio
docker compose up -d
```

## First-Run Notes
Create your local account on first visit and select the 'Audio Transcription & Diarization' template.
