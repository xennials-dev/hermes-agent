"""Twenty CRM - Complete Local REST API, Web Engine, MCP Server & Vector Engine.

Implements:
1. Model Context Protocol (MCP) JSON-RPC 2.0 endpoint at /mcp
2. Structured AI Custom Objects via Metadata API (/rest/metadata/objects)
   - DealStrategyBriefs (/rest/dealStrategyBriefs)
   - CompetitorIntelligences (/rest/competitorIntelligences)
   - RiskAssessments (/rest/riskAssessments)
3. Expanded Lifecycle Webhooks (opportunity.created, note.created, opportunity.stage_updated, person.updated, task.approved)
4. Agent-Assigned Tasks with AI_PROPOSED status & Human Action Approvals (/rest/tasks/{id}/approve)
5. Vector Database & Semantic Search (/rest/semantic-search)
6. Role-Based AI Data Governance (HERMES_AGENT role restrictions)
7. Native AI Workflows (/rest/ai/workflows)
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional
import uuid

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Path as PathParam, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from twenty_crm.audit_logger import AuditChainLogger
from twenty_crm.enterprise_models import Department, Employee, EnterpriseJob, EnterpriseRole, JobPriority, JobStatus
from twenty_crm.job_queue import EnterpriseJobEngine
from twenty_crm.scim import SCIMProvider

STATIC_DIR = Path(__file__).resolve().parent / "static"
DATA_FILE = Path(__file__).resolve().parent / "data.json"

# In-memory database with standard and AI custom objects
DB: Dict[str, Any] = {
    "companies": [
        {
            "id": "comp-1",
            "name": "ByteDance AI Infrastructure",
            "domainName": "bytedance.com",
            "employees": 110000,
            "annualRecurringRevenue": 240000,
            "createdAt": "2026-09-15T08:00:00Z",
            "enrichedTags": ["AI", "Enterprise", "High-Volume"],
        },
        {
            "id": "comp-2",
            "name": "NovaTech Solutions",
            "domainName": "novatech-solutions.io",
            "employees": 450,
            "annualRecurringRevenue": 85000,
            "createdAt": "2026-09-20T10:30:00Z",
            "enrichedTags": ["SaaS", "Growth", "Cloud"],
        },
        {
            "id": "comp-3",
            "name": "Tencent Cloud AI Lab",
            "domainName": "tencent.com",
            "employees": 105000,
            "annualRecurringRevenue": 350000,
            "createdAt": "2026-09-28T14:15:00Z",
            "enrichedTags": ["Hyperscaler", "GPU Cluster", "Enterprise"],
        },
    ],
    "people": [
        {
            "id": "person-1",
            "name": {"firstName": "Wei", "lastName": "Chen"},
            "emails": {"primaryEmail": "chen.wei@bytedance-labs.cn"},
            "phones": {"primaryPhoneNumber": "+86 10 5888 1234"},
            "jobTitle": "Head of AI Infrastructure",
            "companyId": "comp-1",
            "city": "Beijing",
        },
        {
            "id": "person-2",
            "name": {"firstName": "Sarah", "lastName": "Jenkins"},
            "emails": {"primaryEmail": "s.jenkins@novatech-solutions.io"},
            "phones": {"primaryPhoneNumber": "+1 415 555 0192"},
            "jobTitle": "VP of Engineering",
            "companyId": "comp-2",
            "city": "San Francisco",
        },
        {
            "id": "person-3",
            "name": {"firstName": "Ming", "lastName": "Li"},
            "emails": {"primaryEmail": "ming.li@tencent-cloud.com"},
            "phones": {"primaryPhoneNumber": "+86 21 6123 4567"},
            "jobTitle": "Director of Cloud Systems",
            "companyId": "comp-3",
            "city": "Shenzhen",
        },
    ],
    "opportunities": [
        {
            "id": "opp-1",
            "name": "Enterprise Cluster LLM Mesh (GLM-4 & Qwen)",
            "amount": {"amountMicros": 240000000000, "currencyCode": "USD"},
            "stage": "NEGOTIATION",
            "closeDate": "2026-11-15T00:00:00Z",
            "companyId": "comp-1",
            "pointOfContactId": "person-1",
            "probability": 85,
        },
        {
            "id": "opp-2",
            "name": "Hermes Agent Autonomous Customer Gateway",
            "amount": {"amountMicros": 85000000000, "currencyCode": "USD"},
            "stage": "PROPOSAL",
            "closeDate": "2026-12-01T00:00:00Z",
            "companyId": "comp-2",
            "pointOfContactId": "person-2",
            "probability": 60,
        },
        {
            "id": "opp-3",
            "name": "High-Throughput Chinese Inference Pipeline",
            "amount": {"amountMicros": 350000000000, "currencyCode": "USD"},
            "stage": "DISCOVERY",
            "closeDate": "2026-12-20T00:00:00Z",
            "companyId": "comp-3",
            "pointOfContactId": "person-3",
            "probability": 40,
        },
    ],
    "notes": [
        {
            "id": "note-1",
            "title": "Initial Architecture Review with Chen Wei",
            "body": "Customer confirmed requirement for localized Chinese prompt routing via GLM-4 and Bloom-Z with strict sub-50ms latency.",
            "targetOpportunityId": "opp-1",
            "targetCompanyId": "comp-1",
            "targetPersonId": "person-1",
            "author": "Hermes Autonomous Agent",
            "createdAt": "2026-10-01T11:00:00Z",
            "category": "TECHNICAL_REQ",
            "sentiment": "POSITIVE",
        },
    ],
    "tasks": [
        {
            "id": "task-1",
            "title": "Send NVIDIA Nemotron Benchmarking Report to Sarah Jenkins",
            "body": "Prepare latency and memory comparisons for 8B model on single L4 GPU.",
            "status": "APPROVED",
            "dueAt": "2026-10-10T17:00:00Z",
            "targetOpportunityId": "opp-2",
            "createdBy": "Hermes Agent",
        },
        {
            "id": "task-2",
            "title": "Deliver Enterprise SLA Contract for ByteDance Cluster",
            "body": "AI proposed contract review and throughput guarantees.",
            "status": "AI_PROPOSED",
            "dueAt": "2026-10-12T12:00:00Z",
            "targetOpportunityId": "opp-1",
            "createdBy": "Hermes Agent",
        },
    ],
    "dealStrategyBriefs": [
        {
            "id": "dsb-1",
            "opportunityId": "opp-1",
            "executiveAssessment": "High strategic value account. Client requires hybrid routing across GLM-4 and local Qwen instances to preserve data sovereignty.",
            "riskScore": 18,
            "closingProbability": 88,
            "strategicRecommendations": [
                "Deploy on-prem vLLM inference node for proof-of-concept",
                "Guarantee sub-50ms latency for Chinese tokens",
                "Integrate Twenty CRM webhook dispatchers into client gateway",
            ],
            "modelEngine": "glm-chinese",
            "createdAt": "2026-10-04T12:00:00Z",
        }
    ],
    "competitorIntelligences": [
        {
            "id": "ci-1",
            "opportunityId": "opp-1",
            "competitorName": "Proprietary Cloud Provider X",
            "pricingPressure": "MEDIUM",
            "winLossFactor": "Client refuses US-hosted cloud lock-in; Hermes open-weight stack wins on sovereignty.",
            "counterTactics": "Highlight zero egress cost, local model privacy, and Hermes Agent multi-platform support.",
            "createdAt": "2026-10-04T12:05:00Z",
        }
    ],
    "riskAssessments": [
        {
            "id": "ra-1",
            "opportunityId": "opp-1",
            "riskLevel": "LOW",
            "technicalRisks": "Local GPU memory allocation during peak Chinese LLM batch inference.",
            "commercialRisks": "Standard quarterly procurement review delays.",
            "mitigationPlan": "Provision 4x NVIDIA L4 cluster with dynamic quantization and automated failover.",
            "createdAt": "2026-10-04T12:10:00Z",
        }
    ],
    "departments": [
        {
            "id": "dept-sales",
            "name": "Enterprise Sales",
            "code": "SALES",
            "headEmployeeId": "emp-101",
            "budgetTokens": 20_000_000,
            "tokensUsed": 1_240_000,
            "costAccruedUsd": 124.0,
            "createdAt": "2026-09-01T00:00:00Z",
        },
        {
            "id": "dept-sol",
            "name": "Solutions Architecture",
            "code": "SOLENG",
            "headEmployeeId": "emp-104",
            "budgetTokens": 15_000_000,
            "tokensUsed": 2_850_000,
            "costAccruedUsd": 285.0,
            "createdAt": "2026-09-01T00:00:00Z",
        },
        {
            "id": "dept-cs",
            "name": "Customer Success",
            "code": "CS",
            "headEmployeeId": "emp-105",
            "budgetTokens": 10_000_000,
            "tokensUsed": 450_000,
            "costAccruedUsd": 45.0,
            "createdAt": "2026-09-01T00:00:00Z",
        },
        {
            "id": "dept-exec",
            "name": "Executive Leadership",
            "code": "EXEC",
            "headEmployeeId": "emp-100",
            "budgetTokens": 50_000_000,
            "tokensUsed": 3_100_000,
            "costAccruedUsd": 310.0,
            "createdAt": "2026-09-01T00:00:00Z",
        },
        {
            "id": "dept-legal",
            "name": "Legal & Compliance",
            "code": "LEGAL",
            "headEmployeeId": "emp-106",
            "budgetTokens": 5_000_000,
            "tokensUsed": 120_000,
            "costAccruedUsd": 12.0,
            "createdAt": "2026-09-01T00:00:00Z",
        },
    ],
    "employees": [
        {
            "id": "emp-100",
            "name": "Victoria Sterling",
            "email": "victoria.sterling@enterprise.com",
            "role": "SUPER_ADMIN",
            "departmentId": "dept-exec",
            "managerId": None,
            "title": "Chief Commercial Officer",
            "quotaAnnual": 10_000_000.0,
            "closedWonAmount": 3_450_000.0,
            "activeDealsCount": 0,
            "maxCapacityDeals": 20,
            "skills": ["Executive_Strategy", "Capital_Allocation"],
            "isActive": True,
            "createdAt": "2026-09-01T00:00:00Z",
        },
        {
            "id": "emp-101",
            "name": "Elena Rostova",
            "email": "elena.rostova@enterprise.com",
            "role": "DEPT_HEAD",
            "departmentId": "dept-sales",
            "managerId": "emp-100",
            "title": "VP of Enterprise Sales",
            "quotaAnnual": 3_500_000.0,
            "closedWonAmount": 1_240_000.0,
            "activeDealsCount": 1,
            "maxCapacityDeals": 10,
            "skills": ["Enterprise_Negotiation", "Chinese_LLM", "Tier1_Accounts"],
            "isActive": True,
            "createdAt": "2026-09-01T00:00:00Z",
        },
        {
            "id": "emp-102",
            "name": "Marcus Vance",
            "email": "marcus.vance@enterprise.com",
            "role": "MANAGER",
            "departmentId": "dept-sales",
            "managerId": "emp-101",
            "title": "Enterprise Sales Director",
            "quotaAnnual": 1_800_000.0,
            "closedWonAmount": 650_000.0,
            "activeDealsCount": 2,
            "maxCapacityDeals": 12,
            "skills": ["Cloud_Migration", "SaaS_Security", "Team_Mentorship"],
            "isActive": True,
            "createdAt": "2026-09-05T00:00:00Z",
        },
        {
            "id": "emp-103",
            "name": "Jin Woo",
            "email": "jin.woo@enterprise.com",
            "role": "EMPLOYEE",
            "departmentId": "dept-sales",
            "managerId": "emp-102",
            "title": "Senior Enterprise Account Exec",
            "quotaAnnual": 800_000.0,
            "closedWonAmount": 240_000.0,
            "activeDealsCount": 3,
            "maxCapacityDeals": 10,
            "skills": ["Chinese_LLM", "OnPrem_Deploy", "Bilingual_Mandarin"],
            "isActive": True,
            "createdAt": "2026-09-10T00:00:00Z",
        },
        {
            "id": "emp-104",
            "name": "Aria Montgomery",
            "email": "aria.montgomery@enterprise.com",
            "role": "DEPT_HEAD",
            "departmentId": "dept-sol",
            "managerId": "emp-100",
            "title": "Principal AI Solutions Architect",
            "quotaAnnual": 0.0,
            "closedWonAmount": 0.0,
            "activeDealsCount": 4,
            "maxCapacityDeals": 8,
            "skills": ["vLLM_Benchmarking", "GPU_Clusters", "pgvector", "Hermes_Agent_Mesh"],
            "isActive": True,
            "createdAt": "2026-09-01T00:00:00Z",
        },
    ],
    "webhooks": [
        {
            "id": "wh-n8n-router",
            "targetUrl": os.environ.get("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/twenty-events"),
            "event": "*",
            "description": "Route Twenty CRM native lifecycle webhooks to dedicated n8n workflow engine",
        }
    ],
    "auditLogs": [],
}

# Initialize Enterprise Singletons
audit_logger = AuditChainLogger(DB.setdefault("auditLogs", []))
job_engine = EnterpriseJobEngine(max_concurrent_workers=4)
scim_provider = SCIMProvider(DB.setdefault("employees", []), DB.setdefault("departments", []))


# --- Metadata Definitions for Twenty Metadata API ---
METADATA_OBJECTS = [
    {
        "nameSingular": "opportunity",
        "namePlural": "opportunities",
        "labelSingular": "Opportunity",
        "labelPlural": "Opportunities",
        "description": "Sales deals, value pipelines, and stages.",
        "isCustom": False,
        "fields": ["name", "amount", "stage", "closeDate", "companyId", "pointOfContactId", "probability"],
    },
    {
        "nameSingular": "company",
        "namePlural": "companies",
        "labelSingular": "Company",
        "labelPlural": "Companies",
        "description": "Client accounts and enterprises.",
        "isCustom": False,
        "fields": ["name", "domainName", "employees", "annualRecurringRevenue", "enrichedTags"],
    },
    {
        "nameSingular": "person",
        "namePlural": "people",
        "labelSingular": "Person",
        "labelPlural": "People",
        "description": "Contacts and points of contact.",
        "isCustom": False,
        "fields": ["name", "emails", "phones", "jobTitle", "companyId", "city"],
    },
    {
        "nameSingular": "note",
        "namePlural": "notes",
        "labelSingular": "Note",
        "labelPlural": "Notes",
        "description": "Interaction logs, transcripts, and touchpoints.",
        "isCustom": False,
        "fields": ["title", "body", "targetOpportunityId", "targetCompanyId", "targetPersonId", "author", "category", "sentiment"],
    },
    {
        "nameSingular": "task",
        "namePlural": "tasks",
        "labelSingular": "Task",
        "labelPlural": "Tasks",
        "description": "Action items, due dates, and approvals.",
        "isCustom": False,
        "fields": ["title", "body", "status", "dueAt", "targetOpportunityId", "createdBy"],
    },
    {
        "nameSingular": "dealStrategyBrief",
        "namePlural": "dealStrategyBriefs",
        "labelSingular": "Deal Strategy Brief",
        "labelPlural": "Deal Strategy Briefs",
        "description": "Structured AI executive strategic assessment and closing tactics generated by Hermes Agent.",
        "isCustom": True,
        "fields": ["opportunityId", "executiveAssessment", "riskScore", "closingProbability", "strategicRecommendations", "modelEngine"],
    },
    {
        "nameSingular": "competitorIntelligence",
        "namePlural": "competitorIntelligences",
        "labelSingular": "Competitor Intelligence",
        "labelPlural": "Competitor Intelligences",
        "description": "Structured AI competitive analysis, pricing pressure, and counter-tactics.",
        "isCustom": True,
        "fields": ["opportunityId", "competitorName", "pricingPressure", "winLossFactor", "counterTactics"],
    },
    {
        "nameSingular": "riskAssessment",
        "namePlural": "riskAssessments",
        "labelSingular": "Risk Assessment",
        "labelPlural": "Risk Assessments",
        "description": "Structured AI technical and commercial risk factors with mitigation plans.",
        "isCustom": True,
        "fields": ["opportunityId", "riskLevel", "technicalRisks", "commercialRisks", "mitigationPlan"],
    },
]


def _save_db() -> None:
    try:
        DATA_FILE.write_text(json.dumps(DB, indent=2), encoding="utf-8")
    except Exception:
        pass


def _load_db() -> None:
    global DB
    if DATA_FILE.is_file():
        try:
            loaded = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                for k, v in loaded.items():
                    if k in DB and isinstance(v, list):
                        DB[k] = v
        except Exception:
            pass


# --- Vector Database & Semantic Embedding Utilities ---
def _tokenize_text(text: str) -> List[str]:
    return re.findall(r"\b[a-zA-Z0-9_\u4e00-\u9fa5]{2,}\b", text.lower())


def _build_embedding_vector(text: str, vocab_size: int = 256) -> List[float]:
    """Generates a normalized deterministic dense embedding vector simulating pgvector embeddings."""
    tokens = _tokenize_text(text)
    vec = [0.0] * vocab_size
    if not tokens:
        return vec
    for tok in tokens:
        idx = hash(tok) % vocab_size
        vec[idx] += 1.0
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec


def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    return sum(a * b for a, b in zip(vec_a, vec_b))


def _semantic_search_crm(query: str, limit: int = 5, object_type: Optional[str] = None) -> List[Dict[str, Any]]:
    query_vec = _build_embedding_vector(query)
    candidates: List[Dict[str, Any]] = []

    # Search Opportunities
    if not object_type or object_type == "opportunity":
        for o in DB["opportunities"]:
            text = f"{o.get('name', '')} {o.get('stage', '')} {o.get('companyName', '')}"
            score = _cosine_similarity(query_vec, _build_embedding_vector(text))
            candidates.append({
                "id": o["id"],
                "objectType": "opportunity",
                "title": o.get("name"),
                "snippet": f"Stage: {o.get('stage')}, Prob: {o.get('probability')}%",
                "score": round(score, 4),
            })

    # Search Notes
    if not object_type or object_type == "note":
        for n in DB["notes"]:
            text = f"{n.get('title', '')} {n.get('body', '')}"
            score = _cosine_similarity(query_vec, _build_embedding_vector(text))
            candidates.append({
                "id": n["id"],
                "objectType": "note",
                "title": n.get("title"),
                "snippet": n.get("body", "")[:160] + "...",
                "score": round(score, 4),
            })

    # Search DealStrategyBriefs
    if not object_type or object_type == "dealStrategyBrief":
        for b in DB.get("dealStrategyBriefs", []):
            text = f"{b.get('executiveAssessment', '')} {' '.join(b.get('strategicRecommendations', []))}"
            score = _cosine_similarity(query_vec, _build_embedding_vector(text))
            candidates.append({
                "id": b["id"],
                "objectType": "dealStrategyBrief",
                "title": f"Strategy Brief ({b.get('opportunityId')})",
                "snippet": b.get("executiveAssessment", "")[:160] + "...",
                "score": round(score, 4),
            })

    # Search CompetitorIntelligences
    if not object_type or object_type == "competitorIntelligence":
        for ci in DB.get("competitorIntelligences", []):
            text = f"{ci.get('competitorName', '')} {ci.get('winLossFactor', '')} {ci.get('counterTactics', '')}"
            score = _cosine_similarity(query_vec, _build_embedding_vector(text))
            candidates.append({
                "id": ci["id"],
                "objectType": "competitorIntelligence",
                "title": f"Competitor Intel: {ci.get('competitorName')}",
                "snippet": ci.get("counterTactics", "")[:160] + "...",
                "score": round(score, 4),
            })

    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[:limit]


# --- Role-Based AI Data Governance ---
def _verify_governance(action: str, resource: str, role: Optional[str] = None):
    """Enforces strict governance permissions for Hermes Agent role."""
    current_role = role or os.environ.get("TWENTY_ACTIVE_ROLE", "ADMIN")
    if current_role == "HERMES_AGENT":
        # Disallow deletion of core financial entities and companies
        if action == "DELETE" and resource in ("companies", "people", "opportunities"):
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "GovernanceViolation",
                    "role": "HERMES_AGENT",
                    "forbiddenAction": f"{action}:{resource}",
                    "message": "Hermes Agent role is restricted from deleting core enterprise CRM entities.",
                },
            )
        # Disallow mutating core revenue without human approval
        if action in ("UPDATE", "CREATE") and resource == "financial_override":
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "GovernanceViolation",
                    "role": "HERMES_AGENT",
                    "message": "Direct revenue overrides require ADMIN role authorization.",
                },
            )


@asynccontextmanager
async def lifespan(app: FastAPI):
    _load_db()
    await job_engine.start()
    audit_logger.log(
        actor="SYSTEM",
        actor_role="SUPER_ADMIN",
        action="SERVER_START",
        entity_type="system",
        entity_id="twenty-crm-engine",
        details={"version": "0.3.0-enterprise", "workers": 4},
    )
    yield
    await job_engine.stop()
    _save_db()


app = FastAPI(title="Twenty CRM Enterprise Engine", version="0.3.0-enterprise", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", include_in_schema=False)
async def serve_root():
    index_file = STATIC_DIR / "index.html"
    if index_file.is_file():
        return FileResponse(index_file)
    return {"message": "Twenty CRM Enterprise Engine online. Open /rest/healthz or /docs"}


@app.get("/rest/healthz")
async def healthz():
    return {
        "status": "ok",
        "app": "Twenty CRM",
        "version": "0.3.0-enterprise",
        "features": {
            "mcpServer": True,
            "metadataApi": True,
            "vectorPgvector": True,
            "aiGovernance": True,
            "nativeWorkflows": True,
            "enterpriseDepartments": True,
            "enterpriseEmployees": True,
            "enterpriseJobEngine": True,
            "auditChainLogger": True,
            "scim2": True,
        },
        "activeWorkers": job_engine.max_concurrent_workers,
        "auditLogCount": len(audit_logger.logs),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# =====================================================================
# 1. MODEL CONTEXT PROTOCOL (MCP) JSON-RPC 2.0 ENDPOINT
# =====================================================================
@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """Model Context Protocol (MCP) JSON-RPC 2.0 endpoint for Hermes Agent."""
    body = await request.json()
    method = body.get("method")
    req_id = body.get("id", 1)
    params = body.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": False},
                    "resources": {"subscribe": False, "listChanged": False},
                },
                "serverInfo": {"name": "twenty-crm-mcp", "version": "0.2.0"},
            },
        }

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "twenty_list_opportunities",
                        "description": "List CRM sales opportunities/deals with optional stage filtering.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"stage": {"type": "string", "description": "e.g. DISCOVERY, PROPOSAL, NEGOTIATION, WON"}},
                        },
                    },
                    {
                        "name": "twenty_get_opportunity",
                        "description": "Get deep details for an opportunity by ID.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"opportunityId": {"type": "string"}},
                            "required": ["opportunityId"],
                        },
                    },
                    {
                        "name": "twenty_list_notes",
                        "description": "List interactions, customer communication minutes, and AI summaries.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"opportunityId": {"type": "string"}},
                        },
                    },
                    {
                        "name": "twenty_create_note",
                        "description": "Create an interaction note attached to an opportunity and company.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "body": {"type": "string"},
                                "opportunityId": {"type": "string"},
                                "author": {"type": "string"},
                            },
                            "required": ["title", "body"],
                        },
                    },
                    {
                        "name": "twenty_create_task",
                        "description": "Propose an agent task with status 'AI_PROPOSED' or 'TODO'.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "body": {"type": "string"},
                                "opportunityId": {"type": "string"},
                                "status": {"type": "string", "default": "AI_PROPOSED"},
                            },
                            "required": ["title"],
                        },
                    },
                    {
                        "name": "twenty_semantic_search",
                        "description": "Perform pgvector semantic search across all CRM notes, deal briefs, and competitor intelligence.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "Natural language query e.g. 'high throughput clusters'"},
                                "limit": {"type": "integer", "default": 5},
                            },
                            "required": ["query"],
                        },
                    },
                    {
                        "name": "twenty_create_deal_strategy_brief",
                        "description": "Store a structured AI Deal Strategy Brief custom object via Twenty Metadata API.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "opportunityId": {"type": "string"},
                                "executiveAssessment": {"type": "string"},
                                "riskScore": {"type": "integer"},
                                "closingProbability": {"type": "integer"},
                                "strategicRecommendations": {"type": "array", "items": {"type": "string"}},
                                "modelEngine": {"type": "string"},
                            },
                            "required": ["opportunityId", "executiveAssessment", "strategicRecommendations"],
                        },
                    },
                    {
                        "name": "twenty_create_competitor_intel",
                        "description": "Store structured Competitor Intelligence custom object via Twenty Metadata API.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "opportunityId": {"type": "string"},
                                "competitorName": {"type": "string"},
                                "pricingPressure": {"type": "string"},
                                "winLossFactor": {"type": "string"},
                                "counterTactics": {"type": "string"},
                            },
                            "required": ["opportunityId", "competitorName", "counterTactics"],
                        },
                    },
                    {
                        "name": "twenty_create_risk_assessment",
                        "description": "Store structured Risk Assessment custom object via Twenty Metadata API.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "opportunityId": {"type": "string"},
                                "riskLevel": {"type": "string"},
                                "technicalRisks": {"type": "string"},
                                "commercialRisks": {"type": "string"},
                                "mitigationPlan": {"type": "string"},
                            },
                            "required": ["opportunityId", "riskLevel", "mitigationPlan"],
                        },
                    },
                    {
                        "name": "twenty_approve_task",
                        "description": "Approve an AI-proposed task and trigger follow-up execution.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"taskId": {"type": "string"}},
                            "required": ["taskId"],
                        },
                    },
                    {
                        "name": "twenty_list_employees",
                        "description": "List enterprise employees with department, role, and capacity metrics.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "departmentId": {"type": "string"},
                                "role": {"type": "string"},
                            },
                        },
                    },
                    {
                        "name": "twenty_assign_record",
                        "description": "Assign an opportunity or task to an enterprise employee.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "entityType": {"type": "string", "enum": ["opportunity", "task"]},
                                "entityId": {"type": "string"},
                                "employeeId": {"type": "string"},
                            },
                            "required": ["entityType", "entityId", "employeeId"],
                        },
                    },
                    {
                        "name": "twenty_submit_enterprise_job",
                        "description": "Submit an asynchronous enterprise background job (BATCH_LEAD_ENRICHMENT, PORTFOLIO_RISK_SCAN, VECTOR_INDEX_SYNC).",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "jobType": {"type": "string"},
                                "priority": {"type": "string", "enum": ["CRITICAL", "HIGH", "NORMAL", "LOW"], "default": "NORMAL"},
                                "payload": {"type": "object"},
                            },
                            "required": ["jobType"],
                        },
                    },
                    {
                        "name": "twenty_check_job_status",
                        "description": "Check real-time progress percentage, status, and outputs of an enterprise background job.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"jobId": {"type": "string"}},
                            "required": ["jobId"],
                        },
                    },
                ]
            },
        }

    elif method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})

        if tool_name == "twenty_list_opportunities":
            stage = args.get("stage")
            opps = DB["opportunities"]
            if stage:
                opps = [o for o in opps if o.get("stage", "").upper() == stage.upper()]
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(opps, indent=2)}]}}

        elif tool_name == "twenty_get_opportunity":
            opp_id = args.get("opportunityId")
            opp = next((o for o in DB["opportunities"] if o["id"] == opp_id), None)
            if not opp:
                return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32602, "message": f"Opportunity {opp_id} not found"}}
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(opp, indent=2)}]}}

        elif tool_name == "twenty_list_notes":
            opp_id = args.get("opportunityId")
            notes = DB["notes"]
            if opp_id:
                notes = [n for n in notes if n.get("targetOpportunityId") == opp_id]
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(notes, indent=2)}]}}

        elif tool_name == "twenty_create_note":
            new_id = f"note-{uuid.uuid4().hex[:8]}"
            item = {
                "id": new_id,
                "title": args.get("title"),
                "body": args.get("body"),
                "targetOpportunityId": args.get("opportunityId"),
                "author": args.get("author", "Hermes Agent (via MCP)"),
                "createdAt": datetime.now(timezone.utc).isoformat(),
            }
            DB["notes"].append(item)
            _save_db()
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(item, indent=2)}]}}

        elif tool_name == "twenty_create_task":
            new_id = f"task-{uuid.uuid4().hex[:8]}"
            item = {
                "id": new_id,
                "title": args.get("title"),
                "body": args.get("body", ""),
                "targetOpportunityId": args.get("opportunityId"),
                "status": args.get("status", "AI_PROPOSED"),
                "createdBy": "Hermes Agent (via MCP)",
                "createdAt": datetime.now(timezone.utc).isoformat(),
            }
            DB["tasks"].append(item)
            _save_db()
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(item, indent=2)}]}}

        elif tool_name == "twenty_semantic_search":
            query = args.get("query", "")
            limit = args.get("limit", 5)
            results = _semantic_search_crm(query, limit=limit)
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(results, indent=2)}]}}

        elif tool_name == "twenty_create_deal_strategy_brief":
            new_id = f"dsb-{uuid.uuid4().hex[:8]}"
            brief = {
                "id": new_id,
                "opportunityId": args.get("opportunityId"),
                "executiveAssessment": args.get("executiveAssessment"),
                "riskScore": args.get("riskScore", 20),
                "closingProbability": args.get("closingProbability", 75),
                "strategicRecommendations": args.get("strategicRecommendations", []),
                "modelEngine": args.get("modelEngine", "glm-chinese"),
                "createdAt": datetime.now(timezone.utc).isoformat(),
            }
            DB.setdefault("dealStrategyBriefs", []).append(brief)
            _save_db()
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(brief, indent=2)}]}}

        elif tool_name == "twenty_create_competitor_intel":
            new_id = f"ci-{uuid.uuid4().hex[:8]}"
            ci = {
                "id": new_id,
                "opportunityId": args.get("opportunityId"),
                "competitorName": args.get("competitorName"),
                "pricingPressure": args.get("pricingPressure", "MEDIUM"),
                "winLossFactor": args.get("winLossFactor", ""),
                "counterTactics": args.get("counterTactics"),
                "createdAt": datetime.now(timezone.utc).isoformat(),
            }
            DB.setdefault("competitorIntelligences", []).append(ci)
            _save_db()
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(ci, indent=2)}]}}

        elif tool_name == "twenty_create_risk_assessment":
            new_id = f"ra-{uuid.uuid4().hex[:8]}"
            ra = {
                "id": new_id,
                "opportunityId": args.get("opportunityId"),
                "riskLevel": args.get("riskLevel", "LOW"),
                "technicalRisks": args.get("technicalRisks", ""),
                "commercialRisks": args.get("commercialRisks", ""),
                "mitigationPlan": args.get("mitigationPlan"),
                "createdAt": datetime.now(timezone.utc).isoformat(),
            }
            DB.setdefault("riskAssessments", []).append(ra)
            _save_db()
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(ra, indent=2)}]}}

        elif tool_name == "twenty_approve_task":
            task_id = args.get("taskId")
            task = next((t for t in DB["tasks"] if t["id"] == task_id), None)
            if not task:
                return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32602, "message": f"Task {task_id} not found"}}
            task["status"] = "APPROVED"
            task["approvedAt"] = datetime.now(timezone.utc).isoformat()
            audit_logger.log(actor="HERMES_AGENT", actor_role="HERMES_AGENT", action="APPROVE_TASK", entity_type="task", entity_id=task_id)
            _save_db()
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(task, indent=2)}]}}

        elif tool_name == "twenty_list_employees":
            dept = args.get("departmentId")
            role = args.get("role")
            emps = DB.get("employees", [])
            if dept:
                emps = [e for e in emps if e.get("departmentId") == dept]
            if role:
                emps = [e for e in emps if e.get("role") == role]
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(emps, indent=2)}]}}

        elif tool_name == "twenty_assign_record":
            etype = args.get("entityType")
            eid = args.get("entityId")
            emp_id = args.get("employeeId")
            emp = next((e for e in DB.get("employees", []) if e["id"] == emp_id), None)
            if not emp:
                return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32602, "message": f"Employee {emp_id} not found"}}

            if etype == "opportunity":
                opp = next((o for o in DB["opportunities"] if o["id"] == eid), None)
                if not opp:
                    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32602, "message": f"Opportunity {eid} not found"}}
                opp["assignedEmployeeId"] = emp_id
                emp["activeDealsCount"] = emp.get("activeDealsCount", 0) + 1
                audit_logger.log(actor="HERMES_AGENT", actor_role="HERMES_AGENT", action="ASSIGN_OPPORTUNITY", entity_type="opportunity", entity_id=eid, details={"assignedEmployee": emp_id})
                _save_db()
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": f"Opportunity {eid} assigned to {emp['name']} ({emp_id})."}]}}
            elif etype == "task":
                task = next((t for t in DB["tasks"] if t["id"] == eid), None)
                if not task:
                    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32602, "message": f"Task {eid} not found"}}
                task["assignedEmployeeId"] = emp_id
                audit_logger.log(actor="HERMES_AGENT", actor_role="HERMES_AGENT", action="ASSIGN_TASK", entity_type="task", entity_id=eid, details={"assignedEmployee": emp_id})
                _save_db()
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": f"Task {eid} assigned to {emp['name']} ({emp_id})."}]}}
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32602, "message": f"Invalid entityType {etype}"}}

        elif tool_name == "twenty_submit_enterprise_job":
            jtype = args.get("jobType")
            priority = args.get("priority", "NORMAL")
            payload = args.get("payload", {})
            job = await job_engine.submit_job(job_type=jtype, payload=payload, priority=JobPriority(priority), submitted_by_employee_id="HERMES_AGENT")
            audit_logger.log(actor="HERMES_AGENT", actor_role="HERMES_AGENT", action="JOB_SUBMIT", entity_type="job", entity_id=job["id"], details={"jobType": jtype, "priority": priority})
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(job, indent=2)}]}}

        elif tool_name == "twenty_check_job_status":
            jid = args.get("jobId")
            job = job_engine.get_job(jid)
            if not job:
                return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32602, "message": f"Job {jid} not found"}}
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(job, indent=2)}]}}

        else:
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method {tool_name} not found"}}

    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Unknown RPC method {method}"}}


# =====================================================================
# 2. METADATA API & STRUCTURED AI CUSTOM OBJECTS
# =====================================================================
@app.get("/rest/metadata/objects")
async def get_metadata_objects():
    """Returns schemas for standard CRM objects and custom AI objects."""
    return {"data": {"objects": METADATA_OBJECTS}}


# --- Deal Strategy Briefs ---
@app.get("/rest/dealStrategyBriefs")
async def list_deal_strategy_briefs(opportunityId: Optional[str] = None):
    briefs = DB.get("dealStrategyBriefs", [])
    if opportunityId:
        briefs = [b for b in briefs if b.get("opportunityId") == opportunityId]
    return {"data": {"dealStrategyBriefs": briefs}}


@app.post("/rest/dealStrategyBriefs")
async def create_deal_strategy_brief(payload: Dict[str, Any]):
    new_id = f"dsb-{uuid.uuid4().hex[:8]}"
    item = {
        "id": new_id,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        **payload,
    }
    DB.setdefault("dealStrategyBriefs", []).append(item)
    _save_db()
    return {"data": {"createDealStrategyBrief": item}}


# --- Competitor Intelligence ---
@app.get("/rest/competitorIntelligences")
async def list_competitor_intelligences(opportunityId: Optional[str] = None):
    items = DB.get("competitorIntelligences", [])
    if opportunityId:
        items = [i for i in items if i.get("opportunityId") == opportunityId]
    return {"data": {"competitorIntelligences": items}}


@app.post("/rest/competitorIntelligences")
async def create_competitor_intelligence(payload: Dict[str, Any]):
    new_id = f"ci-{uuid.uuid4().hex[:8]}"
    item = {
        "id": new_id,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        **payload,
    }
    DB.setdefault("competitorIntelligences", []).append(item)
    _save_db()
    return {"data": {"createCompetitorIntelligence": item}}


# --- Risk Assessments ---
@app.get("/rest/riskAssessments")
async def list_risk_assessments(opportunityId: Optional[str] = None):
    items = DB.get("riskAssessments", [])
    if opportunityId:
        items = [i for i in items if i.get("opportunityId") == opportunityId]
    return {"data": {"riskAssessments": items}}


@app.post("/rest/riskAssessments")
async def create_risk_assessment(payload: Dict[str, Any]):
    new_id = f"ra-{uuid.uuid4().hex[:8]}"
    item = {
        "id": new_id,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        **payload,
    }
    DB.setdefault("riskAssessments", []).append(item)
    _save_db()
    return {"data": {"createRiskAssessment": item}}


# =====================================================================
# 3. VECTOR DATABASE (PGVECTOR) SEMANTIC SEARCH
# =====================================================================
@app.post("/rest/semantic-search")
async def semantic_search_endpoint(payload: Dict[str, Any]):
    """Performs semantic search across historical CRM notes, deals, briefs, and competitor intelligence."""
    query = payload.get("query", "")
    if not query:
        raise HTTPException(400, "Query string is required")
    limit = int(payload.get("limit", 5))
    object_type = payload.get("objectType")
    results = _semantic_search_crm(query, limit=limit, object_type=object_type)
    return {"data": {"query": query, "totalMatches": len(results), "matches": results}}


# =====================================================================
# 4. AGENT TASKS & ACTION APPROVALS
# =====================================================================
@app.get("/rest/tasks")
async def list_tasks(status: Optional[str] = None):
    tasks = DB["tasks"]
    if status:
        tasks = [t for t in tasks if t.get("status", "").upper() == status.upper()]
    return {"data": {"tasks": tasks}}


@app.post("/rest/tasks")
async def create_task(payload: Dict[str, Any]):
    new_id = f"task-{uuid.uuid4().hex[:8]}"
    item = {
        "id": new_id,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "status": payload.get("status", "TODO"),
        "createdBy": payload.get("createdBy", "Hermes Agent"),
        **payload,
    }
    DB["tasks"].append(item)
    _save_db()
    return {"data": {"createTask": item}}


@app.post("/rest/tasks/{id}/approve")
async def approve_task(id: str, background_tasks: BackgroundTasks):
    """Human approvals workflow for AI-proposed tasks."""
    for t in DB["tasks"]:
        if t["id"] == id:
            t["status"] = "APPROVED"
            t["approvedAt"] = datetime.now(timezone.utc).isoformat()
            _save_db()
            # Dispatch lifecycle webhook
            for wh in DB["webhooks"]:
                if wh.get("event") in ("task.approved", "*"):
                    background_tasks.add_task(_dispatch_webhook, wh["targetUrl"], "task.approved", t)
            return {"data": {"task": t, "status": "APPROVED", "message": "Task approved. Hermes Agent follow-up triggered."}}
    raise HTTPException(404, "Task not found")


@app.post("/rest/tasks/{id}/reject")
async def reject_task(id: str):
    for t in DB["tasks"]:
        if t["id"] == id:
            t["status"] = "REJECTED"
            t["rejectedAt"] = datetime.now(timezone.utc).isoformat()
            _save_db()
            return {"data": {"task": t, "status": "REJECTED"}}
    raise HTTPException(404, "Task not found")


# =====================================================================
# 5. EXPANDED LIFECYCLE WEBHOOKS & SUBSCRIPTIONS
# =====================================================================
@app.get("/rest/webhooks")
async def list_webhooks():
    return {"data": {"webhooks": DB["webhooks"]}}


@app.post("/rest/webhooks")
async def register_webhook(payload: Dict[str, Any]):
    new_id = f"wh-{uuid.uuid4().hex[:8]}"
    item = {"id": new_id, **payload}
    DB["webhooks"].append(item)
    _save_db()
    return {"data": {"registerWebhook": item}}


@app.post("/rest/webhooks/trigger")
async def manual_trigger_webhook(payload: Dict[str, Any], background_tasks: BackgroundTasks):
    event = payload.get("event", "opportunity.created")
    opp_id = payload.get("opportunityId")
    opp = next((o for o in DB["opportunities"] if o["id"] == opp_id), None) if opp_id else DB["opportunities"][0]
    for wh in DB["webhooks"]:
        background_tasks.add_task(_dispatch_webhook, wh["targetUrl"], event, opp or {})
    return {"status": "triggered", "event": event, "targetOpportunity": opp}


async def _dispatch_webhook(url: str, event: str, record: Dict[str, Any]) -> None:
    """Dispatches webhook event to n8n workflow engine or external subscribers."""
    import httpx
    event_id = f"evt-{uuid.uuid4().hex[:12]}"
    payload = {
        "eventId": event_id,
        "event": event,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "TwentyCRM",
        "data": record,
    }
    headers = {
        "Content-Type": "application/json",
        "X-Twenty-Event": event,
        "X-Twenty-Event-Id": event_id,
    }
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            await client.post(url, json=payload, headers=headers)
    except Exception:
        pass


# =====================================================================
# 6. NATIVE AI WORKFLOWS (Categorization & Lead Enrichment)
# =====================================================================
@app.get("/rest/ai/workflows")
async def get_ai_workflows():
    return {
        "data": {
            "workflows": [
                {
                    "name": "lead-enrichment",
                    "status": "ACTIVE",
                    "description": "Auto-enriches company tags, domain verification, and scale bracket.",
                },
                {
                    "name": "note-sentiment-categorization",
                    "status": "ACTIVE",
                    "description": "Extracts sentiment, urgency, and category on note creation.",
                },
                {
                    "name": "hermes-strategic-router",
                    "status": "ACTIVE",
                    "description": "Routes high-stakes deals to Hermes Agent + local GLM-4/Qwen cluster for strategy briefs.",
                },
            ]
        }
    }


def _run_native_note_enrichment(note: Dict[str, Any]) -> None:
    """Native high-volume workflow: categorizes note sentiment and keywords."""
    body_lower = note.get("body", "").lower()
    if any(k in body_lower for k in ("risk", "delay", "concern", "blocker")):
        note["sentiment"] = "AT_RISK"
        note["category"] = "RISK_ALERT"
    elif any(k in body_lower for k in ("contract", "sla", "sign", "deal", "close")):
        note["sentiment"] = "POSITIVE"
        note["category"] = "CLOSING_SIGNAL"
    else:
        note["sentiment"] = "NEUTRAL"
        note["category"] = "GENERAL_COMMUNICATION"


# =====================================================================
# 7. CORE ENTITIES (OPPORTUNITIES, COMPANIES, PEOPLE, NOTES)
# =====================================================================
@app.get("/rest/opportunities")
async def list_opportunities():
    comp_map = {c["id"]: c["name"] for c in DB["companies"]}
    person_map = {p["id"]: f"{p['name']['firstName']} {p['name']['lastName']}" for p in DB["people"]}
    enriched = []
    for opp in DB["opportunities"]:
        e = dict(opp)
        e["companyName"] = comp_map.get(opp.get("companyId", ""), "Unknown Company")
        e["pointOfContactName"] = person_map.get(opp.get("pointOfContactId", ""), "Unassigned")
        enriched.append(e)
    return {"data": {"opportunities": enriched}}


@app.post("/rest/opportunities")
async def create_opportunity(payload: Dict[str, Any], background_tasks: BackgroundTasks):
    new_id = f"opp-{uuid.uuid4().hex[:8]}"
    item = {
        "id": new_id,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "stage": payload.get("stage", "DISCOVERY"),
        **payload,
    }
    DB["opportunities"].append(item)
    _save_db()

    for wh in DB["webhooks"]:
        if wh.get("event") in ("opportunity.created", "*"):
            background_tasks.add_task(_dispatch_webhook, wh["targetUrl"], "opportunity.created", item)

    return {"data": {"createOpportunity": item}}


@app.patch("/rest/opportunities/{id}")
async def update_opportunity(id: str, payload: Dict[str, Any], background_tasks: BackgroundTasks):
    for opp in DB["opportunities"]:
        if opp["id"] == id:
            old_stage = opp.get("stage")
            opp.update(payload)
            _save_db()
            new_stage = opp.get("stage")

            # Dispatch stage_updated event if stage changed
            event = "opportunity.stage_updated" if old_stage != new_stage else "opportunity.updated"
            for wh in DB["webhooks"]:
                if wh.get("event") in (event, "*"):
                    background_tasks.add_task(_dispatch_webhook, wh["targetUrl"], event, opp)
            return {"data": {"updateOpportunity": opp}}
    raise HTTPException(404, "Opportunity not found")


@app.delete("/rest/opportunities/{id}")
async def delete_opportunity(id: str = PathParam(...), x_api_role: Optional[str] = Header(None)):
    _verify_governance("DELETE", "opportunities", x_api_role)
    for i, opp in enumerate(DB["opportunities"]):
        if opp["id"] == id:
            removed = DB["opportunities"].pop(i)
            _save_db()
            return {"data": {"deleteOpportunity": removed}}
    raise HTTPException(404, "Opportunity not found")


@app.get("/rest/companies")
async def list_companies():
    return {"data": {"companies": DB["companies"]}}


@app.post("/rest/companies")
async def create_company(payload: Dict[str, Any]):
    new_id = f"comp-{uuid.uuid4().hex[:8]}"
    item = {
        "id": new_id,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "enrichedTags": ["Lead", "Enriched"],
        **payload,
    }
    DB["companies"].append(item)
    _save_db()
    return {"data": {"createCompany": item}}


@app.delete("/rest/companies/{id}")
async def delete_company(id: str = PathParam(...), x_api_role: Optional[str] = Header(None)):
    _verify_governance("DELETE", "companies", x_api_role)
    for i, c in enumerate(DB["companies"]):
        if c["id"] == id:
            removed = DB["companies"].pop(i)
            _save_db()
            return {"data": {"deleteCompany": removed}}
    raise HTTPException(404, "Company not found")


@app.get("/rest/people")
async def list_people():
    return {"data": {"people": DB["people"]}}


@app.post("/rest/people")
async def create_person(payload: Dict[str, Any]):
    new_id = f"person-{uuid.uuid4().hex[:8]}"
    item = {"id": new_id, "createdAt": datetime.now(timezone.utc).isoformat(), **payload}
    DB["people"].append(item)
    _save_db()
    return {"data": {"createPerson": item}}


@app.patch("/rest/people/{id}")
async def update_person(id: str, payload: Dict[str, Any], background_tasks: BackgroundTasks):
    for p in DB["people"]:
        if p["id"] == id:
            p.update(payload)
            _save_db()
            for wh in DB["webhooks"]:
                if wh.get("event") in ("person.updated", "*"):
                    background_tasks.add_task(_dispatch_webhook, wh["targetUrl"], "person.updated", p)
            return {"data": {"updatePerson": p}}
    raise HTTPException(404, "Person not found")


@app.delete("/rest/people/{id}")
async def delete_person(id: str = PathParam(...), x_api_role: Optional[str] = Header(None)):
    _verify_governance("DELETE", "people", x_api_role)
    for i, p in enumerate(DB["people"]):
        if p["id"] == id:
            removed = DB["people"].pop(i)
            _save_db()
            return {"data": {"deletePerson": removed}}
    raise HTTPException(404, "Person not found")


@app.get("/rest/notes")
async def list_notes(opportunityId: Optional[str] = None):
    notes = DB["notes"]
    if opportunityId:
        notes = [n for n in notes if n.get("targetOpportunityId") == opportunityId]
    return {"data": {"notes": sorted(notes, key=lambda x: x.get("createdAt", ""), reverse=True)}}


@app.post("/rest/notes")
async def create_note(payload: Dict[str, Any], background_tasks: BackgroundTasks):
    new_id = f"note-{uuid.uuid4().hex[:8]}"
    item = {
        "id": new_id,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "author": payload.get("author", "Hermes Agent"),
        **payload,
    }
    # Run native AI workflow enrichment
    _run_native_note_enrichment(item)
    DB["notes"].append(item)
    _save_db()

    # Dispatch note.created webhook so Hermes can extract action items
    for wh in DB["webhooks"]:
        if wh.get("event") in ("note.created", "*"):
            background_tasks.add_task(_dispatch_webhook, wh["targetUrl"], "note.created", item)

    return {"data": {"createNote": item}}


# =====================================================================
# 6. ENTERPRISE WORKFORCE & DEPARTMENT HIERARCHY
# =====================================================================
@app.get("/rest/departments")
async def list_departments():
    return {"data": {"departments": DB.get("departments", [])}}


@app.post("/rest/departments")
async def create_department(payload: Dict[str, Any]):
    new_id = f"dept-{uuid.uuid4().hex[:6]}"
    item = {
        "id": new_id,
        "name": payload.get("name", "New Department"),
        "code": payload.get("code", "DEPT"),
        "headEmployeeId": payload.get("headEmployeeId"),
        "budgetTokens": payload.get("budgetTokens", 10_000_000),
        "tokensUsed": 0,
        "costAccruedUsd": 0.0,
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    DB.setdefault("departments", []).append(item)
    audit_logger.log(actor="ADMIN", actor_role="SUPER_ADMIN", action="CREATE_DEPARTMENT", entity_type="department", entity_id=new_id, details=item)
    _save_db()
    return {"data": {"department": item}}


@app.get("/rest/employees")
async def list_employees(departmentId: Optional[str] = None, role: Optional[str] = None):
    emps = DB.get("employees", [])
    if departmentId:
        emps = [e for e in emps if e.get("departmentId") == departmentId]
    if role:
        emps = [e for e in emps if e.get("role") == role]
    return {"data": {"employees": emps}}


@app.get("/rest/employees/{id}")
async def get_employee(id: str):
    emp = next((e for e in DB.get("employees", []) if e["id"] == id), None)
    if not emp:
        raise HTTPException(404, "Employee not found")
    return {"data": {"employee": emp}}


@app.post("/rest/employees")
async def create_employee(payload: Dict[str, Any]):
    new_id = f"emp-{uuid.uuid4().hex[:6]}"
    item = {
        "id": new_id,
        "name": payload.get("name", "New Employee"),
        "email": payload.get("email", f"{new_id}@enterprise.com"),
        "role": payload.get("role", "EMPLOYEE"),
        "departmentId": payload.get("departmentId", "dept-sales"),
        "managerId": payload.get("managerId"),
        "title": payload.get("title", "Account Executive"),
        "quotaAnnual": float(payload.get("quotaAnnual", 500_000.0)),
        "closedWonAmount": 0.0,
        "activeDealsCount": 0,
        "maxCapacityDeals": int(payload.get("maxCapacityDeals", 12)),
        "skills": payload.get("skills", ["Enterprise_Sales"]),
        "isActive": True,
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    DB.setdefault("employees", []).append(item)
    audit_logger.log(actor="ADMIN", actor_role="SUPER_ADMIN", action="CREATE_EMPLOYEE", entity_type="employee", entity_id=new_id, details=item)
    _save_db()
    return {"data": {"employee": item}}


@app.get("/rest/employees/{id}/team")
async def get_employee_team(id: str):
    """Returns all direct reports reporting to this manager."""
    team = [e for e in DB.get("employees", []) if e.get("managerId") == id]
    return {"data": {"managerId": id, "directReportsCount": len(team), "team": team}}


@app.post("/rest/employees/{id}/assign-lead")
async def assign_lead_to_employee(id: str, payload: Dict[str, Any]):
    emp = next((e for e in DB.get("employees", []) if e["id"] == id), None)
    if not emp:
        raise HTTPException(404, "Employee not found")

    opp_id = payload.get("opportunityId")
    opp = next((o for o in DB["opportunities"] if o["id"] == opp_id), None)
    if not opp:
        raise HTTPException(404, "Opportunity not found")

    opp["assignedEmployeeId"] = id
    emp["activeDealsCount"] = emp.get("activeDealsCount", 0) + 1
    audit_logger.log(actor="ADMIN", actor_role="MANAGER", action="ASSIGN_LEAD", entity_type="opportunity", entity_id=opp_id, details={"assignedTo": id, "employeeName": emp["name"]})
    _save_db()
    return {"data": {"opportunity": opp, "assignedTo": emp, "message": f"Lead assigned to {emp['name']}"}}


@app.post("/rest/auto-assign-lead")
async def auto_assign_lead(payload: Dict[str, Any]):
    """Intelligently matches incoming lead to optimal employee based on skills and capacity."""
    opp_id = payload.get("opportunityId")
    required_skill = payload.get("requiredSkill", "Chinese_LLM")
    opp = next((o for o in DB["opportunities"] if o["id"] == opp_id), None)
    if not opp:
        raise HTTPException(404, "Opportunity not found")

    # Filter candidates with matching skill and capacity available
    candidates = [
        e for e in DB.get("employees", [])
        if e.get("isActive", True)
        and (not required_skill or required_skill in e.get("skills", []))
        and e.get("activeDealsCount", 0) < e.get("maxCapacityDeals", 15)
    ]

    if not candidates:
        # Fallback to least loaded active sales rep
        candidates = sorted(
            [e for e in DB.get("employees", []) if e.get("isActive", True) and e.get("departmentId") == "dept-sales"],
            key=lambda x: x.get("activeDealsCount", 0),
        )

    if not candidates:
        raise HTTPException(500, "No available employees found for assignment")

    selected = sorted(candidates, key=lambda x: x.get("activeDealsCount", 0))[0]
    opp["assignedEmployeeId"] = selected["id"]
    selected["activeDealsCount"] = selected.get("activeDealsCount", 0) + 1

    audit_logger.log(actor="HERMES_AGENT", actor_role="HERMES_AGENT", action="AUTO_ASSIGN_LEAD", entity_type="opportunity", entity_id=opp_id, details={"selectedEmployee": selected["id"], "reason": f"Skill match '{required_skill}' with capacity available."})
    _save_db()
    return {"data": {"opportunity": opp, "assignedEmployee": selected, "selectionReason": f"Optimal skill match: {required_skill}"}}


# =====================================================================
# 7. DISTRIBUTED ENTERPRISE BACKGROUND JOBS
# =====================================================================
@app.post("/rest/jobs")
async def submit_job(payload: Dict[str, Any]):
    job_type = payload.get("jobType")
    if not job_type:
        raise HTTPException(400, "jobType is required")
    priority_str = payload.get("priority", "NORMAL").upper()
    try:
        priority = JobPriority(priority_str)
    except Exception:
        priority = JobPriority.NORMAL

    job = await job_engine.submit_job(
        job_type=job_type,
        payload=payload.get("payload", {}),
        priority=priority,
        submitted_by_employee_id=payload.get("submittedByEmployeeId", "emp-101"),
        department_id=payload.get("departmentId", "dept-sales"),
    )
    audit_logger.log(actor=payload.get("submittedByEmployeeId", "emp-101"), actor_role="EMPLOYEE", action="SUBMIT_JOB", entity_type="job", entity_id=job["id"], details={"jobType": job_type, "priority": priority.value})
    return {"data": {"job": job}}


@app.get("/rest/jobs")
async def list_jobs(status: Optional[str] = None, jobType: Optional[str] = None, employeeId: Optional[str] = None, limit: int = 50):
    jobs = job_engine.list_jobs(status=status, job_type=jobType, employee_id=employeeId, limit=limit)
    return {"data": {"totalJobs": len(jobs), "jobs": jobs}}


@app.get("/rest/jobs/{id}")
async def get_job(id: str):
    job = job_engine.get_job(id)
    if not job:
        raise HTTPException(404, "Job not found")
    return {"data": {"job": job}}


@app.post("/rest/jobs/{id}/cancel")
async def cancel_job(id: str):
    success = await job_engine.cancel_job(id)
    if not success:
        raise HTTPException(400, "Job could not be cancelled (either not found or already terminal)")
    audit_logger.log(actor="ADMIN", actor_role="SUPER_ADMIN", action="CANCEL_JOB", entity_type="job", entity_id=id)
    return {"data": {"jobId": id, "cancelled": True, "message": "Job successfully cancelled"}}


# =====================================================================
# 8. CRYPTOGRAPHIC IMMUTABLE AUDIT LOG (SOC2 / GDPR)
# =====================================================================
@app.get("/rest/audit-logs")
async def get_audit_logs(actor: Optional[str] = None, entityType: Optional[str] = None, limit: int = 50):
    logs = audit_logger.get_logs(actor=actor, entity_type=entityType, limit=limit)
    return {"data": {"totalEntries": len(logs), "chainValid": audit_logger.verify_chain_integrity(), "logs": logs}}


@app.get("/rest/audit-logs/verify")
async def verify_audit_chain():
    is_valid = audit_logger.verify_chain_integrity()
    return {
        "data": {
            "chainValid": is_valid,
            "totalBlocks": len(audit_logger.logs),
            "latestHash": audit_logger.latest_hash,
            "compliance": "SOC2_TYPE_II_READY",
        }
    }


# =====================================================================
# 9. SCIM 2.0 DIRECTORY INTEGRATION (RFC 7643 / RFC 7644)
# =====================================================================
@app.get("/scim/v2/Users")
async def scim_list_users(startIndex: int = 1, count: int = 50):
    return scim_provider.list_users(start_index=startIndex, count=count)


@app.get("/scim/v2/Users/{id}")
async def scim_get_user(id: str):
    user = scim_provider.get_user(id)
    if not user:
        raise HTTPException(404, "User not found")
    return user


@app.post("/scim/v2/Users")
async def scim_create_user(payload: Dict[str, Any]):
    user = scim_provider.create_user(payload)
    audit_logger.log(actor="SCIM_SYNC", actor_role="IDP", action="PROVISION_USER", entity_type="employee", entity_id=user["id"], details=payload)
    _save_db()
    return user


@app.patch("/scim/v2/Users/{id}")
async def scim_patch_user(id: str, payload: Dict[str, Any]):
    ops = payload.get("Operations", [])
    user = scim_provider.patch_user(id, ops)
    if not user:
        raise HTTPException(404, "User not found")
    audit_logger.log(actor="SCIM_SYNC", actor_role="IDP", action="UPDATE_USER", entity_type="employee", entity_id=id, details=payload)
    _save_db()
    return user


@app.get("/scim/v2/Groups")
async def scim_list_groups():
    return scim_provider.list_groups()

