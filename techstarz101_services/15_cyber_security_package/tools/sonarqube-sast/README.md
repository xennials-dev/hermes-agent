# 🛡️ SonarQube SAST (`sonarqube-sast`)

**Stack A · Service #15: Cyber Security Package (`TS101-SRV-15`)**

- **Role:** Static Application Security Testing (SAST), OWASP Top 10 & secret leak code analyzer
- **Upstream Repo:** https://github.com/SonarSource/sonarqube
- **License:** LGPL-3.0
- **Local App URL:** http://localhost:7520
- **One-Click Hub Launch Link:** `http://localhost:7879/t/sonarqube-sast`
- **Estimated RAM:** ~1800 MB

## Run Standalone (Independent of Hub)

```bash
cp .env.example .env
docker compose up -d
```

## First-Run Notes
Default local login: admin / admin (prompts to update on first sign-in). Connect GitHub repos for SAST.
