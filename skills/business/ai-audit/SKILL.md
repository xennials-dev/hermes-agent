---
name: ai-audit
description: Conduct a 45-minute AI assessment discovery call with a s...
version: 1.0.0
author: Hermes Consulting Suite
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - AIConsulting
    - DiscoveryCall
    - Audit
    - SmallBusiness
    - AOA
    related_skills:
    - audit-analyze
    - audit-report
    - audit-review
    - process-redesign
    - ai-concierge
---

# AI Assessment Discovery Call (Corey Ganim Method)

## Trigger Conditions
Use this skill when:
- Starting a new client assessment or discovery call
- Prepping a call with a small business owner (2–20 employees, $500K–$5M revenue)
- Identifying operational bottlenecks and automation opportunities
- Initiating the 4-phase AI Audit & Consulting workflow

---

## 1. Discovery Call Structure (45 Minutes)

1. **Setup & Tooling**:
   - Platform: Zoom or Google Meet
   - AI Note-taker: Fathom, Otter.ai, or Fireflies.ai enabled to record transcript

2. **Core Discovery Questions (Bite Your Tongue & Listen)**:
   *Do NOT prescribe tools during this call. Focus 100% on uncovering pain points.*
   - *"Walk me through your day yesterday from start to finish. What does a typical day look like?"*
   - *"What tasks in your business do you or your staff dread doing?"*
   - *"Where does work consistently pile up or get delayed?"*
   - *"What repetitive communications (emails, customer Q&A, quotes) take up the most time?"*
   - *"What software or automations have you tried in the past that failed or felt too complicated?"*
   - *"If you had a magic wand and could delete 2 operational processes tomorrow, what would they be?"*

3. **Wrap-up & Commitment**:
   - Close with: *"I'm going to take this transcript, run an in-depth audit against our tool database, and deliver a prioritized 1-page Action Report with exact ROI numbers and a 4-day quickstart plan for our review call."*

---

## 2. Next Step Execution
Immediately after the call, run `audit-analyze` on the recorded transcript:
```bash
hermes chat --toolsets "skills,terminal" -q "Analyze transcript for [Client Name] using audit-analyze"
```
