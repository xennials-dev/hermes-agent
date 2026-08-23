"""Test script for FastAPI Multi-Agent Bridge server."""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient
from services.multi_agent_bridge.server import app

def test_bridge_endpoints():
    client = TestClient(app)

    # 1. Test Root
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["status"] == "online"
    print(" [OK] GET / -> Online")

    # 2. Test Pipeline Runner
    res = client.post("/tools/run_pipeline", json={"task": "Build local dashboard", "context": {}})
    assert res.status_code == 200
    assert res.json()["status"] == "success"
    print(" [OK] POST /tools/run_pipeline")

    # 3. Test Build Dashboard
    res = client.post("/tools/build_dashboard", json={"features": {"offline_mode": True, "agent_timelines": True}})
    assert res.status_code == 200
    assert res.json()["status"] == "success"
    print(" [OK] POST /tools/build_dashboard")

    # 4. Test Automated Tests
    res = client.post("/tools/run_tests", json={"project_path": ".", "test_type": "unit"})
    assert res.status_code == 200
    assert res.json()["report"]["status"] == "PASSED"
    print(" [OK] POST /tools/run_tests")

    # 5. Test Deploy Cloudflare
    res = client.post("/tools/deploy_cloudflare", json={"project_name": "agent-dashboard", "build_path": "./dist"})
    assert res.status_code == 200
    assert "pages.dev" in res.json()["url"]
    print(" [OK] POST /tools/deploy_cloudflare ->", res.json()["url"])

    # 6. Test Deploy Vercel
    res = client.post("/tools/deploy_vercel", json={"project_name": "agent-dashboard", "build_path": "./dist"})
    assert res.status_code == 200
    assert "vercel.app" in res.json()["url"]
    print(" [OK] POST /tools/deploy_vercel ->", res.json()["url"])

    # 7. Test Observability Logging
    res = client.post("/tools/log_event", json={"agent": "Logan", "event": "build_verified", "metadata": {"status": "ok"}})
    assert res.status_code == 200
    print(" [OK] POST /tools/log_event")

    # 8. Test Timeline
    res = client.get("/tools/get_agent_timeline")
    assert res.status_code == 200
    assert len(res.json()["events"]) >= 1
    print(" [OK] GET /tools/get_agent_timeline")

    # 9. Test Sandbox Execution
    res = client.post("/tools/sandbox_execute", json={"command": "python", "args": ["--version"]})
    assert res.status_code == 200
    print(" [OK] POST /tools/sandbox_execute")

    print("\nAll 8 Bridge Endpoints passed with 100% success!")

if __name__ == "__main__":
    test_bridge_endpoints()
