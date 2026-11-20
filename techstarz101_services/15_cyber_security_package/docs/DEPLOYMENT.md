# Deployment Guide — Service #15: Cyber Security Package

## 1. Local Modular Hub
```bash
cd techstarz101_services/15_cyber_security_package
python hub/app.py
# Open http://localhost:7879
```

## 2. Boot Any Tool Independently
```bash
cd tools/vaultwarden-sec
cp .env.example .env
docker compose up -d
# Open http://localhost:7610
```

## 3. Production Hardening Notes
- Put **Vaultwarden** (`:7610`) behind HTTPS (Nginx + Let's Encrypt) and set `SIGNUPS_ALLOWED=false` after enrolling your team.
- Bind **OWASP ZAP** (`:7500`), **Trivy** (`:7510`), and **SonarQube** (`:7520`) to a private VPN/Tailscale interface rather than the public internet.
- Only run **OWASP ZAP** against domains and APIs you own or have written authorization to test.
