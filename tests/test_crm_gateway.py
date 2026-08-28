import json
import pytest
from tools.crm_tool import crm_manage
from tui_gateway.methods_crm import _load_leads, _save_leads


def test_crm_tool_list_and_create(tmp_path, monkeypatch):
    test_storage = tmp_path / "leads.json"
    monkeypatch.setattr("tools.crm_tool._get_crm_storage", lambda: test_storage)

    # Test initial listing
    res_raw = crm_manage(action="list")
    res = json.loads(res_raw)
    assert res["status"] == "success"
    initial_count = res["count"]

    # Test creating lead
    create_raw = crm_manage(
        action="create",
        name="Global AI Contract",
        partner_name="Tech Solutions Ltd",
        email="bizdev@techsolutions.com",
        expected_revenue=50000.0,
        stage="qualified",
    )
    create_res = json.loads(create_raw)
    assert create_res["status"] == "success"
    assert create_res["lead"]["name"] == "Global AI Contract"
    assert create_res["lead"]["expected_revenue"] == 50000.0

    # Test updating stage
    lead_id = create_res["lead"]["id"]
    update_raw = crm_manage(action="update_stage", lead_id=lead_id, stage="won")
    update_res = json.loads(update_raw)
    assert update_res["status"] == "success"
    assert update_res["lead"]["stage_id"] == "won"
    assert update_res["lead"]["probability"] == 100
