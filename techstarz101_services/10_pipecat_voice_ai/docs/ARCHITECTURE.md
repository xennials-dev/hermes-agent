# System Architecture — Service #10: Pipecat 24/7 Voice AI

## 1. End-to-End Voice Turn Pipeline
```
Caller Phone / Browser
   │ (SIP Trunk or WebRTC)
   ▼
LiveKit (:6500)  /  Asterisk SIP PBX (:6600)
   │ (20ms PCM frames)
   ▼
Pipecat Pipeline Orchestrator
   ├─► Silero VAD (~48ms) — endpointing & barge-in interruption
   ├─► Speaches Faster-Whisper (:6520, ~178ms) — streaming transcription
   ├─► Streaming LLM / Open WebUI (:6620, ~235ms TTFT) — intent + tool calls
   │       ├─► Cal.com (:6530) — live slot check & booking
   │       └─► n8n Call Router (:6630) — SMS confirmation & CRM sync
   └─► Kokoro-FastAPI (:6510, ~124ms TTFB) / OpenedAI Piper (:6610, ~142ms)
   │ (streaming audio frames)
   ▼
Caller Hears Natural Reply in ~624ms E2E
```

## 2. Port & Network Isolation
Every tool has its own `tools/<id>/docker-compose.yml` and `.env.example`:
- **Hub Control Plane:** `http://localhost:7873` (FastAPI + Uvicorn)
- **Stack A (WebRTC & Neural TTS):** `:6500` (LiveKit), `:6510` (Kokoro-FastAPI), `:6520` (Speaches), `:6530` (Cal.com)
- **Stack B (SIP PBX & CPU Piper):** `:6600` (Asterisk ARI + SIP `:5060`), `:6610` (OpenedAI Speech), `:6620` (Open WebUI), `:6630` (n8n Call Router)

## 3. Barge-In & Interruption Handling
Pipecat's frame-based pipeline cancels in-flight LLM and TTS audio frames immediately when Silero VAD detects caller speech during playout, delivering natural human-like turn-taking without awkward overlap.
