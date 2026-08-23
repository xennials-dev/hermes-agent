---
name: audit-analyze
description: "Analyze a client discovery call transcript to extract pain points, classify ROI levers, and recommend off-the-shelf AI/SaaS tools."
version: 1.0.0
author: Hermes Consulting Suite
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [TranscriptAnalysis, ToolRecommendation, BottleneckExtraction, ROIEvaluation]
    related_skills: [ai-audit, audit-report, audit-review, process-redesign]
---

# Audit Transcript Analysis

## Trigger Conditions
Use this skill when:
- Analyzing a discovery call transcript from Fathom, Otter, Fireflies, or manual notes
- Extracting operational bottlenecks, wasted hours, and repetitive tasks
- Matching pain points to high-ROI, off-the-shelf AI / automation tools

---

## 1. Analysis Protocol

1. **Transcript Ingestion**: Read the client transcript or paste notes.
2. **Pain Point & Bottleneck Extraction**:
   - Extract 3–7 core pain points.
   - Estimate weekly hours wasted per pain point.
   - Classify each by ROI Lever:
     - **Effectiveness**: Generates more revenue or closes more deals.
     - **Efficiency**: Directly cuts labor hours and operational drag.
     - **Quality**: Elevates consistency, speed to response, or customer satisfaction.

3. **Tool Matching Guidelines**:
   - Prioritize **Off-the-shelf SaaS & AI tools** (<$100/mo, fast setup).
   - Match client technical competence (avoid overly complex enterprise tooling for small teams).
   - Reference directories: `futurepedia.io`, `thereisanai.com`, or custom Hermes knowledge bases.

4. **Matrix Categorization**:
   - **Quick Wins** (High Impact, Low Effort): Self-implementation / 4-day quick start.
   - **Major Projects** (High Impact, High Effort): Upsell pipeline (Process Redesign, Knowledge Systems, Concierge).

---

## 2. Analysis Prompt & Structure

```
Client Industry: [e.g., Landscaping, Real Estate, E-Commerce]
Estimated Hourly Rate: $[50 - $150/hr]

For each identified pain point:
- Pain Point: [Detailed bottleneck description]
- Recommended Tool: [Name & URL]
- Estimated Cost: $[X]/mo
- Setup Time: [X] minutes
- Weekly Time Saved: [X] hours
- ROI Category: [Efficiency / Effectiveness / Quality]
- Quadrant: [Quick Win vs. Major Project]
```
