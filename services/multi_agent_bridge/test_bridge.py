"""Self-contained test script for the Multi-Agent Bridge server."""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from services.multi_agent_bridge.server import (
    execute_pipeline,
    execute_build_dashboard,
    execute_deploy,
    execute_tests,
    execute_log_event,
    get_timeline,
    execute_sandbox,
)

def test_bridge_functions():
    print("Testing Multi-Agent Bridge core functions...")

    # 1. Test Pipeline Runner
    res = execute_pipeline("Build local dashboard", {"mode": "local"})
    assert res["status"] == "success"
    print(" [OK] execute_pipeline ->", res["task_id"])

    # 2. Test Build Dashboard
    res = execute_build_dashboard({"offline_mode": True, "agent_timelines": True})
    assert res["status"] == "success"
    assert "output_path" in res
    print(" [OK] execute_build_dashboard ->", res["output_path"])

    # 3. Test Automated Tests
    res = execute_tests(".", "unit")
    assert res["status"] == "success"
    assert res["report"]["status"] == "PASSED"
    print(" [OK] execute_tests -> PASSED")

    # 4. Test Deploy Cloudflare
    res = execute_deploy("agent-dashboard", "./dist", "Cloudflare")
    assert res["status"] == "deployed"
    assert "pages.dev" in res["url"]
    print(" [OK] execute_deploy(Cloudflare) ->", res["url"])

    # 5. Test Deploy Vercel
    res = execute_deploy("agent-dashboard", "./dist", "Vercel")
    assert res["status"] == "deployed"
    assert "vercel.app" in res["url"]
    print(" [OK] execute_deploy(Vercel) ->", res["url"])

    # 6. Test Observability Logging
    res = execute_log_event("Logan", "build_verified", {"status": "ok"})
    assert res["status"] == "logged"
    print(" [OK] execute_log_event -> Logged")

    # 7. Test Timeline
    tl = get_timeline()
    assert len(tl["events"]) >= 1
    assert len(tl["timeline"]) >= 1
    print(f" [OK] get_timeline -> {len(tl['events'])} events tracked")

    # 8. Test Sandbox Execution
    res = execute_sandbox("echo", ["Hello from Sandbox"])
    assert res["status"] == "success"
    print(" [OK] execute_sandbox -> Echo verified")

    print("\n[SUCCESS] All 8 Multi-Agent Bridge functions and endpoints verified successfully!")

if __name__ == "__main__":
    test_bridge_functions()
