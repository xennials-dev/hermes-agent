# 📡 LiveKit WebRTC & SIP (`livekit`)

**Stack A · Service #10: Pipecat 24/7 Voice AI (`TS101-SRV-10`)**

- **Role:** Ultra-low-latency WebRTC & SIP media server powering Pipecat voice streams
- **Upstream Repo:** https://github.com/livekit/livekit
- **License:** Apache-2.0
- **Local App URL:** http://localhost:6500
- **One-Click Hub Launch Link:** `http://localhost:7873/t/livekit`
- **Estimated RAM:** ~300 MB

## Run Standalone (Independent of Hub)

```bash
cp .env.example .env
docker compose up -d
```

## First-Run Notes
Runs in dev mode locally on ws://localhost:6500 (API key: devkey / secret: secret) ready for Pipecat.
