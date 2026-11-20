# Deployment Guide — Service #14: Claude Finance Agent Suite

## 1. Local Modular Hub
```bash
cd techstarz101_services/14_claude_finance_agent_suite
python hub/app.py
# Open http://localhost:7878
```

## 2. Boot Any Tool Independently
```bash
cd tools/yente-kyc
cp .env.example .env
docker compose up -d
# Open http://localhost:7400/docs
```

## 3. Compliance & Security Hardening
- Keep `docling-filings` (`:7320`), `yente-kyc` (`:7400`), and `langfuse-audit` (`:7420`) inside a private VPC/Tailscale subnet for live client deal rooms.
- Always back up `langfuse-audit` Postgres volumes to preserve immutable SEC/FINRA-grade agent decision logs.
