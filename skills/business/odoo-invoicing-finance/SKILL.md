---
name: odoo-invoicing-finance
description: "Automate Odoo invoicing, accounting moves, and payments."
version: 1.0.0
author: Terrance (tee), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Odoo, Invoicing, Accounting, Finance, Payments, Expenses]
    related_skills: [odoo-sales-crm, process-redesign]
---

# Odoo Invoicing & Financial Operations

Manage customer invoices, vendor bills, payment registrations, and financial reconciliations across Odoo Accounting.

---

## 1. Quick Reference

| Action | Target Model | CLI Command Example |
|---|---|---|
| **List Unpaid Invoices** | `account.move` | `python skills/business/odoo/scripts/odoo_client.py search-read --model account.move --domain '[["move_type","=","out_invoice"],["payment_state","=","not_paid"]]'` |
| **Create Customer Invoice** | `account.move` | `python skills/business/odoo/scripts/odoo_client.py create --model account.move --values '{"move_type":"out_invoice","partner_id":1}'` |
| **Track Expenses** | `hr.expense` | `python skills/business/odoo/scripts/odoo_client.py search-read --model hr.expense --fields "name,total_amount,state"` |

---

## 2. Core Accounting Models

- **`account.move`**: `name`, `move_type` (`out_invoice`, `in_invoice`, `out_refund`), `partner_id`, `invoice_date`, `amount_total`, `payment_state` (`not_paid`, `paid`, `in_payment`).
- **`account.move.line`**: `move_id`, `product_id`, `name`, `quantity`, `price_unit`, `account_id`.
- **`account.payment`**: `partner_id`, `amount`, `payment_type` (`inbound`, `outbound`), `journal_id`.

---

## 3. Financial Automation Workflow

1. **Invoice Draft**: Auto-create `account.move` upon sales order confirmation.
2. **Post Invoice**: Trigger `action_post` to post the journal entry.
3. **Payment Receipt**: Track inbound wire or credit card payments and register against invoice.
