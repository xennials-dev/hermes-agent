"""``hermes twenty`` subcommand parser and dispatch handler."""

from __future__ import annotations

import argparse
import asyncio
from typing import Callable, Optional


def build_twenty_parser(subparsers, *, cmd_twenty: Optional[Callable] = None) -> argparse.ArgumentParser:
    """Attach the ``twenty`` subcommand to ``subparsers``."""
    twenty_parser = subparsers.add_parser(
        "twenty",
        help="Interact with Twenty CRM, MCP server, and autonomous deal intelligence",
        description=(
            "Twenty CRM Integration for Hermes Agent.\n\n"
            "Query live opportunities, accounts, contacts, and metadata objects;\n"
            "perform pgvector semantic searches; run autonomous deal summarization;\n"
            "and review/approve AI-proposed tasks."
        ),
    )
    twenty_sub = twenty_parser.add_subparsers(dest="twenty_action")

    # deals
    deals_p = twenty_sub.add_parser("deals", aliases=["opportunities"], help="List active opportunities / deals")
    deals_p.add_argument("--stage", help="Filter by stage (e.g. PROPOSAL, NEGOTIATION, WON)")

    # companies
    twenty_sub.add_parser("companies", aliases=["accounts"], help="List registered client companies")

    # people
    twenty_sub.add_parser("people", aliases=["contacts"], help="List contact people")

    # summarize
    summarize_p = twenty_sub.add_parser(
        "summarize", help="Run autonomous LLM summarization and sync AI custom objects to Twenty CRM"
    )
    summarize_p.add_argument("opportunity_id", help="ID of the opportunity to summarize")
    summarize_p.add_argument(
        "--model",
        default="glm-chinese",
        help="Model identifier (e.g. glm-chinese, qwen, bloom-z, mistral)",
    )

    # search
    search_p = twenty_sub.add_parser("search", help="Perform pgvector semantic search across CRM context")
    search_p.add_argument("query", help="Natural language query string")
    search_p.add_argument("--limit", type=int, default=5, help="Max results (default: 5)")

    # approve
    approve_p = twenty_sub.add_parser("approve", help="Approve an AI Proposed Task in Twenty CRM")
    approve_p.add_argument("task_id", help="ID of the task to approve")

    # briefs
    briefs_p = twenty_sub.add_parser("briefs", help="List AI Deal Strategy Briefs")
    briefs_p.add_argument("--opp", help="Filter by Opportunity ID")

    # metadata
    twenty_sub.add_parser("metadata", help="List Twenty Metadata API objects (standard + custom AI objects)")

    # log
    log_p = twenty_sub.add_parser("log", help="Log an interaction / note into Twenty CRM")
    log_p.add_argument("opportunity_id", help="Target opportunity ID")
    log_p.add_argument("title", help="Note title")
    log_p.add_argument("body", help="Note body / content")

    # webhook
    webhook_p = twenty_sub.add_parser(
        "webhook", help="Simulate or deliver a lifecycle webhook event into the autonomous loop"
    )
    webhook_p.add_argument("opportunity_id", help="Target opportunity ID")
    webhook_p.add_argument(
        "--event",
        default="opportunity.created",
        choices=["opportunity.created", "note.created", "opportunity.stage_updated", "task.approved"],
        help="Event type",
    )

    # employees
    emp_p = twenty_sub.add_parser("employees", aliases=["workforce"], help="List enterprise employees and capacity")
    emp_p.add_argument("--dept", help="Filter by department ID (e.g. dept-sales, dept-sol)")
    emp_p.add_argument("--role", help="Filter by role (e.g. MANAGER, EMPLOYEE, DEPT_HEAD)")

    # departments
    twenty_sub.add_parser("departments", help="List enterprise departments and token budgets")

    # jobs
    jobs_p = twenty_sub.add_parser("jobs", help="Manage enterprise background jobs")
    jobs_sub = jobs_p.add_subparsers(dest="jobs_action")
    jobs_list_p = jobs_sub.add_parser("list", help="List background jobs")
    jobs_list_p.add_argument("--status", help="Filter by status (QUEUED, PROCESSING, COMPLETED, FAILED)")
    jobs_submit_p = jobs_sub.add_parser("submit", help="Submit a new background job")
    jobs_submit_p.add_argument("job_type", help="Job type (BATCH_LEAD_ENRICHMENT, PORTFOLIO_RISK_SCAN, VECTOR_INDEX_SYNC)")
    jobs_submit_p.add_argument("--priority", default="NORMAL", choices=["CRITICAL", "HIGH", "NORMAL", "LOW"], help="Job priority")
    jobs_status_p = jobs_sub.add_parser("status", help="Check status of a job")
    jobs_status_p.add_argument("job_id", help="Job ID")

    # assign
    assign_p = twenty_sub.add_parser("assign", help="Assign lead to employee or auto-assign by skill")
    assign_p.add_argument("opportunity_id", help="Target opportunity ID")
    assign_p.add_argument("--emp", help="Target employee ID (omit for auto-assign)")
    assign_p.add_argument("--skill", default="Chinese_LLM", help="Required skill for auto-assignment")

    # audit-log
    audit_p = twenty_sub.add_parser("audit-log", aliases=["audit"], help="Inspect tamper-proof audit trail")
    audit_p.add_argument("--limit", type=int, default=10, help="Max entries (default: 10)")
    audit_p.add_argument("--verify", action="store_true", help="Verify SHA-256 cryptographic chain integrity")

    # composio-status
    twenty_sub.add_parser("composio-status", aliases=["composio"], help="Inspect Composio B2B fabric status and audit trail")

    # n8n-status
    twenty_sub.add_parser("n8n-status", aliases=["n8n"], help="Check n8n workflow engine and webhook listener connectivity")

    twenty_parser.set_defaults(func=cmd_twenty or execute_twenty_command)
    return twenty_parser


def execute_twenty_command(args: argparse.Namespace) -> int:
    """Execute hermes twenty subcommands."""
    action = getattr(args, "twenty_action", None)
    if not action:
        print("Usage: hermes twenty {deals,companies,people,summarize,search,approve,briefs,metadata,log,webhook}")
        return 0

    from plugins.twenty_crm.client import TwentyClient
    from plugins.twenty_crm.autonomous_loop import AutonomousDealLoop

    crm = TwentyClient()
    loop = AutonomousDealLoop(twenty_client=crm)

    async def _run():
        if action in ("deals", "opportunities"):
            deals = await crm.list_opportunities(stage=getattr(args, "stage", None))
            print(f"--- Twenty CRM Opportunities ({len(deals)}) ---")
            for d in deals:
                amt = d.get("amount", {})
                val = amt.get("amountMicros", 0) / 1_000_000
                curr = amt.get("currencyCode", "USD")
                print(
                    f"[{d.get('id')}] {d.get('name')} | Stage: {d.get('stage')} | "
                    f"Value: ${val:,.2f} {curr} | Company: {d.get('companyName')}"
                )

        elif action in ("companies", "accounts"):
            comps = await crm.list_companies()
            print(f"--- Twenty CRM Companies ({len(comps)}) ---")
            for c in comps:
                print(f"[{c.get('id')}] {c.get('name')} | Domain: {c.get('domainName')} | Employees: {c.get('employees', 'N/A')}")

        elif action in ("people", "contacts"):
            people = await crm.list_people()
            print(f"--- Twenty CRM Contacts ({len(people)}) ---")
            for p in people:
                name_obj = p.get("name") or {}
                first = p.get("firstName") or name_obj.get("firstName") or ""
                last = p.get("lastName") or name_obj.get("lastName") or ""
                email = p.get("email") or (p.get("emails") or {}).get("primaryEmail") or ""
                print(f"[{p.get('id')}] {first} {last} | {email} | {p.get('jobTitle')}")

        elif action == "summarize":
            opp_id = args.opportunity_id
            model = args.model
            print(f"Running autonomous deal loop on opportunity {opp_id} with model '{model}'...")
            res = await loop.summarize_and_sync_deal(
                opportunity_id=opp_id,
                model_name=model,
            )
            print("\nAutonomous AI Custom Objects Created in Twenty CRM:")
            print("=" * 65)
            print(f"• Deal Strategy Brief ID:        {res.get('strategyBriefId')}")
            print(f"• Competitor Intelligence ID:   {res.get('competitorIntelId')}")
            print(f"• Risk Assessment ID:           {res.get('riskAssessmentId')}")
            print(f"• Proposed Task ID (AI_PROPOSED): {res.get('proposedTaskId')}")
            print(f"• Interaction Note ID:          {res.get('noteId')}")
            print("=" * 65)
            print("Summary Narrative:")
            print(res.get("summary"))

        elif action == "search":
            query = args.query
            limit = args.limit
            matches = await crm.semantic_search(query=query, limit=limit)
            print(f"--- Twenty pgvector Semantic Matches for '{query}' ({len(matches)}) ---")
            for m in matches:
                print(f"[{m.get('score')}] [{m.get('objectType')}] {m.get('title')}: {m.get('snippet')}")

        elif action == "approve":
            task_id = args.task_id
            res = await crm.approve_task(task_id=task_id)
            print(f"Task {task_id} approved! Status: {res.get('status')}")
            print(f"Lifecycle webhook 'task.approved' triggered for Hermes Agent follow-up.")

        elif action == "briefs":
            briefs = await crm.list_deal_strategy_briefs(opportunity_id=getattr(args, "opp", None))
            print(f"--- AI Deal Strategy Briefs ({len(briefs)}) ---")
            for b in briefs:
                print(f"[{b.get('id')}] Opp: {b.get('opportunityId')} | Model: {b.get('modelEngine')} | Risk: {b.get('riskScore')}/100")
                print(f"Assessment: {b.get('executiveAssessment')}\n")

        elif action == "metadata":
            objs = await crm.get_metadata_objects()
            print(f"--- Twenty CRM Metadata API Objects ({len(objs)}) ---")
            for o in objs:
                kind = "CUSTOM AI OBJECT" if o.get("isCustom") else "STANDARD"
                print(f"• {o.get('nameSingular')} ({kind}): {o.get('description')}")

        elif action == "log":
            note = await crm.create_note(
                title=args.title,
                body=args.body,
                opportunity_id=args.opportunity_id,
                author="Hermes Agent CLI",
            )
            print(f"Note logged successfully to Twenty CRM: ID {note.get('id')}")

        elif action == "webhook":
            payload = {
                "event": args.event,
                "data": {"id": args.opportunity_id, "name": "Enterprise Cluster", "stage": "NEGOTIATION"},
            }
            print(f"Simulating lifecycle webhook '{args.event}' for opportunity {args.opportunity_id}...")
            result = await loop.handle_webhook_event(payload)
            print(f"Webhook processing complete: {result.get('status')} - {result.get('action')}")

        elif action in ("employees", "workforce"):
            emps = await crm.list_employees(department_id=getattr(args, "dept", None), role=getattr(args, "role", None))
            print(f"--- Enterprise Workforce Roster ({len(emps)}) ---")
            for e in emps:
                active = e.get("activeDealsCount", 0)
                cap = e.get("maxCapacityDeals", 15)
                skills_str = ", ".join(e.get("skills", []))
                print(
                    f"[{e.get('id')}] {e.get('name')} | Role: {e.get('role')} | Dept: {e.get('departmentId')} | "
                    f"Load: {active}/{cap} deals | Skills: [{skills_str}]"
                )

        elif action == "departments":
            depts = await crm.list_departments()
            print(f"--- Enterprise Departments & Token Budgets ({len(depts)}) ---")
            for d in depts:
                budget = d.get("budgetTokens", 0)
                used = d.get("tokensUsed", 0)
                cost = d.get("costAccruedUsd", 0.0)
                print(
                    f"[{d.get('id')}] {d.get('name')} ({d.get('code')}) | Head: {d.get('headEmployeeId')} | "
                    f"Tokens: {used:,}/{budget:,} | Accrued: ${cost:.2f}"
                )

        elif action == "jobs":
            jobs_action = getattr(args, "jobs_action", "list")
            if jobs_action == "submit":
                jtype = args.job_type
                prio = args.priority
                job = await crm.submit_job(job_type=jtype, priority=prio)
                print(f"Enterprise Background Job Submitted!")
                print(f"• Job ID:   {job.get('id')}")
                print(f"• Type:     {job.get('jobType')}")
                print(f"• Priority: {job.get('priority')}")
                print(f"• Status:   {job.get('status')}")
            elif jobs_action == "status":
                jid = args.job_id
                job = await crm.get_job(job_id=jid)
                print(f"--- Job Status: {job.get('id')} ---")
                print(f"Status:   {job.get('status')} ({job.get('progressPct')}%)")
                print(f"Worker:   {job.get('workerId')}")
                print("Logs:")
                for log in job.get("logs", []):
                    print(f"  {log}")
                if job.get("result"):
                    print(f"Result:   {job.get('result')}")
            else:
                jobs = await crm.list_jobs(status=getattr(args, "status", None))
                print(f"--- Enterprise Background Jobs ({len(jobs)}) ---")
                for j in jobs:
                    print(f"[{j.get('id')}] {j.get('jobType')} | Priority: {j.get('priority')} | Status: {j.get('status')} ({j.get('progressPct')}%)")

        elif action == "assign":
            opp_id = args.opportunity_id
            emp_id = getattr(args, "emp", None)
            if emp_id:
                res = await crm.assign_lead(employee_id=emp_id, opportunity_id=opp_id)
                print(f"Lead {opp_id} assigned: {res.get('message')}")
            else:
                skill = getattr(args, "skill", "Chinese_LLM")
                res = await crm.auto_assign_lead(opportunity_id=opp_id, required_skill=skill)
                emp = res.get("assignedEmployee", {})
                print(f"Lead {opp_id} automatically assigned to {emp.get('name')} ({emp.get('id')}) based on '{skill}' skill matching.")

        elif action in ("audit-log", "audit"):
            if getattr(args, "verify", False):
                res = await crm.verify_audit_chain()
                valid = res.get("chainValid")
                print(f"Audit Trail Verification: {'VALID (TAMPER-PROOF)' if valid else 'COMPROMISED'}")
                print(f"• Blocks Verified: {res.get('totalBlocks')}")
                print(f"• Latest Hash:     {res.get('latestHash')}")
                print(f"• Compliance:      {res.get('compliance')}")
            else:
                data = await crm.get_audit_logs(limit=args.limit)
                logs = data.get("logs", [])
                valid = data.get("chainValid")
                print(f"--- Twenty CRM Cryptographic Audit Log (Chain Valid: {valid}) ---")
                for l in logs:
                    print(f"[{l.get('timestamp')}] Actor: {l.get('actor')} | Action: {l.get('action')} | Entity: {l.get('entityType')}/{l.get('entityId')}")
                    print(f"   Hash: {l.get('currentHash')[:16]}... (Prev: {l.get('previousHash')[:16]}...)")

        elif action in ("composio-status", "composio"):
            from plugins.twenty_crm.composio_fabric import ComposioFabric
            comp = ComposioFabric()
            print("--- Composio Universal B2B API Fabric Status ---")
            print(f"• Execution Mode: {'LIVE (Connected)' if not comp.is_mock else 'MOCK / AUDIT SIMULATION'}")
            print(f"• API Key Status: {'Configured' if bool(comp.api_key) else 'Unset (set COMPOSIO_API_KEY for live SaaS execution)'}")
            print("• Supported Endpoints: Slack, Linear, Gmail, Google Drive, GitHub, Jira, HubSpot")
            trails = comp.get_audit_trail(limit=5)
            print(f"• Recent Dispatches ({len(trails)}):")
            for t in trails:
                print(f"  [{t.get('timestamp')}] {t.get('app').upper()} -> {t.get('action')} [{t.get('status')}]")

        elif action in ("n8n-status", "n8n"):
            import httpx
            import os
            from pathlib import Path
            n8n_url = os.environ.get("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/twenty-events")
            print("--- Dedicated n8n Workflow Engine Status ---")
            print(f"• Inbound Webhook Listener: {n8n_url}")
            wf_dir = Path(__file__).resolve().parent.parent.parent / "twenty_crm" / "n8n_workflows"
            wfs = list(wf_dir.glob("*.json")) if wf_dir.exists() else []
            print(f"• Available Workflows ({len(wfs)}):")
            for w in wfs:
                print(f"  - {w.name}")
            try:
                async with httpx.AsyncClient(timeout=2.0) as client:
                    resp = await client.get("http://localhost:5678/healthz")
                    online = resp.status_code == 200
            except Exception:
                online = False
            print(f"• n8n Instance Connectivity: {'ONLINE' if online else 'OFFLINE (Start via docker compose up -d n8n)'}")

        return 0

    return asyncio.run(_run())
