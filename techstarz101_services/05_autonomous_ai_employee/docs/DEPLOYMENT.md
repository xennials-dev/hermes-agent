# Production Deployment Guide — Autonomous AI Employee

## 1. Localhost Hub Review
```powershell
python techstarz101_services/05_autonomous_ai_employee/hub/app.py
```
Open **[http://localhost:7869](http://localhost:7869)** to click any tool's repo icon (`/t/<tool>`), stack selected tools, or test the Executive Task Delegator.

## 2. Standalone Single-Tool CLI Deployment
```bash
cd techstarz101_services/05_autonomous_ai_employee/tools/qdrant
docker compose up -d
```

## 3. Governance & Budget Safety
- Point all agents through **LiteLLM** (`http://localhost:5820`) to enforce hard per-day USD spend caps.
- Route external actions (sending emails, creating invoices, updating CRM stages) through **NocoDB** (`http://localhost:5830`) approval rows or **Langfuse** (`http://localhost:5730`) audit traces.
