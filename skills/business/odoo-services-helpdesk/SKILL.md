---
name: odoo-services-helpdesk
description: "Manage project tasks, support tickets, and employee hours."
version: 1.0.0
author: Terrance (tee), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Odoo, Projects, Tasks, Helpdesk, Tickets, HR, Timesheets]
    related_skills: [odoo-sales-crm, process-redesign]
---

# Odoo Services, Projects & Helpdesk Management

Orchestrate customer support tickets, project task assignments, team timesheets, and HR records in Odoo.

---

## 1. Quick Reference

| Action | Target Model | CLI Command Example |
|---|---|---|
| **Query Open Tickets** | `helpdesk.ticket` | `python skills/business/odoo/scripts/odoo_client.py search-read --model helpdesk.ticket --domain '[["stage_id","!=","Solved"]]'` |
| **Create Task** | `project.task` | `python skills/business/odoo/scripts/odoo_client.py create --model project.task --values '{"name":"Implement AI Sync","project_id":1}'` |
| **Log Timesheet** | `account.analytic.line` | `python skills/business/odoo/scripts/odoo_client.py create --model account.analytic.line --values '{"name":"Client Meeting","unit_amount":1.5,"project_id":1}'` |
| **Query Employees** | `hr.employee` | `python skills/business/odoo/scripts/odoo_client.py search-read --model hr.employee --fields "name,job_title,work_email"` |

---

## 2. Core Service Models

- **`project.project` & `project.task`**: Agile sprints, task states, assignees, deadlines, and deliverables.
- **`helpdesk.ticket`**: Customer support tickets, priority, SLA deadline, communication thread.
- **`account.analytic.line`**: Timesheets, billable client hours, project costs.
- **`hr.employee` & `hr.applicant`**: Employee records, department structure, recruitment candidates.
- **`calendar.event`**: Appointments and client discovery scheduling.
