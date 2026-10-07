"""Twenty CRM REST & MCP API Client for Hermes Agent."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid
import httpx

DEFAULT_TWENTY_URL = os.environ.get("TWENTY_SERVER_URL", "http://localhost:3000").rstrip("/")
LOCAL_DATA_FILE = Path(__file__).resolve().parent.parent.parent / "twenty_crm" / "data.json"


def _load_local_data() -> Dict[str, Any]:
    if LOCAL_DATA_FILE.is_file():
        try:
            return json.loads(LOCAL_DATA_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_local_data(data: Dict[str, Any]) -> None:
    if LOCAL_DATA_FILE.parent.exists():
        try:
            LOCAL_DATA_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass


class TwentyClient:
    """Async client for Twenty CRM REST endpoints, MCP server, and Metadata API."""

    def __init__(
        self,
        base_url: str = DEFAULT_TWENTY_URL,
        api_key: Optional[str] = None,
        role: str = "HERMES_AGENT",
        timeout: float = 10.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.environ.get("TWENTY_API_KEY", "")
        self.role = role
        self.timeout = timeout
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Role": self.role,
        }
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"

    # --- System / Health ---
    async def health_check(self) -> Dict[str, Any]:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            resp = await client.get("/rest/healthz")
            resp.raise_for_status()
            return resp.json()

    # --- Model Context Protocol (MCP) ---
    async def call_mcp(self, method: str, params: Optional[Dict[str, Any]] = None, req_id: int = 1) -> Dict[str, Any]:
        payload = {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params or {}}
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            resp = await client.post("/mcp", json=payload, headers=self.headers)
            resp.raise_for_status()
            return resp.json()

    async def mcp_list_tools(self) -> List[Dict[str, Any]]:
        res = await self.call_mcp("tools/list")
        return res.get("result", {}).get("tools", [])

    async def mcp_call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        res = await self.call_mcp("tools/call", {"name": name, "arguments": arguments})
        return res.get("result", {})

    # --- Metadata API ---
    async def get_metadata_objects(self) -> List[Dict[str, Any]]:
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                resp = await client.get("/rest/metadata/objects", headers=self.headers)
                resp.raise_for_status()
                return resp.json().get("data", {}).get("objects", [])
        except Exception:
            return [
                {"nameSingular": "opportunity", "namePlural": "opportunities", "isCustom": False, "description": "Sales deals, value pipelines, and stages."},
                {"nameSingular": "company", "namePlural": "companies", "isCustom": False, "description": "Client accounts and enterprises."},
                {"nameSingular": "person", "namePlural": "people", "isCustom": False, "description": "Contacts and points of contact."},
                {"nameSingular": "note", "namePlural": "notes", "isCustom": False, "description": "Interaction logs, transcripts, and touchpoints."},
                {"nameSingular": "task", "namePlural": "tasks", "isCustom": False, "description": "Action items, due dates, and approvals."},
                {"nameSingular": "dealStrategyBrief", "namePlural": "dealStrategyBriefs", "isCustom": True, "description": "Structured AI executive strategic assessment and closing tactics."},
                {"nameSingular": "competitorIntelligence", "namePlural": "competitorIntelligences", "isCustom": True, "description": "Structured AI competitive analysis, pricing pressure, and counter-tactics."},
                {"nameSingular": "riskAssessment", "namePlural": "riskAssessments", "isCustom": True, "description": "Structured AI technical and commercial risk factors with mitigation plans."},
            ]

    # --- Opportunities (Deals) ---
    async def list_opportunities(self, stage: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                resp = await client.get("/rest/opportunities", headers=self.headers)
                resp.raise_for_status()
                opps = resp.json().get("data", {}).get("opportunities", [])
        except Exception:
            local = _load_local_data()
            opps = local.get("opportunities", [])
        if stage:
            opps = [o for o in opps if o.get("stage", "").upper() == stage.upper()]
        return opps

    async def get_opportunity(self, opp_id: str) -> Dict[str, Any]:
        opps = await self.list_opportunities()
        for o in opps:
            if o.get("id") == opp_id:
                return o
        raise ValueError(f"Opportunity '{opp_id}' not found in Twenty CRM")

    async def create_opportunity(
        self,
        name: str,
        amount_dollars: float = 0.0,
        company_id: Optional[str] = None,
        stage: str = "DISCOVERY",
        point_of_contact_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = {
            "name": name,
            "amount": {"amountMicros": int(amount_dollars * 1_000_000), "currencyCode": "USD"},
            "stage": stage.upper(),
            "companyId": company_id,
            "pointOfContactId": point_of_contact_id,
        }
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            resp = await client.post("/rest/opportunities", json=payload, headers=self.headers)
            resp.raise_for_status()
            return resp.json().get("data", {}).get("createOpportunity", {})

    async def update_opportunity_stage(self, opp_id: str, new_stage: str) -> Dict[str, Any]:
        payload = {"stage": new_stage.upper()}
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            resp = await client.patch(f"/rest/opportunities/{opp_id}", json=payload, headers=self.headers)
            resp.raise_for_status()
            return resp.json().get("data", {}).get("updateOpportunity", {})

    # --- Companies & People ---
    async def list_companies(self) -> List[Dict[str, Any]]:
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                resp = await client.get("/rest/companies", headers=self.headers)
                resp.raise_for_status()
                return resp.json().get("data", {}).get("companies", [])
        except Exception:
            local = _load_local_data()
            return local.get("companies", [])

    async def list_people(self) -> List[Dict[str, Any]]:
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                resp = await client.get("/rest/people", headers=self.headers)
                resp.raise_for_status()
                return resp.json().get("data", {}).get("people", [])
        except Exception:
            local = _load_local_data()
            return local.get("people", [])

    # --- Notes ---
    async def list_notes(self, opportunity_id: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            params = {"opportunityId": opportunity_id} if opportunity_id else {}
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                resp = await client.get("/rest/notes", params=params, headers=self.headers)
                resp.raise_for_status()
                return resp.json().get("data", {}).get("notes", [])
        except Exception:
            local = _load_local_data()
            notes = local.get("notes", [])
            if opportunity_id:
                notes = [n for n in notes if n.get("targetOpportunityId") == opportunity_id]
            return notes

    async def create_note(
        self,
        title: str,
        body: str,
        opportunity_id: Optional[str] = None,
        company_id: Optional[str] = None,
        author: str = "Hermes Agent",
    ) -> Dict[str, Any]:
        payload = {
            "title": title,
            "body": body,
            "targetOpportunityId": opportunity_id,
            "targetCompanyId": company_id,
            "author": author,
        }
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                resp = await client.post("/rest/notes", json=payload, headers=self.headers)
                resp.raise_for_status()
                return resp.json().get("data", {}).get("createNote", {})
        except Exception:
            local = _load_local_data()
            item = {"id": f"note-{uuid.uuid4().hex[:8]}", "createdAt": datetime.now(timezone.utc).isoformat(), **payload}
            local.setdefault("notes", []).append(item)
            _save_local_data(local)
            return item

    # --- Structured AI Custom Objects ---
    async def list_deal_strategy_briefs(self, opportunity_id: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            params = {"opportunityId": opportunity_id} if opportunity_id else {}
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                resp = await client.get("/rest/dealStrategyBriefs", params=params, headers=self.headers)
                resp.raise_for_status()
                return resp.json().get("data", {}).get("dealStrategyBriefs", [])
        except Exception:
            local = _load_local_data()
            briefs = local.get("dealStrategyBriefs", [])
            if opportunity_id:
                briefs = [b for b in briefs if b.get("opportunityId") == opportunity_id]
            return briefs

    async def create_deal_strategy_brief(
        self,
        opportunity_id: str,
        executive_assessment: str,
        risk_score: int,
        closing_probability: int,
        strategic_recommendations: List[str],
        model_engine: str = "glm-chinese",
    ) -> Dict[str, Any]:
        payload = {
            "opportunityId": opportunity_id,
            "executiveAssessment": executive_assessment,
            "riskScore": risk_score,
            "closingProbability": closing_probability,
            "strategicRecommendations": strategic_recommendations,
            "modelEngine": model_engine,
        }
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                resp = await client.post("/rest/dealStrategyBriefs", json=payload, headers=self.headers)
                resp.raise_for_status()
                return resp.json().get("data", {}).get("createDealStrategyBrief", {})
        except Exception:
            local = _load_local_data()
            item = {"id": f"dsb-{uuid.uuid4().hex[:8]}", "createdAt": datetime.now(timezone.utc).isoformat(), **payload}
            local.setdefault("dealStrategyBriefs", []).append(item)
            _save_local_data(local)
            return item

    async def create_competitor_intelligence(
        self,
        opportunity_id: str,
        competitor_name: str,
        pricing_pressure: str,
        win_loss_factor: str,
        counter_tactics: str,
    ) -> Dict[str, Any]:
        payload = {
            "opportunityId": opportunity_id,
            "competitorName": competitor_name,
            "pricingPressure": pricing_pressure,
            "winLossFactor": win_loss_factor,
            "counterTactics": counter_tactics,
        }
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                resp = await client.post("/rest/competitorIntelligences", json=payload, headers=self.headers)
                resp.raise_for_status()
                return resp.json().get("data", {}).get("createCompetitorIntelligence", {})
        except Exception:
            local = _load_local_data()
            item = {"id": f"ci-{uuid.uuid4().hex[:8]}", "createdAt": datetime.now(timezone.utc).isoformat(), **payload}
            local.setdefault("competitorIntelligences", []).append(item)
            _save_local_data(local)
            return item

    async def create_risk_assessment(
        self,
        opportunity_id: str,
        risk_level: str,
        technical_risks: str,
        commercial_risks: str,
        mitigation_plan: str,
    ) -> Dict[str, Any]:
        payload = {
            "opportunityId": opportunity_id,
            "riskLevel": risk_level,
            "technicalRisks": technical_risks,
            "commercialRisks": commercial_risks,
            "mitigationPlan": mitigation_plan,
        }
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                resp = await client.post("/rest/riskAssessments", json=payload, headers=self.headers)
                resp.raise_for_status()
                return resp.json().get("data", {}).get("createRiskAssessment", {})
        except Exception:
            local = _load_local_data()
            item = {"id": f"ra-{uuid.uuid4().hex[:8]}", "createdAt": datetime.now(timezone.utc).isoformat(), **payload}
            local.setdefault("riskAssessments", []).append(item)
            _save_local_data(local)
            return item

    # --- Tasks & Approvals ---
    async def list_tasks(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            params = {"status": status} if status else {}
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                resp = await client.get("/rest/tasks", params=params, headers=self.headers)
                resp.raise_for_status()
                return resp.json().get("data", {}).get("tasks", [])
        except Exception:
            local = _load_local_data()
            tasks = local.get("tasks", [])
            if status:
                tasks = [t for t in tasks if t.get("status", "").upper() == status.upper()]
            return tasks

    async def create_task(
        self,
        title: str,
        body: Optional[str] = None,
        opportunity_id: Optional[str] = None,
        status: str = "AI_PROPOSED",
        due_at: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = {
            "title": title,
            "body": body or "",
            "targetOpportunityId": opportunity_id,
            "status": status,
            "dueAt": due_at,
            "createdBy": "Hermes Agent",
        }
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                resp = await client.post("/rest/tasks", json=payload, headers=self.headers)
                resp.raise_for_status()
                return resp.json().get("data", {}).get("createTask", {})
        except Exception:
            local = _load_local_data()
            item = {"id": f"task-{uuid.uuid4().hex[:8]}", "createdAt": datetime.now(timezone.utc).isoformat(), **payload}
            local.setdefault("tasks", []).append(item)
            _save_local_data(local)
            return item

    async def approve_task(self, task_id: str) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                resp = await client.post(f"/rest/tasks/{task_id}/approve", headers=self.headers)
                resp.raise_for_status()
                return resp.json().get("data", {})
        except Exception:
            local = _load_local_data()
            for t in local.get("tasks", []):
                if t.get("id") == task_id:
                    t["status"] = "APPROVED"
                    t["approvedAt"] = datetime.now(timezone.utc).isoformat()
                    _save_local_data(local)
                    return {"task": t, "status": "APPROVED", "message": "Task approved locally"}
            return {"status": "APPROVED", "message": "Task approved locally"}

    # --- Vector Database Semantic Search ---
    async def semantic_search(self, query: str, limit: int = 5, object_type: Optional[str] = None) -> List[Dict[str, Any]]:
        payload = {"query": query, "limit": limit, "objectType": object_type}
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                resp = await client.post("/rest/semantic-search", json=payload, headers=self.headers)
                resp.raise_for_status()
                return resp.json().get("data", {}).get("matches", [])
        except Exception:
            from .semantic_engine import semantic_search_db
            local_db = _load_local_data()
            return semantic_search_db(local_db, query, limit=limit, object_type=object_type)

    # --- Webhooks ---
    async def trigger_webhook(self, event: str, data: Dict[str, Any]) -> Dict[str, Any]:
        payload = {"event": event, "data": data}
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            resp = await client.post("/rest/webhooks", json=payload, headers=self.headers)
            resp.raise_for_status()
            return resp.json()

    # --- Enterprise Workforce & Departments ---
    async def list_departments(self) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            resp = await client.get("/rest/departments", headers=self.headers)
            resp.raise_for_status()
            return resp.json().get("data", {}).get("departments", [])

    async def list_employees(self, department_id: Optional[str] = None, role: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {}
        if department_id:
            params["departmentId"] = department_id
        if role:
            params["role"] = role
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            resp = await client.get("/rest/employees", params=params, headers=self.headers)
            resp.raise_for_status()
            return resp.json().get("data", {}).get("employees", [])

    async def get_employee(self, employee_id: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            resp = await client.get(f"/rest/employees/{employee_id}", headers=self.headers)
            resp.raise_for_status()
            return resp.json().get("data", {}).get("employee", {})

    async def assign_lead(self, employee_id: str, opportunity_id: str) -> Dict[str, Any]:
        payload = {"opportunityId": opportunity_id}
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            resp = await client.post(f"/rest/employees/{employee_id}/assign-lead", json=payload, headers=self.headers)
            resp.raise_for_status()
            return resp.json().get("data", {})

    async def auto_assign_lead(self, opportunity_id: str, required_skill: str = "Chinese_LLM") -> Dict[str, Any]:
        payload = {"opportunityId": opportunity_id, "requiredSkill": required_skill}
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            resp = await client.post("/rest/auto-assign-lead", json=payload, headers=self.headers)
            resp.raise_for_status()
            return resp.json().get("data", {})

    # --- Enterprise Background Jobs ---
    async def submit_job(
        self,
        job_type: str,
        payload: Optional[Dict[str, Any]] = None,
        priority: str = "NORMAL",
        submitted_by: str = "emp-101",
        department_id: str = "dept-sales",
    ) -> Dict[str, Any]:
        data = {
            "jobType": job_type,
            "payload": payload or {},
            "priority": priority,
            "submittedByEmployeeId": submitted_by,
            "departmentId": department_id,
        }
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            resp = await client.post("/rest/jobs", json=data, headers=self.headers)
            resp.raise_for_status()
            return resp.json().get("data", {}).get("job", {})

    async def list_jobs(self, status: Optional[str] = None, job_type: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {}
        if status:
            params["status"] = status
        if job_type:
            params["jobType"] = job_type
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            resp = await client.get("/rest/jobs", params=params, headers=self.headers)
            resp.raise_for_status()
            return resp.json().get("data", {}).get("jobs", [])

    async def get_job(self, job_id: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            resp = await client.get(f"/rest/jobs/{job_id}", headers=self.headers)
            resp.raise_for_status()
            return resp.json().get("data", {}).get("job", {})

    async def cancel_job(self, job_id: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            resp = await client.post(f"/rest/jobs/{job_id}/cancel", headers=self.headers)
            resp.raise_for_status()
            return resp.json().get("data", {})

    # --- Audit Trail & Compliance ---
    async def get_audit_logs(self, actor: Optional[str] = None, entity_type: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        params = {"limit": limit}
        if actor:
            params["actor"] = actor
        if entity_type:
            params["entityType"] = entity_type
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            resp = await client.get("/rest/audit-logs", params=params, headers=self.headers)
            resp.raise_for_status()
            return resp.json().get("data", {})

    async def verify_audit_chain(self) -> Dict[str, Any]:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            resp = await client.get("/rest/audit-logs/verify", headers=self.headers)
            resp.raise_for_status()
            return resp.json().get("data", {})

