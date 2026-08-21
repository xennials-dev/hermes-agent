---
name: audit-analyze
description: "Analyze discovery transcripts and recommend high-ROI AI tools."
version: 1.0.0
author: Terrance (tee), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Analysis, Transcript, Tools, SaaS, Consulting, ROI]
    related_skills: [ai-audit, audit-report]
---

# Audit Transcript Analysis

## Trigger Conditions
Use this skill when the user says "analyze transcript", "find tools", or
after completing a discovery call.

## Instructions

### Phase 2: AI Analysis

1. **Obtain the transcript** – From Fathom, Otter, or Fireflies.ai

2. **Feed the transcript to AI** with this prompt:
   ```text
   I just had a call with a business owner. Attached is the transcript.

   Please:
   1. Extract all pain points and bottlenecks mentioned
   2. Research off-the-shelf SaaS or AI tools that fix each pain point
   3. For each tool, include: name, cost, setup time, and estimated time saved
   4. Prioritize tools that are HIGH IMPACT + LOW EFFORT (quick wins)

   Transcript: [PASTE TRANSCRIPT HERE]
   ```

3. **Quality Assurance** – Review the AI's recommendations:
   - Is the tool appropriate for a small business? (e.g., don't recommend Salesforce to a 4‑person landscaping company)
   - Substitute tools when needed

4. **Tool Research Resources**:
   - `futurepedia.io` – AI tool directory
   - `thereisanai.com` – Search by industry

5. **Categorize by ROI levers**:
   - **Effectiveness** – Makes more money
   - **Efficiency** – Saves time
   - **Quality** – Improves product/service

### Output Format
A list of 3–7 recommended tools with:
- Pain point addressed
- Tool name
- Monthly cost
- Setup time
- Weekly hours saved

## Quality Checklist
- [ ] Tools are off‑the‑shelf (no custom coding required)
- [ ] Each tool addresses a specific pain point from the transcript
- [ ] Tool complexity matches client's technical ability
- [ ] Total monthly tool cost is reasonable (<$100/month typical)

## Follow‑up
After analysis, run the `audit-report` skill to generate the client deliverable.
