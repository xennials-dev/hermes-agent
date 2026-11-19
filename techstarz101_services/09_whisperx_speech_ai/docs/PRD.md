# Product Requirements Document (PRD) — WhisperX Speech AI

**Service ID:** `TS101-SRV-09`  
**Product Name:** Techstarz101 WhisperX Speech AI (70x Real-Time Diarization & Timestamps)  
**Status:** Production Ready  
**Localhost Hub:** `http://localhost:7872`  
**Live Catalog Reference:** `https://techstarz101.com/agents/whisperx-transcription`

---

## 1. Executive Summary
Sales teams, podcasters, and legal/medical operations pay punitive per-minute cloud transcription fees (Gong, Otter, Rev, AssemblyAI) while sending confidential audio to third-party servers.
The **Techstarz101 WhisperX Speech AI** suite delivers **8 standalone, click-to-launch open-source app repos** across 2 composable stacks:
- 70x real-time transcription with word-level timestamps & speaker diarization (Speaches / WhisperX ASR)
- Private S3 audio vault (MinIO) + sub-50ms full-text transcript search (Meilisearch)
- Meeting summary & subtitle studio (Scriberr / Whisper-WebUI), waveform QA (Label Studio), and CRM sync (n8n)
