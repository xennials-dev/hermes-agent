# ☎️ Asterisk SIP PBX (`asterisk`)

**Stack B · Service #10: Pipecat 24/7 Voice AI (`TS101-SRV-10`)**

- **Role:** Self-hosted SIP phone trunk router with ARI REST/WebSocket audio bridge
- **Upstream Repo:** https://github.com/asterisk/asterisk
- **License:** GPL-2.0
- **Local App URL:** http://localhost:6600/ari/api-docs/resources.json
- **One-Click Hub Launch Link:** `http://localhost:7873/t/asterisk`
- **Estimated RAM:** ~350 MB

## Run Standalone (Independent of Hub)

```bash
cp .env.example .env
docker compose up -d
```

## First-Run Notes
Exposes SIP :5060 and ARI HTTP :6600 to bridge Twilio/Telnyx/VoIP.ms trunks straight into Pipecat.
