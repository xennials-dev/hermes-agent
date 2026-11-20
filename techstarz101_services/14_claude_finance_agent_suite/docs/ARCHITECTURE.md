# System Architecture — Service #14: Claude Finance Agent Suite

## 1. End-to-End 10-Agent Diligence Topology
```
CIM / 10-K / Data Room Intake
   │
   ├─► Docling Filings (:7320) — 93.6% table accuracy financial extraction
   ├─► OpenBB Financial API (:7300) — live market comps & SEC EDGAR feeds
   ├─► Jupyter Quant Lab (:7310) — reproducible Python DCF & LBO models
   ├─► OpenSanctions Yente (:7400) — real-time OFAC / PEP / UBO KYC screening
   │
   ▼
n8n 10-Agent Orchestrator (:7430)
   ├─► NocoDB Deal Room (:7410) — deal pipeline, VDR checklist & IC approval
   ├─► Metabase IC (:7330) — portfolio & LP KPI dashboards
   └─► Langfuse Audit Ledger (:7420) — immutable prompt, citation & hash trail
```

## 2. Port & Network Isolation
- **Modular Hub:** `http://localhost:7878`
- **Stack A:** `:7300` (OpenBB), `:7310` (Jupyter Quant), `:7320` (Docling Filings), `:7330` (Metabase IC)
- **Stack B:** `:7400` (Yente KYC), `:7410` (NocoDB Deal Room), `:7420` (Langfuse Audit), `:7430` (n8n Finance)
