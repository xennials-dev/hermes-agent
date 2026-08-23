#!/usr/bin/env python3
"""
Hermes AI Consulting - Client Audit & Action Report Generator
Generates structured Markdown & HTML client deliverables with financial ROI calculations.
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

def generate_report(
    client_name: str,
    business_type: str,
    hourly_rate: float,
    quick_wins: list,
    major_projects: list
) -> str:
    total_hours_saved = sum(item.get("hours_saved", 0) for item in quick_wins)
    total_tool_cost = sum(item.get("monthly_cost", 0) for item in quick_wins)
    gross_monthly_value = total_hours_saved * 4 * hourly_rate
    net_monthly_roi = gross_monthly_value - total_tool_cost
    annual_net_roi = net_monthly_roi * 12

    date_str = datetime.now().strftime("%B %d, %Y")

    report_md = f"""# AI Opportunity Assessment & Action Plan
**Client:** {client_name}  
**Industry / Business Type:** {business_type}  
**Date:** {date_str}  
**Prepared by:** Hermes AI Consulting Services  

---

## 1. Executive Summary
During our discovery audit, we identified **{len(quick_wins)} immediate quick wins** and **{len(major_projects)} high-impact transformation projects**.

By executing the quick wins outlined below:
- **Time Returned:** **{total_hours_saved:.1f} hours / week** (~{total_hours_saved * 4:.1f} hours/month)
- **Monthly Value Generated:** **${gross_monthly_value:,.2f}** (calculated at ${hourly_rate:.2f}/hr)
- **Estimated Tool Investment:** **${total_tool_cost:,.2f}/month**
- **Net Monthly ROI:** **${net_monthly_roi:,.2f}/month** (${annual_net_roi:,.2f}/year)

---

## 2. Effort vs. Impact Matrix

```
HIGH IMPACT
   ▲
   │  [ QUICK WINS ]                │  [ MAJOR PROJECTS / UPSELL ]
   │  • Immediate Self-Rollout      │  • Process Redesign (AOA)
   │  • High ROI, Low Setup Time    │  • Custom Knowledge Systems
   │  • 4-Day Execution Plan        │  • Hermes Retainer / Concierge
   │                                │
───┼────────────────────────────────┼─────────────────────────────────►
   │  [ LOW PRIORITY ]              │  [ COMPLEX / LOW YIELD ]
   │  • Minor adjustments           │  • Heavy bespoke builds
   │  • Postpone for now            │  • Deprioritized
   │
 LOW EFFORT ◄─────────────────────────────────────────────► HIGH EFFORT
```

---

## 3. Recommended Quick-Win Solutions

| Pain Point Addressed | Tool Recommendation | Setup Time | Monthly Cost | Weekly Hours Saved |
| :--- | :--- | :--- | :--- | :--- |
"""

    for item in quick_wins:
        report_md += f"| **{item['pain']}** | {item['tool']} | {item['setup_time']} | ${item['monthly_cost']:.2f} | {item['hours_saved']:.1f} hrs |\n"

    report_md += """
---

## 4. Four-Day Quick Start Roadmap

| Day | Action Step | Estimated Commitment |
| :--- | :--- | :--- |
| **Day 1** | Provision tool accounts & verify credentials | 10 Minutes |
| **Day 2** | Configure initial prompt templates / webhook connection | 15 Minutes |
| **Day 3** | Test workflow on 3 sample customer inquiries/tasks | 15 Minutes |
| **Day 4** | Deploy live to daily operations & monitor first results | 10 Minutes |

---

## 5. Strategic Transformation Projects (Phase 2)

These high-leverage initiatives represent major time-saving and revenue-expansion opportunities:

"""
    for proj in major_projects:
        report_md += f"- **{proj['name']}**: {proj['description']} *(Estimated Impact: {proj['impact']})*\n"

    report_md += f"""
---

## 6. Next Steps & Review Call
1. Review the Quick-Win recommendations and confirm tool selection.
2. Schedule our **30-minute Review Call** to discuss self-implementation vs. managed implementation.
3. *Note:* If you decide to proceed with our Managed Implementation or AI Concierge Retainer, 100% of your assessment investment will be credited toward the package.
"""
    return report_md

def main():
    parser = argparse.ArgumentParser(description="Hermes AI Consulting Audit Report Generator")
    parser.add_argument("--client", type=str, default="Sample Client", help="Client business name")
    parser.add_argument("--business", type=str, default="Service Business", help="Business niche")
    parser.add_argument("--rate", type=float, default=75.0, help="Client effective hourly rate")
    parser.add_argument("--output", type=str, default="audit_report.md", help="Output file path")
    args = parser.parse_args()

    sample_quick_wins = [
        {"pain": "Customer FAQ Email Inquiries", "tool": "Hermes Knowledge System / Custom GPT", "setup_time": "30 mins", "monthly_cost": 20.0, "hours_saved": 3.5},
        {"pain": "Manual Meeting Follow-ups", "tool": "Fathom AI / Granola", "setup_time": "10 mins", "monthly_cost": 19.0, "hours_saved": 2.0},
        {"pain": "Invoice Data Re-entry", "tool": "Make.com + OCR Bridge", "setup_time": "45 mins", "monthly_cost": 15.0, "hours_saved": 2.5}
    ]

    sample_major_projects = [
        {"name": "Multi-Channel Knowledge System", "description": "Automate buyer inquiry responses across Telegram, WhatsApp, and Email using Hermes Agent.", "impact": "+15 hrs/week saved"},
        {"name": "End-to-End AOA Process Redesign", "description": "Streamline lead qualification and quoting workflow from 14 manual steps down to 4 automated steps.", "impact": "2x lead speed-to-lead"}
    ]

    content = generate_report(args.client, args.business, args.rate, sample_quick_wins, sample_major_projects)
    Path(args.output).write_text(content, encoding="utf-8")
    print(f"[OK] Audit report successfully generated at: {args.output}")

if __name__ == "__main__":
    main()
