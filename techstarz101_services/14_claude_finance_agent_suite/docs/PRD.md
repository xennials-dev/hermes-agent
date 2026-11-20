# Product Requirements Document (PRD) — Service #14: Claude Finance Agent Suite

## 1. Objective
Deliver a self-hosted, institutional-grade 10-agent Investment Banking (IB), Private Equity (PE), and KYC/AML diligence platform that compresses CIM/10-K review, comps benchmarking, DCF/LBO modeling, and sanctions screening from days to minutes—while keeping 100% of sensitive deal data on-premise with immutable citation audit trails.

## 2. Official 10-Agent Architecture
1. `01_SEC_EDGAR_Analyst` — Audited filing & footnote table extraction (`docling-filings :7320`)
2. `02_Comps_Valuation_Agent` — Peer EV/EBITDA & EV/Rev multiples (`openbb-platform :7300`)
3. `03_DCF_Modeler_Agent` — 5-yr FCF projection, WACC & terminal value (`jupyter-quant :7310`)
4. `04_LBO_Sponsor_Agent` — Sources/uses, debt paydown, MOIC & IRR (`jupyter-quant :7310`)
5. `05_QoE_Forensic_Agent` — Margin integrity & add-back anomaly review (`docling-filings :7320`)
6. `06_KYC_Sanctions_Agent` — Real-time OFAC/EU/UN/PEP & UBO screening (`yente-kyc :7400`)
7. `07_Legal_Diligence_Agent` — Change-of-control, customer concentration & IP checklist (`nocodb-dealroom :7410`)
8. `08_IC_Memo_Writer_Agent` — Investment Committee memo synthesis (`n8n-finance :7430`)
9. `09_Risk_Compliance_Agent` — Downside stress test & DSCR check (`metabase-ic :7330`)
10. `10_Audit_Trail_Logger` — Cryptographic decision & citation trace (`langfuse-audit :7420`)
