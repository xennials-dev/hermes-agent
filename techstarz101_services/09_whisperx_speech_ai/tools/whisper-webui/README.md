# 🎬 Whisper-WebUI Studio (Standalone Tool Repo)

- **Role:** Visual Gradio subtitle studio for local audio, video & YouTube SRT/VTT captions
- **Stack:** Stack B
- **Upstream Open-Source Repo:** https://github.com/jhj0517/Whisper-WebUI (MIT)
- **Dedicated Launch Link (Auto-Boots & Opens):** http://localhost:7872/t/whisper-webui
- **Direct Application Port:** http://localhost:6410

## Run Individually (One Click via Hub)
1. Start the Service #09 Hub: `python techstarz101_services/09_whisperx_speech_ai/hub/app.py`
2. Click **[http://localhost:7872/t/whisper-webui](http://localhost:7872/t/whisper-webui)** (or click the 🎬 icon on the Hub).

## Run Individually (Standalone Docker Compose)
```bash
cd techstarz101_services/09_whisperx_speech_ai/tools/whisper-webui
docker compose up -d
```

## First-Run Notes
Drag-and-drop video/audio files or paste YouTube URLs to export synced SRT/VTT/LRC captions.
