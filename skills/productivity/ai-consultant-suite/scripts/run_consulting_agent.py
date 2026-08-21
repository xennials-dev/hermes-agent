#!/usr/bin/env python3
"""
Autonomous AI Consulting & Audit Agent for Hermes.

Orchestrates the full 4-phase AI consulting lifecycle:
1. Ingestion of client transcript or discovery notes
2. Bottleneck & pain point extraction
3. AI/SaaS tool matching with Effort vs Impact matrix
4. Automated client deliverable report generation
5. Customized upsell proposal & closing strategy generation
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


# Curated database of off-the-shelf, high-ROI AI tools
TOOL_KNOWLEDGE_BASE = [
    {
        "keywords": ["meeting", "notes", "summary", "call", "transcript", "zoom", "client call"],
        "name": "Fathom / Fireflies.ai",
        "category": "Meeting Intelligence",
        "cost_monthly": 19,
        "setup_time_mins": 10,
        "hours_saved_weekly": 4.0,
        "impact": "high",
        "effort": "low",
        "benefit": "Automatically records, transcribes, and summarizes client meetings with action items synced to CRM.",
    },
    {
        "keywords": ["email", "inbox", "repetitive", "questions", "faqs", "drafting", "customer support"],
        "name": "Custom GPT / Claude Knowledge Hub",
        "category": "Customer & Team Knowledge Base",
        "cost_monthly": 20,
        "setup_time_mins": 30,
        "hours_saved_weekly": 8.0,
        "impact": "high",
        "effort": "low",
        "benefit": "Instantly answers repetitive client inquiries from uploaded documents and drafts email responses.",
    },
    {
        "keywords": ["invoice", "receipt", "billing", "bookkeeping", "expenses", "accounting", "friday"],
        "name": "Dext / QuickBooks AI Invoicing",
        "category": "Financial Automation",
        "cost_monthly": 25,
        "setup_time_mins": 20,
        "hours_saved_weekly": 3.5,
        "impact": "high",
        "effort": "low",
        "benefit": "Automates receipt capture, expense categorization, and recurring client invoice generation.",
    },
    {
        "keywords": ["lead", "intake", "form", "qualification", "booking", "scheduling", "calendar"],
        "name": "Fillout AI + Cal.com",
        "category": "Lead Intake & Scheduling",
        "cost_monthly": 15,
        "setup_time_mins": 15,
        "hours_saved_weekly": 3.0,
        "impact": "high",
        "effort": "low",
        "benefit": "Dynamic smart forms that qualify leads and book directly into your calendar without back-and-forth emails.",
    },
    {
        "keywords": ["social", "content", "marketing", "post", "newsletter", "copywriting"],
        "name": "Claude Projects / Copy.ai",
        "category": "Marketing Content Repurposing",
        "cost_monthly": 20,
        "setup_time_mins": 15,
        "hours_saved_weekly": 4.5,
        "impact": "medium",
        "effort": "low",
        "benefit": "Repurposes project updates, customer wins, and photos into polished newsletters and social updates in seconds.",
    },
    {
        "keywords": ["process", "workflow", "copy-paste", "manual", "sync", "data entry", "spreadsheet"],
        "name": "Make.com / Zapier Smart Workflows",
        "category": "Process Automation",
        "cost_monthly": 29,
        "setup_time_mins": 45,
        "hours_saved_weekly": 6.0,
        "impact": "high",
        "effort": "medium",
        "benefit": "Connects existing tools so data flows automatically without manual copy-pasting between spreadsheets.",
    },
]


class ConsultingAgent:
    """Autonomous engine for client assessment, ROI modeling, and report drafting."""

    def __init__(
        self,
        client_name: str,
        industry: str,
        employees: int = 5,
        hourly_rate: float = 85.0,
        output_dir: str = "./client_deliverables",
    ):
        self.client_name = client_name
        self.industry = industry
        self.employees = employees
        self.hourly_rate = hourly_rate
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def analyze_pain_points(self, text: str) -> List[Dict[str, Any]]:
        """Identify matched bottlenecks and recommend tools from the knowledge base."""
        matched_tools = []
        text_lower = text.lower()

        for tool in TOOL_KNOWLEDGE_BASE:
            matched_keywords = [kw for kw in tool["keywords"] if kw in text_lower]
            if matched_keywords:
                matched_tools.append({**tool, "matched_reasons": matched_keywords})

        # Fallback if text is generic
        if not matched_tools:
            matched_tools = TOOL_KNOWLEDGE_BASE[:3]

        return matched_tools

    def calculate_financial_roi(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compute weekly time saved, monthly value, total tool cost, and net ROI."""
        total_weekly_hours = sum(t["hours_saved_weekly"] for t in recommendations)
        total_monthly_tool_cost = sum(t["cost_monthly"] for t in recommendations)

        monthly_hours_saved = total_weekly_hours * 4.2
        gross_monthly_value = monthly_hours_saved * self.hourly_rate
        net_monthly_roi = gross_monthly_value - total_monthly_tool_cost
        roi_percentage = ((gross_monthly_value - total_monthly_tool_cost) / max(total_monthly_tool_cost, 1)) * 100

        return {
            "total_weekly_hours": round(total_weekly_hours, 1),
            "monthly_hours_saved": round(monthly_hours_saved, 1),
            "total_monthly_tool_cost": round(total_monthly_tool_cost, 2),
            "gross_monthly_value": round(gross_monthly_value, 2),
            "net_monthly_roi": round(net_monthly_roi, 2),
            "roi_percentage": round(roi_percentage, 0),
        }

    def generate_client_report(
        self, recommendations: List[Dict[str, Any]], roi: Dict[str, Any]
    ) -> Path:
        """Generate the complete, executive client deliverable report."""
        date_str = datetime.datetime.now().strftime("%B %d, %Y")
        clean_name = re.sub(r"[^\w\s-]", "", self.client_name).strip().replace(" ", "_")
        report_file = self.output_dir / f"{clean_name}_AI_Audit_Report.md"

        quick_wins = [t for t in recommendations if t["impact"] == "high" and t["effort"] == "low"]
        major_projects = [t for t in recommendations if t not in quick_wins]
        if not major_projects:
            major_projects = recommendations[-1:]

        content = f"""# AI Opportunity & Efficiency Assessment
**Prepared for:** {self.client_name}
**Industry:** {self.industry} ({self.employees} Team Members)
**Date:** {date_str}

---

## 1. Executive Summary

Based on our discovery assessment, {self.client_name} has significant potential to eliminate manual friction, reduce administrative burden, and accelerate customer response times using off-the-shelf AI tooling.

- **Total Reclaimable Time:** **{roi['total_weekly_hours']} hours / week** (~{roi['monthly_hours_saved']} hours / month)
- **Gross Monthly Value Returned:** **${roi['gross_monthly_value']:,.2f}** (calculated at ${self.hourly_rate:.0f}/hr valuation)
- **Monthly Tool Investment:** **${roi['total_monthly_tool_cost']:,.2f}**
- **Net Monthly ROI:** **${roi['net_monthly_roi']:,.2f} / month** ({roi['roi_percentage']:.0f}% Return on Investment)

---

## 2. Effort vs. Impact Matrix

| Quadrant | Focus & Opportunity | Recommended Action |
|---|---|---|
| **Quick Wins** *(High Impact, Low Effort)* | {', '.join(t['name'] for t in quick_wins)} | **Implement Immediately (Days 1–4)** |
| **Major Projects** *(High Impact, Higher Effort)* | Custom Knowledge Bases, Cross-App Sync | **Phase 2 Implementation / Managed Support** |

---

## 3. Recommended Quick-Win Solutions

"""
        for i, tool in enumerate(recommendations, 1):
            content += f"""### Solution {i}: {tool['name']}
- **Primary Benefit:** {tool['benefit']}
- **Monthly Cost:** ${tool['cost_monthly']}/month
- **Setup Time:** ~{tool['setup_time_mins']} minutes
- **Estimated Time Reclaimed:** **{tool['hours_saved_weekly']} hrs/week**
- **Implementation Category:** {tool['category']}

"""

        content += f"""---

## 4. 4-Day Quick Start Implementation Plan

| Day | Focus Area | Action Item | Est. Time |
|---|---|---|---|
| **Day 1** | Foundation Setup | Create tool accounts and connect core integrations | 15 mins |
| **Day 2** | Prompt & Template Config | Upload business context and configure default templates | 20 mins |
| **Day 3** | Live Test Run | Run 3 real client scenarios and refine output formatting | 25 mins |
| **Day 4** | Team Handover | Review quick guide with team and deploy to daily workflow | 15 mins |

---

## 5. Financial ROI Breakdown

```
  Weekly Time Returned:        {roi['total_weekly_hours']} Hours
× Internal Hourly Valuation:  ${self.hourly_rate:.2f} / Hour
────────────────────────────────────────────────────
= Weekly Value Reclaimed:     ${roi['total_weekly_hours'] * self.hourly_rate:,.2f}
= Gross Monthly Value:        ${roi['gross_monthly_value']:,.2f}
- Estimated Software Cost:   -${roi['total_monthly_tool_cost']:,.2f}
────────────────────────────────────────────────────
= Net Monthly Economic ROI:   ${roi['net_monthly_roi']:,.2f} / month
```

---

## 6. Next Steps

1. Review this document with key stakeholders.
2. Schedule our 30-minute review call to finalize questions.
3. Select whether to self-implement via the 4-Day Plan or partner for full turnkey execution.
"""
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(content)

        return report_file

    def generate_upsell_strategy(
        self, recommendations: List[Dict[str, Any]], roi: Dict[str, Any]
    ) -> Path:
        """Generate the consultant's strategic playbook for the review call."""
        clean_name = re.sub(r"[^\w\s-]", "", self.client_name).strip().replace(" ", "_")
        strategy_file = self.output_dir / f"{clean_name}_Upsell_Strategy.md"

        content = f"""# Consultant Dossier & Upsell Playbook
**Client:** {self.client_name} | **Target Rate:** ${self.hourly_rate}/hr

---

## 1. The 3 Review Call Closing Questions

1. *"Of the recommendations in this report, which one would give you and your team the biggest sigh of relief if it were solved by next week?"*
2. *"Do you prefer to have your team follow the 4-day plan to set this up internally, or would you like me to handle the implementation turnkey?"*
3. *"What is your timeline? Is eliminating this {roi['total_weekly_hours']} hours/week friction urgent, or can it wait 60 days?"*

---

## 2. Qualified Upsell Offerings

### Tier A: Turnkey Implementation & Knowledge System ($3,500 – $5,000)
- **When to Pitch:** If client mentions email overload, repetitive Q&A, or lack of internal tech bandwidth.
- **The Pitch:**
  > *"We can credit your $999 assessment fee directly toward the implementation. We will build, test, and deploy the entire system and train your staff in a 30-minute workshop."*

### Tier B: AI Concierge Retainer ($1,500 / month)
- **When to Pitch:** If client wants ongoing AI coaching, regular skill building, and direct advisory.
- **The Pitch:**
  > *"Instead of a one-off build, I can act as your in-house AI Concierge. We do two 45-minute working sessions a month where we optimize workflows, plus you get direct async access for any AI questions."*

---

## 3. Pre-Call Checklist
- [ ] Email report to client 2 hours before the call.
- [ ] Have tool demo tabs or sample output ready to share.
- [ ] Open proposal agreement template.
"""
        with open(strategy_file, "w", encoding="utf-8") as f:
            f.write(content)

        return strategy_file

    def run(self, input_text: str) -> Dict[str, Any]:
        """Execute the entire autonomous consulting workflow."""
        recommendations = self.analyze_pain_points(input_text)
        roi = self.calculate_financial_roi(recommendations)
        report_path = self.generate_client_report(recommendations, roi)
        strategy_path = self.generate_upsell_strategy(recommendations, roi)

        return {
            "client": self.client_name,
            "report_path": str(report_path),
            "strategy_path": str(strategy_path),
            "weekly_hours_saved": roi["total_weekly_hours"],
            "net_monthly_roi": roi["net_monthly_roi"],
            "recommendations_count": len(recommendations),
        }


def main():
    parser = argparse.ArgumentParser(description="Autonomous AI Consultant Agent")
    parser.add_argument("--client", required=True, help="Client or Business Name")
    parser.add_argument("--industry", default="General Business", help="Business Industry")
    parser.add_argument("--employees", type=int, default=5, help="Number of team members")
    parser.add_argument("--hourly-rate", type=float, default=85.0, help="Estimated hourly value of owner/staff time")
    parser.add_argument("--transcript", help="Path to transcript text file")
    parser.add_argument("--notes", help="Inline discovery notes / pain points")
    parser.add_argument("--output-dir", default="./client_deliverables", help="Output directory for reports")

    args = parser.parse_args()

    input_text = ""
    if args.transcript and os.path.exists(args.transcript):
        with open(args.transcript, "r", encoding="utf-8", errors="ignore") as f:
            input_text = f.read()
    elif args.notes:
        input_text = args.notes
    else:
        input_text = "General operational friction, email overload, repetitive meeting notes, manual data entry and invoicing."

    agent = ConsultingAgent(
        client_name=args.client,
        industry=args.industry,
        employees=args.employees,
        hourly_rate=args.hourly_rate,
        output_dir=args.output_dir,
    )

    result = agent.run(input_text)

    print("\n" + "=" * 60)
    print(f"  Autonomous AI Audit Complete for: {result['client']}")
    print("=" * 60)
    print(f"  • Weekly Time Reclaimed: {result['weekly_hours_saved']} hours")
    print(f"  • Net Monthly ROI:       ${result['net_monthly_roi']:,.2f} / month")
    print(f"  • Client Report:         {result['report_path']}")
    print(f"  • Upsell Strategy:       {result['strategy_path']}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
