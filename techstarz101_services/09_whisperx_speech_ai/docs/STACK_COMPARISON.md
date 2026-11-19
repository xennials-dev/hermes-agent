# Two Open-Source Tool Stacks Comparison — WhisperX Speech AI

## Stack A: 70x Real-Time Diarization & Search (4 Standalone Repos)

| Tool Repo | Dedicated Launch Link | Direct Port | Upstream Repo | Role |
| :--- | :--- | :--- | :--- | :--- |
| **Speaches** (`tools/speaches/`) | `http://localhost:7872/t/speaches` | `:6300/docs` | `speaches-ai/speaches` | OpenAI-compatible Faster-Whisper API |
| **WhisperX ASR** (`tools/whisperx-asr/`) | `http://localhost:7872/t/whisperx-asr` | `:6310/docs` | `ahmetoner/whisper-asr-webservice` | REST ASR & SRT/VTT/JSON webservice |
| **MinIO Vault** (`tools/minio/`) | `http://localhost:7872/t/minio` | `:6320` | `minio/minio` | S3-compatible audio & transcript vault |
| **Meilisearch** (`tools/meilisearch/`) | `http://localhost:7872/t/meilisearch` | `:6330` | `meilisearch/meilisearch` | Sub-50ms full-text transcript search |

## Stack B: Meeting Intelligence & Subtitle Studio (4 Standalone Repos)

| Tool Repo | Dedicated Launch Link | Direct Port | Upstream Repo | Role |
| :--- | :--- | :--- | :--- | :--- |
| **Scriberr** (`tools/scriberr/`) | `http://localhost:7872/t/scriberr` | `:6400` | `rishikanthc/Scriberr` | AI diarization & meeting summary app |
| **Whisper-WebUI** (`tools/whisper-webui/`) | `http://localhost:7872/t/whisper-webui` | `:6410` | `jhj0517/Whisper-WebUI` | Visual video & YouTube SRT/VTT studio |
| **Label Studio** (`tools/label-studio/`) | `http://localhost:7872/t/label-studio` | `:6420` | `HumanSignal/label-studio` | Audio waveform & speaker-turn QA UI |
| **n8n Speech** (`tools/n8n-speech/`) | `http://localhost:7872/t/n8n-speech` | `:6430` | `n8n-io/n8n` | Automated audio-to-CRM pipelines |
