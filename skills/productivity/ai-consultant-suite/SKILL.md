---
name: ai-consultant-suite
description: "Autonomously execute end-to-end AI audits, reports, and upsells."
version: 1.0.0
author: Terrance (tee), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Consulting, AutonomousAgent, AIAudit, Reports, Sales, Upsell, Business]
    related_skills: [ai-audit, audit-analyze, audit-report, audit-review, ai-concierge]
---

# Autonomous AI Consultant Agent

An autonomous agent workflow that orchestrates the entire consulting lifecycle: discovery ingestion, transcript bottleneck analysis, tool ROI matching, client deliverable generation, and custom upsell proposal creation.

---

## 1. Quick Invocation

Run the autonomous consulting agent from terminal or inside Hermes:

```bash
# Run autonomous analysis & generate report from transcript
python skills/productivity/ai-consultant-suite/scripts/run_consulting_agent.py \
  --client "GreenLeaf Landscaping" \
  --industry "Landscaping & Lawn Care" \
  --employees 8 \
  --hourly-rate 75 \
  --transcript "path/to/transcript.txt" \
  --output-dir "./client_deliverables"
```

Or execute directly with an inline transcript / notes:
```bash
python skills/productivity/ai-consultant-suite/scripts/run_consulting_agent.py \
  --client "Apex Business Brokers" \
  --industry "Brokerage & M&A" \
  --hourly-rate 150 \
  --notes "Owner spends 15 hours/week answering 400 buyer emails asking the exact same 5 questions. Invoicing takes 6 hours every Friday."
```

---

## 2. Autonomous Agent Execution Flow

```
[Client Call Transcript / Notes]
                │
                ▼
1. Autonomous Pain Point Extraction
   (Filters Dread Tasks, Bottlenecks, Inefficiencies)
                │
                ▼
2. SaaS & AI Tool Matching Engine
   (High-Impact + Low-Effort Quick Wins)
                │
                ▼
3. Financial ROI & Time Savings Calculation
   (Weekly hours reclaimed, Net Monthly ROI)
                │
                ▼
4. Deliverable Report Generation
   (Executive Summary, Effort-Impact Matrix, 4-Day Plan)
                │
                ▼
5. Upsell Proposal & Pitch Generator
   (Knowledge Systems, Process Redesign, AI Concierge Retainer)
```

---

## 3. Autonomous Deliverables Generated

1. **Client Deliverable (`<client>_AI_Audit_Report.md`)**:
   - Executive Summary
   - Effort vs. Impact 2x2 Matrix
   - Quick-Win SaaS & AI Tool Recommendations
   - Step-by-Step 4-Day Implementation Plan
   - Transparent Financial ROI Breakdown
2. **Consultant Playbook & Upsell Dossier (`<client>_Upsell_Strategy.md`)**:
   - 3 Key Review Call Closing Questions
   - Custom-tailored pitch for Knowledge System ($3K–$5K), Process Redesign ($3.5K), or AI Concierge Retainer ($1,500/mo)
   - Fee-crediting strategy
