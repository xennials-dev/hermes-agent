# Production Deployment Guide — WhisperX Speech AI

## 1. Localhost Hub Review
```powershell
python techstarz101_services/09_whisperx_speech_ai/hub/app.py
```
Open **[http://localhost:7872](http://localhost:7872)** to launch any standalone speech tool (`/t/<tool>`), stack selected tools, or test the 70x Diarization & SRT/VTT Workbench.

## 2. Standalone Single-Tool CLI Deployment
```bash
cd techstarz101_services/09_whisperx_speech_ai/tools/speaches
docker compose up -d
```

## 3. GPU Acceleration (70x Speed)
For NVIDIA GPU hosts, swap `ghcr.io/speaches-ai/speaches:latest-cpu` to `:latest-cuda` and set `WHISPER__INFERENCE_DEVICE=cuda` + `deploy.resources.reservations.devices` in `tools/speaches/docker-compose.yml`.
