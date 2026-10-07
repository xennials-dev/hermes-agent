"""Hermes CLI commands for Twenty CRM integration.

Provides:
- hermes twenty deals [--stage]
- hermes twenty companies
- hermes twenty people
- hermes twenty summarize <opp_id> [--model <name>]
- hermes twenty search <query> [--limit N]
- hermes twenty approve <task_id>
- hermes twenty briefs [--opp <id>]
- hermes twenty metadata
- hermes twenty log <opp_id> <title> <body>
- hermes twenty webhook <opp_id> [--event <event>]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import List, Optional

from .autonomous_loop import AutonomousDealLoop
from .client import TwentyClient


def create_twenty_parser() -> argparse.ArgumentParser:
    """Creates the CLI argument parser for Twenty CRM operations."""
    parser = argparse.ArgumentParser(
        prog="hermes twenty",
        description="Interact with Twenty CRM, MCP server, and autonomous agent loops.",
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Twenty CRM commands")

    # deals
    deals_p = subparsers.add_parser("deals", help="List active opportunities / deals")
    deals_p.add_argument("--stage", help="Filter by stage (e.g. PROPOSAL, NEGOTIATION)")

    # companies
    subparsers.add_parser("companies", help="List registered client companies")

    # people
    subparsers.add_parser("people", help="List contact people")

    # summarize
    summarize_p = subparsers.add_parser(
        "summarize", help="Run autonomous LLM summarization and sync AI custom objects to Twenty CRM"
    )
    summarize_p.add_argument("opportunity_id", help="ID of the opportunity to summarize")
    summarize_p.add_argument(
        "--model",
        default="glm-chinese",
        help="Model identifier (e.g. glm-chinese, qwen, bloom-z, mistral)",
    )

    # search (pgvector semantic search)
    search_p = subparsers.add_parser("search", help="Perform pgvector semantic search across CRM context")
    search_p.add_argument("query", help="Natural language query string")
    search_p.add_argument("--limit", type=int, default=5, help="Max results")

    # approve
    approve_p = subparsers.add_parser("approve", help="Approve an AI Proposed Task in Twenty CRM")
    approve_p.add_argument("task_id", help="ID of the task to approve")

    # briefs
    briefs_p = subparsers.add_parser("briefs", help="List AI Deal Strategy Briefs")
    briefs_p.add_argument("--opp", help="Filter by Opportunity ID")

    # metadata
    subparsers.add_parser("metadata", help="List Twenty Metadata API objects (standard + custom AI objects)")

    # log
    log_p = subparsers.add_parser("log", help="Log an interaction / note into Twenty CRM")
    log_p.add_argument("opportunity_id", help="Target opportunity ID")
    log_p.add_argument("title", help="Note title")
    log_p.add_argument("body", help="Note body / content")

    # webhook
    webhook_p = subparsers.add_parser(
        "webhook", help="Simulate or deliver a lifecycle webhook event into the autonomous loop"
    )
    webhook_p.add_argument("opportunity_id", help="Target opportunity ID")
    webhook_p.add_argument(
        "--event",
        default="opportunity.created",
        help="Event type",
    )

    # composio-status
    subparsers.add_parser("composio-status", aliases=["composio"], help="Inspect Composio B2B fabric status and audit trail")

    # n8n-status
    subparsers.add_parser("n8n-status", aliases=["n8n"], help="Check n8n workflow engine and webhook listener connectivity")

    return parser


async def run_twenty_cli(args: List[str], client: Optional[TwentyClient] = None) -> int:
    """Execute Twenty CRM CLI commands asynchronously."""
    parser = create_twenty_parser()
    parsed = parser.parse_args(args)

    if not parsed.subcommand:
        parser.print_help()
        return 0

    crm = client or TwentyClient()
    loop = AutonomousDealLoop(twenty_client=crm)

    try:
        if parsed.subcommand == "deals":
            deals = await crm.list_opportunities(stage=parsed.stage)
            print(f"--- Twenty CRM Opportunities ({len(deals)}) ---")
            for d in deals:
                amt = d.get("amount", {})
                val = amt.get("amountMicros", 0) / 1_000_000
                curr = amt.get("currencyCode", "USD")
                print(
                    f"[{d.get('id')}] {d.get('name')} | Stage: {d.get('stage')} | "
                    f"Value: ${val:,.2f} {curr} | Company: {d.get('companyName')}"
                )

        elif parsed.subcommand == "companies":
            comps = await crm.list_companies()
            print(f"--- Twenty CRM Companies ({len(comps)}) ---")
            for c in comps:
                print(f"[{c.get('id')}] {c.get('name')} | Domain: {c.get('domainName')} | Employees: {c.get('employees', 'N/A')}")

        elif parsed.subcommand == "people":
            people = await crm.list_people()
            print(f"--- Twenty CRM Contacts ({len(people)}) ---")
            for p in people:
                print(f"[{p.get('id')}] {p.get('firstName', p.get('name', {}).get('firstName'))} {p.get('lastName', p.get('name', {}).get('lastName'))} | {p.get('email', p.get('emails', {}).get('primaryEmail'))} | {p.get('jobTitle')}")

        elif parsed.subcommand == "summarize":
            print(f"Running autonomous deal loop on opportunity {parsed.opportunity_id} with model '{parsed.model}'...")
            res = await loop.summarize_and_sync_deal(
                opportunity_id=parsed.opportunity_id,
                model_name=parsed.model,
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

        elif parsed.subcommand == "search":
            matches = await crm.semantic_search(query=parsed.query, limit=parsed.limit)
            print(f"--- Twenty pgvector Semantic Matches for '{parsed.query}' ({len(matches)}) ---")
            for m in matches:
                print(f"[{m.get('score')}] [{m.get('objectType')}] {m.get('title')}: {m.get('snippet')}")

        elif parsed.subcommand == "approve":
            res = await crm.approve_task(task_id=parsed.task_id)
            print(f"Task {parsed.task_id} approved! Status: {res.get('status')}")
            print(f"Lifecycle webhook 'task.approved' triggered for Hermes Agent follow-up.")

        elif parsed.subcommand == "briefs":
            briefs = await crm.list_deal_strategy_briefs(opportunity_id=parsed.opp)
            print(f"--- AI Deal Strategy Briefs ({len(briefs)}) ---")
            for b in briefs:
                print(f"[{b.get('id')}] Opp: {b.get('opportunityId')} | Model: {b.get('modelEngine')} | Risk: {b.get('riskScore')}/100")
                print(f"Assessment: {b.get('executiveAssessment')}\n")

        elif parsed.subcommand == "metadata":
            objs = await crm.get_metadata_objects()
            print(f"--- Twenty CRM Metadata API Objects ({len(objs)}) ---")
            for o in objs:
                kind = "CUSTOM AI OBJECT" if o.get("isCustom") else "STANDARD"
                print(f"• {o.get('nameSingular')} ({kind}): {o.get('description')}")

        elif parsed.subcommand == "log":
            note = await crm.create_note(
                title=parsed.title,
                body=parsed.body,
                opportunity_id=parsed.opportunity_id,
                author="Hermes Agent CLI",
            )
            print(f"Note logged successfully to Twenty CRM: ID {note.get('id')}")

        elif parsed.subcommand == "webhook":
            payload = {
                "event": parsed.event,
                "data": {"id": parsed.opportunity_id, "name": "Enterprise Cluster", "stage": "NEGOTIATION"},
            }
            print(f"Simulating lifecycle webhook '{parsed.event}' for opportunity {parsed.opportunity_id}...")
            result = await loop.handle_webhook_event(payload)
            print(f"Webhook processing complete: {result.get('status')} - {result.get('action')}")

        elif parsed.subcommand in ("composio-status", "composio"):
            from .composio_fabric import ComposioFabric
            comp = ComposioFabric()
            print("--- Composio Universal B2B API Fabric Status ---")
            print(f"• Execution Mode: {'LIVE (Connected)' if not comp.is_mock else 'MOCK / AUDIT SIMULATION'}")
            print(f"• API Key Status: {'Configured' if bool(comp.api_key) else 'Unset (set COMPOSIO_API_KEY for live SaaS execution)'}")
            print("• Supported Endpoints: Slack, Linear, Gmail, Google Drive, GitHub, Jira, HubSpot")
            trails = comp.get_audit_trail(limit=5)
            print(f"• Recent Dispatches ({len(trails)}):")
            for t in trails:
                print(f"  [{t.get('timestamp')}] {t.get('app').upper()} -> {t.get('action')} [{t.get('status')}]")

        elif parsed.subcommand in ("n8n-status", "n8n"):
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
                import httpx
                async with httpx.AsyncClient(timeout=2.0) as http_client:
                    resp = await http_client.get("http://localhost:5678/healthz")
                    online = resp.status_code == 200
            except Exception:
                online = False
            print(f"• n8n Instance Connectivity: {'ONLINE' if online else 'OFFLINE (Start via docker compose up -d n8n)'}")

        return 0
    except Exception as exc:
        print(f"Twenty CRM CLI Error: {exc}", file=sys.stderr)
        return 1
