---
name: audit-report
description: Generate a client-ready AI Audit & ROI Action Report with...
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
    - ReportGeneration
    - ClientDeliverable
    - ROICalculation
    - EffortImpactMatrix
    related_skills:
    - ai-audit
    - audit-analyze
    - audit-review
    - ai-concierge
---

# Audit Report Generator

## Trigger Conditions
Use this skill when:
- Compiling findings from `audit-analyze` into a polished client deliverable
- Generating executive summary, financial projections, and 4-day quick start roadmaps
- Exporting Markdown, HTML, or presentation-ready copy (for Gamma.app / Claude Design)

---

## 1. Report Template Structure

1. **Title & Context**: Client name, business type, assessment date.
2. **Executive Summary**:
   - Primary operational bottlenecks
   - Estimated reclaimed hours/week (Target: 5–10 hours)
   - Monthly net financial value created
3. **Effort vs. Impact Matrix**:
   - *Top-Left (Quick Wins)*: Immediate self-implementation
   - *Top-Right (Major Projects)*: High-value opportunities for consulting implementation
4. **Tool Recommendations**:
   - Tool Name, Cost ($/mo), Setup Time, Hours Saved/week, Net ROI
5. **4-Day Quick Start Plan**:
   - Day 1: Account setup & initial config (5 min)
   - Day 2: First workflow connection (10 min)
   - Day 3: Team testing & verification (10 min)
   - Day 4: Live rollout (5 min)
6. **Financial Impact Formula**:
   $$\text{Monthly Net ROI} = (\text{Weekly Hours Saved} \times 4 \times \text{Hourly Rate}) - \text{Monthly Tool Cost}$$
7. **Next Steps & Upsell Tee-Up**:
   - Review call booking & roadmap preview for Major Projects

---

## 2. Automated Script Execution

Run the built-in report engine:
```bash
python skills/business/audit-report/scripts/generate_report.py --client "Client Name" --rate 75 --output report.md
```
