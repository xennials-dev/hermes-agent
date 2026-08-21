---
name: odoo-sales-crm
description: "Manage Odoo CRM leads, sales orders, and customer pipelines."
version: 1.0.0
author: Terrance (tee), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Odoo, CRM, Sales, Leads, Quotations, ERP, Business]
    related_skills: [odoo-invoicing-finance, find-clients]
---

# Odoo Sales & CRM Automation

Automate lead intake, opportunity qualification, pipeline stage transitions, quotation creation, and sales order confirmation in Odoo.

---

## 1. Quick Reference

| Action | Target Model | CLI Command Example |
|---|---|---|
| **Query Active Leads** | `crm.lead` | `python skills/business/odoo/scripts/odoo_client.py search-read --model crm.lead --domain '[["type","=","opportunity"]]'` |
| **Create Lead** | `crm.lead` | `python skills/business/odoo/scripts/odoo_client.py create --model crm.lead --values '{"name":"New Enterprise Lead","expected_revenue":15000}'` |
| **Draft Quotation** | `sale.order` | `python skills/business/odoo/scripts/odoo_client.py create --model sale.order --values '{"partner_id": 1}'` |
| **List Customers** | `res.partner` | `python skills/business/odoo/scripts/odoo_client.py search-read --model res.partner --fields "name,email,phone"` |

---

## 2. Key Odoo Models & Fields

- **`crm.lead`**: `name`, `contact_name`, `email_from`, `phone`, `expected_revenue`, `probability`, `stage_id`, `user_id`.
- **`sale.order`**: `name`, `partner_id`, `state` (`draft`, `sent`, `sale`, `done`), `amount_total`, `order_line`.
- **`sale.order.line`**: `order_id`, `product_id`, `product_uom_qty`, `price_unit`, `price_subtotal`.

---

## 3. Workflow Playbook: Lead to Signed Sale

1. **Lead Intake**: Capture inbound inquiries and insert into `crm.lead`.
2. **Opportunity Scoring**: Update `probability` and assign to sales representative.
3. **Quotation Generation**: Generate `sale.order` linked to the customer `res.partner`.
4. **Order Confirmation**: Transition order to confirmed state (`state: 'sale'`).
