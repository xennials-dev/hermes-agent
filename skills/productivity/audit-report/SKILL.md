---
name: audit-report
description: "Generate professional client AI assessment & ROI reports."
version: 1.0.0
author: Terrance (tee), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Report, Assessment, Deliverable, Consulting, ROI]
    related_skills: [audit-analyze, audit-review]
---

# Audit Report Generation

## Trigger Conditions
Use this skill when the user says "generate report", "create deliverable",
or after completing the analysis phase.

## Instructions

### Phase 3: The Report Deliverable

Build the report using this template structure:

---

## Report Template

### 1. Title
- Client Name
- Date
- Business Type
- Primary Focus

### 2. Executive Summary
- Main 1‑2 pain points
- Primary outcome expected
- Hours reclaimable per week (minimum 5, average 7)
- Primary focus: [Effectiveness / Efficiency / Quality]

### 3. Effort vs Impact Matrix
- **Quick Wins** (Top‑Left): High Impact + Low Effort ← FOCUS HERE
- **Major Projects** (Top‑Right): High Impact + High Effort ← Upsell opportunities

### 4. Quick Wins Summary
| Pain Point | Tool | Weekly Hours Saved |
|------------|------|---------------------|
| [Pain 1]   | [Tool 1] | [X hrs] |
| [Pain 2]   | [Tool 2] | [X hrs] |

### 5. Recommended Solutions (Deep Dive)
For EACH tool:
- **Tool Name**: [Name]
- **Pain Point Solved**: [Description]
- **Cost**: $X/month
- **Setup Time**: X minutes
- **Time Saved**: X hours/week

### 6. 4‑Day Quick Start Plan
| Day | Action | Time Required |
|-----|--------|---------------|
| 1 | [Simple setup step] | 5 min |
| 2 | [Next step] | 10 min |
| 3 | [Next step] | 10 min |
| 4 | [Final step] | 5 min |

### 7. Financial Impact & ROI
- Weekly time returned: [X] hours
- Hourly rate: $[X]
- Monthly value: $[X × 4 × hourly_rate]
- Monthly tool cost: ~$60
- **Monthly Net ROI**: $[value - cost]

### 8. What Comes After Quick Wins (Upsell Pathway)
- List major projects from the matrix
- "These are larger initiatives we can help implement"

### 9. Next Steps
- Implement the 4‑day quick start plan
- Book your review call

---

## Design & Formatting Notes
- Keep it concise, high-contrast, and action-oriented.
- Make ROI transparent with clear monetary and time metrics.

## Follow‑up
After the report is generated, run the `audit-review` skill.
