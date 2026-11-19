# Product Requirements Document (PRD) — Social Media Closer

**Service ID:** `TS101-SRV-02`  
**Product Name:** Techstarz101 Social Media Closer (Auto-Posts & 24/7 DM Sales Replies)  
**Status:** Production Ready  
**Localhost Hub:** `http://localhost:7866`  
**Live Catalog Reference:** `https://techstarz101.com/agents/social-media-manager`

---

## 1. Executive Summary & Problem Statement

Growth teams and agencies pay $300–$1,200/month across disconnected SaaS tools (Buffer/Hootsuite + ManyChat + Intercom + Zapier + HubSpot) just to publish posts and answer incoming DMs. Worse:
1. **Missed After-Hours Leads:** 68% of social DMs arrive outside business hours; prospects cool off within 15 minutes if nobody replies.
2. **Monolithic Vendor Lock-In:** Teams cannot swap out individual components (e.g., changing CRM or scheduler) without breaking their entire funnel.
3. **Contact & Seat Taxes:** Legacy tools charge per channel, per agent seat, and per contact stored.

The **Techstarz101 Social Media Closer** solves this with a **modular, standalone-repo architecture**: every tool in Stack A and Stack B runs as its own isolated Docker Compose application with its own dedicated clickable launch link (`/t/<tool>`), while also supporting one-click stacking and automated DM-to-CRM closing pipelines.

---

## 2. Core Functional Requirements

### 2.1. Individual Standalone Tool Repos
- Every tool (`postiz`, `chatwoot`, `n8n`, `ollama-webui`, `twenty`, `mixpost`, `flowise`, `activepieces`, `espocrm`) lives in its own self-contained folder under `tools/<id>/` with its own `docker-compose.yml`, `.env.example`, `README.md`, database, and localhost port.
- Clicking any tool's repo icon or dedicated link (`http://localhost:7866/t/<id>`) automatically starts its containers (if stopped), displays live boot logs, and redirects straight into the working web app.

### 2.2. Composable Stacking & Automation
- Operators can select any subset of tools (or full Stack A / Stack B) from the Hub UI to run together.
- Pre-built webhook endpoints (`/api/closer/chatwoot-webhook`, `/api/closer/generic-webhook`) and importable workflow JSONs (`automations/stack_a_dm_closer.n8n.json`, `automations/stack_b_flowise_closer.json`) chain inbound DMs → intent classification → local LLM/Flowise reply → CRM lead creation.

### 2.3. 24/7 DM Sales Reply SLA
- **Response Latency:** < 5 seconds via local Ollama (`llama3.2:3b`) or Flowise agent, with deterministic instant template fallback if no local LLM is booted.
- **Intent Classification:** Automatically tags `ready_to_buy`, `pricing`, `demo_request`, `objection`, `support`, and `general_inquiry`.
- **Guardrails:** Never fabricates prices; strictly anchors the $390 starter sprint, $1,480 full build, and $490/mo retainer with direct booking link injection.
