---
name: ai-audit
description: "Conduct 45-minute AI assessment discovery calls with clients."
version: 1.0.0
author: Terrance (tee), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Consulting, Assessment, Discovery, Audit, Business]
    related_skills: [audit-analyze, find-clients]
---

# AI Assessment Discovery Call

## Trigger Conditions
Use this skill when the user wants to:
- Start a new client assessment
- Conduct a discovery call with a business owner
- Identify AI opportunities for a client
- Begin the 4-phase audit process

## Instructions

### Phase 1: Discovery Call Structure

1. **Schedule the call** – 45 minutes via Zoom/Google Meet
2. **Enable AI note‑taker** – Use Fathom, Otter, or Fireflies.ai
3. **Ask probing questions** (DO NOT prescribe tools yet):

   **Core Questions:**
   - "Walk me through your day yesterday. What does a typical business day look like?"
   - "What tasks in your business do you dread doing?"
   - "Where does your work pile up?"
   - "What have you tried to automate in the past that failed?"
   - "If you could wave a magic wand and delete any process, what would it be?"

4. **Record the call** – Ensure the AI note‑taker captures the full transcript
5. **End with** – "I'll analyze everything and send you a report with recommendations"

### Key Principle
**First call is ONLY for probing.** Bite your tongue. Don't prescribe tools yet, even if you know the answer immediately.

### Client Profile
- Small business owners: 2–20 employees
- Revenue: $500K–$5M/year
- Industries: Any (landscaping, real estate, e‑commerce, professional services)

### Success Metric
Identify at least 3–7 pain points that can be solved with off‑the‑shelf AI tools.

## Follow‑up
After the call, run the `audit-analyze` skill on the transcript.
