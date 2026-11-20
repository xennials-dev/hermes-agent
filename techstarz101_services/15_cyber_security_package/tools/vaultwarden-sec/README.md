# 🔐 Vaultwarden Zero-Trust (`vaultwarden-sec`)

**Stack B · Service #15: Cyber Security Package (`TS101-SRV-15`)**

- **Role:** Self-hosted Bitwarden-compatible encrypted vault for SSH keys, API tokens & 2FA
- **Upstream Repo:** https://github.com/dani-garcia/vaultwarden
- **License:** GPL-3.0
- **Local App URL:** http://localhost:7610
- **One-Click Hub Launch Link:** `http://localhost:7879/t/vaultwarden-sec`
- **Estimated RAM:** ~120 MB

## Run Standalone (Independent of Hub)

```bash
cp .env.example .env
docker compose up -d
```

## First-Run Notes
Create your team vault account and eliminate plaintext credentials across repos and servers.
