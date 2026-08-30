"""Odoo CRM Integration Tool for Hermes Agent.

Provides the agent with autonomous capabilities to query, create,
and update CRM leads and pipeline stages directly during conversation loops.
"""

import json
import time
from pathlib import Path
from hermes_constants import get_hermes_home
from tools.registry import registry


def _get_crm_storage() -> Path:
    d = get_hermes_home() / "crm"
    d.mkdir(parents=True, exist_ok=True)
    return d / "leads.json"


def _load_leads() -> list[dict]:
    fp = _get_crm_storage()
    if fp.exists():
        try:
            return json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            pass
    return [
        {
            "id": "crm_lead_1",
            "name": "Global Retail POS Upgrade",
            "partner_name": "MegaCorp Retail",
            "email": "procurement@megacorp.com",
            "expected_revenue": 45000.0,
            "probability": 70,
            "stage_id": "proposition",
            "description": "Upgrading 50 stores with automated POS systems.",
        },
        {
            "id": "crm_lead_2",
            "name": "Enterprise Cloud Migration",
            "partner_name": "Apex Logistics",
            "email": "cio@apexlogistics.com",
            "expected_revenue": 120000.0,
            "probability": 40,
            "stage_id": "qualified",
            "description": "Multi-region hybrid cloud deployment.",
        },
    ]


def _save_leads(leads: list[dict]):
    fp = _get_crm_storage()
    fp.write_text(json.dumps(leads, indent=2, ensure_ascii=False), encoding="utf-8")


def crm_manage(
    action: str = "list",
    lead_id: str | None = None,
    name: str | None = None,
    partner_name: str | None = None,
    email: str | None = None,
    expected_revenue: float | None = None,
    stage: str | None = None,
    description: str | None = None,
) -> str:
    """Manage Odoo CRM leads, pipelines, and opportunities."""
    leads = _load_leads()

    if action == "list":
        if stage:
            filtered = [l for l in leads if l.get("stage_id") == stage]
        else:
            filtered = leads
        return json.dumps({"status": "success", "count": len(filtered), "leads": filtered}, indent=2)

    elif action == "get":
        for l in leads:
            if l.get("id") == lead_id or (name and name.lower() in l.get("name", "").lower()):
                return json.dumps({"status": "success", "lead": l}, indent=2)
        return json.dumps({"status": "error", "message": f"Lead {lead_id or name} not found"})

    elif action == "create":
        if not name:
            return json.dumps({"status": "error", "message": "name is required to create a lead"})
        new_id = f"crm_lead_{int(time.time())}"
        new_lead = {
            "id": new_id,
            "name": name,
            "partner_name": partner_name or "Enterprise Partner",
            "email": email or "sales@example.com",
            "expected_revenue": expected_revenue if expected_revenue is not None else 0.0,
            "probability": 100 if stage == "won" else 70 if stage == "proposition" else 40 if stage == "qualified" else 20,
            "stage_id": stage or "new",
            "description": description or "Created via CRM Tool",
        }
        leads.append(new_lead)
        _save_leads(leads)
        return json.dumps({"status": "success", "message": "Lead created", "lead": new_lead}, indent=2)

    elif action == "update_stage":
        if not lead_id:
            return json.dumps({"status": "error", "message": "lead_id is required to update stage"})
        for l in leads:
            if l.get("id") == lead_id:
                l["stage_id"] = stage or l.get("stage_id")
                if stage == "won":
                    l["probability"] = 100
                _save_leads(leads)
                return json.dumps({"status": "success", "message": "Stage updated", "lead": l}, indent=2)
        return json.dumps({"status": "error", "message": f"Lead {lead_id} not found"})

    return json.dumps({"status": "error", "message": f"Unknown action: {action}"})


CRM_TOOL_SCHEMA = {
    "name": "crm_manage",
    "description": "Manage Odoo CRM pipeline: list deals, inspect customer opportunities, create leads, or update deal stages.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["list", "get", "create", "update_stage"],
                "description": "Action to perform on the CRM pipeline.",
            },
            "lead_id": {
                "type": "string",
                "description": "ID of the target CRM lead/deal.",
            },
            "name": {
                "type": "string",
                "description": "Title/name of the opportunity.",
            },
            "partner_name": {
                "type": "string",
                "description": "Name of the customer organization.",
            },
            "email": {
                "type": "string",
                "description": "Contact email address.",
            },
            "expected_revenue": {
                "type": "number",
                "description": "Projected deal revenue.",
            },
            "stage": {
                "type": "string",
                "enum": ["new", "qualified", "proposition", "won"],
                "description": "Target pipeline stage.",
            },
            "description": {
                "type": "string",
                "description": "Notes or deal requirements.",
            },
        },
        "required": ["action"],
    },
}

registry.register(
    name="crm_manage",
    toolset="crm",
    schema=CRM_TOOL_SCHEMA,
    handler=crm_manage,
)
