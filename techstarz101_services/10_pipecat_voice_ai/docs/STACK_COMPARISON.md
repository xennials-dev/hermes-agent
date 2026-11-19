# Stack Comparison — Service #10: Pipecat 24/7 Voice AI

| Dimension | Stack A: Sovereign WebRTC & Kokoro | Stack B: Asterisk SIP PBX & Piper |
| --- | --- | --- |
| **Transport** | LiveKit WebRTC & SIP (`:6500`) | Asterisk SIP PBX + ARI (`:6600`) |
| **TTS Engine** | Kokoro-FastAPI 82M (`:6510`) | OpenedAI Speech Piper (`:6610`) |
| **STT / Brain** | Speaches Faster-Whisper (`:6520`) | Open WebUI + Ollama (`:6620`) |
| **Booking / Workflow** | Cal.com Native Booking (`:6530`) | n8n Call Router (`:6630`) |
| **Typical E2E Latency** | **~624ms** (Sub-800ms) | **~740ms** (Sub-800ms) |
| **Hardware Profile** | 1× GPU (or fast CPU) · ~4.3 GB RAM | CPU-only VPS friendly · ~2.3 GB RAM |
| **Best For** | Browser/WebRTC + SIP voice receptionists with ultra-natural voices and live calendar booking | Traditional VoIP/SIP trunks (Telnyx, VoIP.ms, Twilio BYOC), after-hours IVR, and low-cost CPU VPS deployments |
| **Estimated Cost/Min** | ~\$0.008/min | ~\$0.004/min |

> **Mix & Match:** Because every tool is a standalone repo, you can check tools across both stacks (e.g., **Asterisk SIP** + **Kokoro-FastAPI** + **Cal.com** + **n8n Call Router**) and boot your exact custom combination from the Modular Hub.
