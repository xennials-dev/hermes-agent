# Production Deployment Guide — AI Opportunity Audit ($750)

## 1. Localhost Hub Review
```powershell
python techstarz101_services/06_ai_opportunity_audit/hub/app.py
```
Open **[http://localhost:7870](http://localhost:7870)** to launch any individual audit tool (`/t/<tool>`), stack selected tools, or run the live 360° ROI Scorecard & Markdown Report generator.

## 2. Standalone Single-Tool CLI Deployment
```bash
cd techstarz101_services/06_ai_opportunity_audit/tools/docuseal
docker compose up -d
```

## 3. End-to-End Client Audit Delivery Flow
1. Send client the **Formbricks** (`:5900`) 360° intake survey.
2. Client books kickoff via **Cal.com** (`:5910`) and signs the 100%-credited $750 SOW in **DocuSeal** (`:5930`).
3. Map bottlenecks live in **Excalidraw** (`:6000`), calculate ROI in **Grist** (`:6010`), assemble the executive PDF in **Stirling-PDF** (`:6020`), publish in **BookStack** (`:5920`), and track the $750 credit in **Kimai** (`:6030`).
