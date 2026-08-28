"""Odoo CRM JSON-RPC handlers for Hermes Agent Gateway."""

import json
import logging
from pathlib import Path
from hermes_constants import get_hermes_home
from .method_ctx import HandlerRegistry

log = logging.getLogger(__name__)

_registry = HandlerRegistry()
method = _registry.method


def register(server) -> None:
    """Bind this module's handlers onto server's globals and registry."""
    _registry.install(server)


def _get_crm_storage_file() -> Path:
    storage_dir = get_hermes_home() / "crm"
    storage_dir.mkdir(parents=True, exist_ok=True)
    return storage_dir / "leads.json"


def _load_leads() -> list[dict]:
    fp = _get_crm_storage_file()
    if fp.exists():
        try:
            return json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def _save_leads(leads: list[dict]):
    fp = _get_crm_storage_file()
    fp.write_text(json.dumps(leads, indent=2, ensure_ascii=False), encoding="utf-8")


@method("crm.list_leads")
def _(rid, params: dict) -> dict:
    """List CRM leads filtered by stage or search query."""
    stage = params.get("stage")
    query = str(params.get("query") or "").lower()
    leads = _load_leads()

    filtered = []
    for l in leads:
        if stage and l.get("stage_id") != stage:
            continue
        if query and query not in l.get("name", "").lower() and query not in l.get("email", "").lower():
            continue
        filtered.append(l)

    return {"status": "ok", "leads": filtered, "total": len(filtered)}


@method("crm.create_lead")
def _(rid, params: dict) -> dict:
    """Create a new CRM opportunity/lead."""
    name = str(params.get("name") or "").strip()
    if not name:
        return {"error": "Lead name is required"}

    leads = _load_leads()
    new_lead = {
        "id": f"crm_lead_{len(leads) + 1}",
        "name": name,
        "partner_name": params.get("partner_name", "Enterprise Client"),
        "email": params.get("email", "contact@example.com"),
        "phone": params.get("phone", ""),
        "expected_revenue": float(params.get("expected_revenue", 0.0)),
        "probability": int(params.get("probability", 20)),
        "stage_id": params.get("stage_id", "new"),
        "description": params.get("description", "Created via Hermes Agent API"),
    }
    leads.append(new_lead)
    _save_leads(leads)
    return {"status": "ok", "lead": new_lead}


@method("crm.update_stage")
def _(rid, params: dict) -> dict:
    """Update the pipeline stage of a lead."""
    lead_id = str(params.get("lead_id") or "")
    new_stage = str(params.get("stage_id") or "")

    leads = _load_leads()
    found = None
    for l in leads:
        if l.get("id") == lead_id:
            l["stage_id"] = new_stage
            if new_stage == "won":
                l["probability"] = 100
            found = l
            break

    if not found:
        return {"error": f"Lead {lead_id} not found"}

    _save_leads(leads)
    return {"status": "ok", "lead": found}
