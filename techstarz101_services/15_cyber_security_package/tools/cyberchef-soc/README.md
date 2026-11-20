# 🧪 GCHQ CyberChef SOC (`cyberchef-soc`)

**Stack B · Service #15: Cyber Security Package (`TS101-SRV-15`)**

- **Role:** Offline DFIR & SOC workbench for decoding payloads, JWTs, headers & IOC hashes
- **Upstream Repo:** https://github.com/gchq/CyberChef
- **License:** Apache-2.0
- **Local App URL:** http://localhost:7620
- **One-Click Hub Launch Link:** `http://localhost:7879/t/cyberchef-soc`
- **Estimated RAM:** ~90 MB

## Run Standalone (Independent of Hub)

```bash
cp .env.example .env
docker compose up -d
```

## First-Run Notes
100% browser-local DFIR analysis — inspect suspicious logs, certificates, and IOCs safely offline.
