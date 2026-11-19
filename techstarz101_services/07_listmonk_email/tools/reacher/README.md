# 🛡️ Reacher Email Verifier (Standalone Tool Repo)

- **Role:** Self-hosted Rust MX/SMTP email verification API keeping bounce rates <1%
- **Stack:** Stack A
- **Upstream Open-Source Repo:** https://github.com/reacherhq/check-if-email-exists (AGPL-3.0)
- **Dedicated Launch Link (Auto-Boots & Opens):** http://localhost:7871/t/reacher
- **Direct Application Port:** http://localhost:6130

## Run Individually (One Click via Hub)
1. Start the Service #07 Hub: `python techstarz101_services/07_listmonk_email/hub/app.py`
2. Click **[http://localhost:7871/t/reacher](http://localhost:7871/t/reacher)** (or click the 🛡️ icon on the Hub).

## Run Individually (Standalone Docker Compose)
```bash
cd techstarz101_services/07_listmonk_email/tools/reacher
docker compose up -d
```

## First-Run Notes
POST JSON {"to_email":"lead@domain.com"} to http://localhost:6130/v0/check_email for instant verification.
