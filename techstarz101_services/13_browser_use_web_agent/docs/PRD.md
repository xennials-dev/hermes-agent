# Product Requirements Document (PRD) — Service #13: Browser-Use Web Agent

## 1. Objective
Eliminate repetitive copy-paste operations across legacy vendor, insurance, banking, and logistics web portals that lack APIs—using governed, self-hosted AI browser sandboxes with domain allowlists, audit screenshots, and live human-in-the-loop 2FA handoff.

## 2. Target Users & Use Cases
- **Finance & AP/AR Teams:** Automatically log into vendor portals, pull unpaid invoice tables, and sync line items into ERP/accounting webhooks.
- **Operations & Compliance:** Monitor regulatory, freight, or supplier portals 24/7 via ChangeDetection and trigger Windmill/Browser-Use jobs when status changes.
- **Sales & Competitive Intel:** Crawl public pricing pages and directories into structured JSON via Crawl4AI with zero fragile regex scraping.

## 3. Core Functional Requirements
1. **Isolated Browser Sandboxes:** Run all browser sessions in ephemeral or profile-scoped Docker containers (Browserless `:7100`, Steel `:7120`, Selenium noVNC `:7200/:7201`).
2. **Human-in-the-Loop Governance:** Support `pause-on-2fa`, `read-only-extract`, and `approval-before-submit` safety gates—never bypassing auth controls or CAPTCHAs.
3. **Zero-Docker Playbook Compiler:** Ship a live RPA Playbook & Python Script Compiler (`POST /api/rpa/compile-playbook`) right inside the Hub.
