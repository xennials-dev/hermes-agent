# Deployment Guide — Service #10: Pipecat 24/7 Voice AI

## 1. Local Development (Modular Hub)
```bash
cd techstarz101_services/10_pipecat_voice_ai
python hub/app.py
```
Open `http://localhost:7873` in your browser.
- Click any tool icon (or `/t/<id>`) to auto-generate `.env` secrets and boot that single tool.
- Check multiple tools (or click **Boot Full Stack A / B**) to run a combined voice pipeline.

## 2. Booting a Single Tool via CLI
```bash
cd tools/kokoro-tts
cp .env.example .env
docker compose up -d
# Open http://localhost:6510/web/
```

## 3. Production VPS Deployment (SIP + TLS)
1. Provision a Linux VPS (Ubuntu 24.04, 4+ vCPU / 8 GB RAM; GPU optional for Kokoro/Speaches).
2. Open UDP/TCP `5060` (SIP) and RTP media ports (`7881–7882` for LiveKit or `10000–10100` for Asterisk).
3. Point your SIP trunk provider (Telnyx, VoIP.ms, or Twilio Elastic SIP) to your VPS public IP.
4. Put Nginx + Let's Encrypt TLS in front of LiveKit (`:6500`), Cal.com (`:6530`), and n8n (`:6630`).
5. Import `automations/stack_a_pipecat_call_booking.n8n.json` into n8n (`:6630`) and configure your Cal.com API key and SMS webhook.
