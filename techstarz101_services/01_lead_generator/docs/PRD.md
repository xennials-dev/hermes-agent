# Product Requirements Document (PRD) — Lead Generator (<60s)

**Service ID:** `TS101-SRV-01`  
**Product Name:** Techstarz101 Autonomous Lead Generator & Auto-Booker  
**Status:** Production Ready  
**SLA Target:** <60 Seconds Generation & Enrichment for 250+ ICP Prospects  
**Live Catalog Reference:** `https://techstarz101.com/agents/lead-generator`

---

## 1. Executive Summary & Problem Statement

Modern B2B revenue teams waste $2,000–$5,000/month per seat on fragmented legacy data platforms (Apollo, ZoomInfo, SalesIntel, Clearbit) and suffer from:
1. **Severe Per-Seat Tax:** Paying punitive recurring costs per rep, regardless of pipeline velocity.
2. **Stale Contact Decay:** Average B2B contact data degrades at ~30% per year; scraped databases deliver high bounce rates (>15%).
3. **Manual SDR Bottlenecks:** Reps spend 3–4 hours daily manually copying names, researching company websites, drafting personalized hooks, and chasing calendar booking links.

The **Techstarz101 Autonomous Lead Generator** eliminates these bottlenecks by running a sovereign, automated pipeline that scrapes real-time web sources, enriches company decision-makers with verified emails/phones, generates hyper-personalized pitch hooks, syncs directly into an open-source CRM (Twenty CRM), and triggers automated calendar invites (Cal.com) in **under 60 seconds for 250+ prospects**.

---

## 2. Core Value Propositions & Benchmarks

| Metric | Legacy SaaS (Apollo / ZoomInfo) | Techstarz101 Autonomous Lead Generator |
| :--- | :--- | :--- |
| **Batch Turnaround** | 15–45 minutes manual filtering & exporting | **< 60 seconds for 250+ enriched prospects** |
| **Recurring Cost** | $99–$499/seat/month + contact credit add-ons | **$0 monthly licensing (100% Open Source / Self-Hosted)** |
| **Data Recency** | Static database snapshot (often 3–6 months old) | **Live real-time crawl & verification at point of execution** |
| **Personalization** | Generic merge fields (`{first_name}`, `{company}`) | **LLM semantic reasoning on live website metadata & news** |
| **Calendar Dispatch** | Manual SDR email back-and-forth | **Automated Cal.com meeting booking & CRM stage routing** |

---

## 3. User Personas & Flows

### Primary Persona: Agency Founder / Head of Growth
- **Objective:** Wants 250 targeted, local or niche B2B decision-makers ready for outbound outreach every morning.
- **Pain Point:** Cannot justify enterprise data contracts with slow onboarding cycles.
- **Desired Flow:**
  ```mermaid
  flowchart LR
    A[Define ICP: Niche, Geo, Revenue] --> B[Execute Generator via Web UI or CLI]
    B --> C[<60s Pipeline: Crawl + Enrich + Verify]
    C --> D[Review 250+ Table in Twenty CRM]
    D --> E[Auto-Book Cal.com Link Dispatched]
  ```

---

## 4. Functional Specifications

### 4.1. Input Specification (ICP Definition)
The system accepts structured or conversational ICP inputs:
- **Target Vertical/Industry:** (e.g., HVAC contractors, B2B SaaS, manufacturing, dental practices)
- **Target Geography:** Metro area, state, country, or radius (e.g., "St. Louis, MO, 50-mile radius")
- **Company Size / Employee Bands:** (1–10, 11–50, 51–200, 201–500)
- **Decision-Maker Titles:** (CEO, Founder, CMO, VP Sales, Owner, Managing Partner)
- **Desired Batch Size:** Default 250 prospects (configurable 50–1,000)

### 4.2. Ingestion & Extraction Engine (<25s)
- Parallel multi-threaded headless crawler querying verified business directories, Google Maps, Bing Places, YellowPages, chamber of commerce listings, and LinkedIn company directories.
- Domain extraction, SSL validation, and root website parsing.

### 4.3. Enrichment & LLM Verification Engine (<25s)
- **DNS / MX Verification:** Check SPF/DKIM/DMARC records and test SMTP handshake (`HELO/RCPT TO`) without sending payload to verify email deliverability.
- **Executive Identification:** Extract name, verified title, direct phone number, and LinkedIn profile.
- **Semantic Value Proposition Extractor:** Local or cloud LLM analyzes homepage and 'About Us' copy to synthesize a 1-sentence hook ("*Noticed you scale manufacturing ABM across the Midwest...*").

### 4.4. Storage, CRM Sync & Auto-Booking (<10s)
- **Database Write:** Write enriched batch to PostgreSQL / Twenty CRM custom `Person` and `Company` records.
- **Export Formats:** Live CSV, Excel (.xlsx), and JSON payload.
- **Auto-Booking Dispatch:** Generates individualized Cal.com booking slugs with pre-filled lead context (`https://cal.com/techstarz101/audit?name={name}&email={email}`).

---

## 5. Non-Functional Requirements & SLAs

- **Latency:** End-to-end execution for 250 leads must complete in $\le 60$ seconds using a 16-worker thread pool.
- **Email Deliverability Guarantee:** Bounces must not exceed $3.0\%$ across verified batches.
- **Sovereign Privacy:** Zero outbound telemetry; contact data remains within the user's private database / VPS.
- **Availability:** 99.9% uptime for the dockerized microservice stack.
