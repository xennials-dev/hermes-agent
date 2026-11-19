# Product Requirements Document (PRD) — Service #10: Pipecat 24/7 Voice AI

## 1. Objective
Deliver a 100% open-source, self-hosted 24/7 AI phone receptionist and appointment booking system with sub-800ms end-to-end turn latency, eliminating commercial voice AI SaaS fees (\$0.15–\$0.25/min on Vapi/Bland/Retell) in favor of owned infrastructure (~ \$0.004–\$0.008/min compute + wholesale SIP).

## 2. Target Users & Jobs-to-be-Done
- **Service Businesses & Clinics:** Answer 100% of inbound calls 24/7, check live Cal.com availability mid-call, and confirm bookings via SMS.
- **Agencies & Sales Teams:** Qualify inbound leads, answer pricing/audit FAQs, and log structured call summaries to Twenty CRM via n8n.
- **On-Call Engineering & Emergency Dispatch:** Detect urgent caller intent and execute warm SIP transfers via Asterisk ARI with spoken whisper context.

## 3. Core Functional Requirements
1. **Sub-800ms Turn Budget:** End-to-end conversational response (Silero VAD → Streaming STT → Streaming LLM TTFT → Streaming TTS TTFB → WebRTC/SIP audio playout) must stay under 800ms on Stack A.
2. **Mid-Call Tool Calling:** Support live calendar availability lookup, appointment creation (`calcom.create_booking`), CRM lead logging, and warm SIP transfer.
3. **Standalone Modularity:** Every component (`livekit`, `kokoro-tts`, `speaches-stt`, `calcom-voice`, `asterisk`, `openedai-speech`, `voice-llm`, `n8n-voice`) must operate independently on its own localhost port (`:6500`–`:6630`) with auto-generated `.env` secrets.
4. **Zero-Docker Preview Utility:** The Hub must ship an interactive Sub-800ms Phone Receptionist Simulator (`POST /api/voice/simulate-turn`) with live latency breakdown and browser speech synthesis.

## 4. Success Metrics
- **Latency:** `< 800ms` P50 end-to-end voice turn on Stack A (target `~624ms`).
- **Cost Reduction:** `> 95%` savings per call minute compared to commercial voice AI platforms.
- **Booking Conversion:** Direct mid-call Cal.com booking + automated post-call SMS confirmation.
