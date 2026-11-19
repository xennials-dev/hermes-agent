# 🗄️ MinIO Audio Vault (Standalone Tool Repo)

- **Role:** S3-compatible sovereign object storage for raw call recordings & transcripts
- **Stack:** Stack A
- **Upstream Open-Source Repo:** https://github.com/minio/minio (AGPL-3.0)
- **Dedicated Launch Link (Auto-Boots & Opens):** http://localhost:7872/t/minio
- **Direct Application Port:** http://localhost:6320

## Run Individually (One Click via Hub)
1. Start the Service #09 Hub: `python techstarz101_services/09_whisperx_speech_ai/hub/app.py`
2. Click **[http://localhost:7872/t/minio](http://localhost:7872/t/minio)** (or click the 🗄️ icon on the Hub).

## Run Individually (Standalone Docker Compose)
```bash
cd techstarz101_services/09_whisperx_speech_ai/tools/minio
docker compose up -d
```

## First-Run Notes
Log in with minioadmin and MINIO_ROOT_PASSWORD from tools/minio/.env; create bucket 'audio-inbox'.
