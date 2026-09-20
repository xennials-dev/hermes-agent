---
name: odoo-crm-automation
description: Automate Odoo CRM pipelines, manage leads, update stages...
tags:
- business
- crm
- sales
- leads
- odoo
platforms:
- linux
- macos
- windows
---

# Odoo CRM & Sales Pipeline Automation Skill

This skill guides Hermes Agent in querying, creating, and automating customer deal lifecycles within the **Odoo Enterprise CRM** ecosystem.

---

## 🎯 When to Use
- User asks to inspect active sales opportunities, high-value deals, or win probabilities.
- User requests logging customer inquiries or creating new leads from incoming messages (WhatsApp, WeChat, Slack, Telegram).
- User wants to update a lead's stage (`new` -> `qualified` -> `proposition` -> `won`).
- User asks for deal analysis, risk assessment, or personalized follow-up email drafts.

---

## 🛠️ Available CRM Tool Actions

Use the `crm_manage` tool to perform operations:

### 1. List / Filter Pipeline Leads
```json
{
  "action": "list",
  "stage": "qualified"
}
```

### 2. Create a New Deal / Opportunity
```json
{
  "action": "create",
  "name": "Cloud Infrastructure Expansion",
  "partner_name": "Acme Corp",
  "email": "cto@acmecorp.com",
  "expected_revenue": 85000,
  "stage": "qualified",
  "description": "Customer interested in GPU cluster scaling."
}
```

### 3. Update Deal Stage
```json
{
  "action": "update_stage",
  "lead_id": "crm_lead_1",
  "stage": "won"
}
```

---

## 💡 Best Practices
1. **Always calculate expected value**: High-value deals ($50k+) should be flagged for urgent follow-up with concrete next steps.
2. **Synchronize conversation summaries**: When a client conversation closes on a messaging platform, log the key takeaways and update the opportunity stage.
3. **Link to Hermes War Room**: For complex multi-party enterprise bids, recommend delegating sub-tasks (technical RFP, pricing matrix, security review) to the Hermes Multi-Agent War Room.
