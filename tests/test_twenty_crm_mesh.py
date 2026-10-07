"""Unit and integration tests for Twenty CRM + n8n + Composio Autonomous Intelligence Mesh."""

from __future__ import annotations

import json
from pathlib import Path
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from plugins.twenty_crm.autonomous_loop import AutonomousDealLoop
from plugins.twenty_crm.client import TwentyClient
from plugins.twenty_crm.composio_fabric import ComposioFabric
from plugins.twenty_crm.cli import run_twenty_cli
from twenty_crm.server import _dispatch_webhook


class TestTwentyCRMMesh(unittest.IsolatedAsyncioTestCase):
    """Test suite for Twenty CRM, dedicated n8n, and Composio universal API fabric."""

    def setUp(self):
        self.mock_client = TwentyClient(
            base_url="http://mock-twenty:3000",
            api_key="test-secret-key",
            role="HERMES_AGENT",
        )
        self.composio = ComposioFabric(api_key="")  # mock mode

    async def test_composio_mock_dispatch_and_audit(self):
        """Test Composio universal API fabric dispatch in mock/audit mode."""
        res_slack = await self.composio.send_slack_notification(
            channel="#sales-deals", message="Deal ByteDance approved!"
        )
        self.assertEqual(res_slack.get("status"), "MOCK_EXECUTED")
        self.assertEqual(res_slack.get("app"), "slack")

        res_linear = await self.composio.create_linear_issue(
            team_id="ENG", title="[CRM] Deploy benchmark", description="Approved follow-up."
        )
        self.assertEqual(res_linear.get("status"), "MOCK_EXECUTED")
        self.assertEqual(res_linear.get("app"), "linear")

        # Verify audit trail
        trail = self.composio.get_audit_trail(limit=5)
        self.assertGreaterEqual(len(trail), 2)
        actions = [t.get("action") for t in trail]
        self.assertIn("SLACK_CHAT_POST_MESSAGE", actions)
        self.assertIn("LINEAR_CREATE_ISSUE", actions)

    async def test_composio_live_dispatch(self):
        """Test Composio live API execution path when API key is provided."""
        live_fabric = ComposioFabric(api_key="comp_live_token_12345")
        self.assertFalse(live_fabric.is_mock)

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_resp = AsyncMock()
            mock_resp.json = MagicMock(return_value={"execution_id": "exec-99", "status": "COMPLETED"})
            mock_resp.raise_for_status = MagicMock()
            mock_post.return_value = mock_resp

            res = await live_fabric.execute_action(
                action_name="GMAIL_SEND_EMAIL",
                app_name="gmail",
                params={"recipientEmail": "client@example.com", "subject": "Brief", "body": "Hello"},
            )
            self.assertTrue(res.get("success"))
            self.assertEqual(res.get("result", {}).get("execution_id"), "exec-99")

    async def test_autonomous_loop_task_approved_triggers_composio(self):
        """Test that task.approved lifecycle events trigger Composio multi-app execution."""
        mock_crm = MagicMock()
        mock_crm.create_note = AsyncMock(return_value={"id": "note-comp-1"})

        loop = AutonomousDealLoop(twenty_client=mock_crm, composio_fabric=self.composio)

        event_payload = {
            "event": "task.approved",
            "data": {
                "id": "task-71763ed7",
                "title": "Deliver tailored SLA benchmarking report",
                "body": "Benchmark local Chinese model latencies on vLLM clusters.",
                "targetOpportunityId": "opp-1",
            },
        }

        result = await loop.handle_webhook_event(event_payload)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("action"), "approved_task_executed")
        self.assertEqual(result.get("noteId"), "note-comp-1")

        composio_results = result.get("composioResults", [])
        self.assertEqual(len(composio_results), 2)  # slack and linear (matches "benchmark")
        platforms = [c.get("platform") for c in composio_results]
        self.assertIn("slack", platforms)
        self.assertIn("linear", platforms)

        # Ensure execution note was saved into Twenty CRM
        mock_crm.create_note.assert_called_once()
        call_kwargs = mock_crm.create_note.call_args.kwargs
        self.assertIn("Composio Dispatches", call_kwargs["body"])
        self.assertEqual(call_kwargs["opportunity_id"], "opp-1")

    async def test_server_webhook_dispatch_headers_and_payload(self):
        """Test that Twenty CRM webhook dispatch includes correlation headers for n8n."""
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_resp = AsyncMock()
            mock_post.return_value = mock_resp

            await _dispatch_webhook(
                url="http://localhost:5678/webhook/twenty-events",
                event="opportunity.created",
                record={"id": "opp-10", "name": "Tencent AI Expansion"},
            )

            mock_post.assert_called_once()
            call_kwargs = mock_post.call_args.kwargs
            payload = call_kwargs["json"]
            headers = call_kwargs["headers"]

            self.assertEqual(payload["event"], "opportunity.created")
            self.assertEqual(payload["source"], "TwentyCRM")
            self.assertTrue(payload["eventId"].startswith("evt-"))
            self.assertEqual(payload["data"]["id"], "opp-10")

            self.assertEqual(headers["X-Twenty-Event"], "opportunity.created")
            self.assertTrue(headers["X-Twenty-Event-Id"].startswith("evt-"))

    def test_n8n_workflows_valid_json_and_nodes(self):
        """Validate that n8n workflow definitions are syntactically valid and contain core nodes."""
        wf_dir = Path(__file__).resolve().parent.parent / "twenty_crm" / "n8n_workflows"

        router_file = wf_dir / "twenty_lifecycle_router.json"
        self.assertTrue(router_file.exists(), f"Router workflow missing: {router_file}")
        with open(router_file, "r", encoding="utf-8") as f:
            router_wf = json.load(f)
        self.assertEqual(router_wf["name"], "Twenty CRM Native Lifecycle Router to Hermes Agent & Composio")
        node_names = [n["name"] for n in router_wf["nodes"]]
        self.assertIn("Twenty CRM Webhook Ingestion", node_names)
        self.assertIn("Route by CRM Event", node_names)
        self.assertIn("Composio B2B Action Fabric", node_names)

        watcher_file = wf_dir / "twenty_file_watcher.json"
        self.assertTrue(watcher_file.exists(), f"Watcher workflow missing: {watcher_file}")
        with open(watcher_file, "r", encoding="utf-8") as f:
            watcher_wf = json.load(f)
        self.assertEqual(watcher_wf["name"], "Twenty CRM Inbound Contract & File Watcher")
        node_names_w = [n["name"] for n in watcher_wf["nodes"]]
        self.assertIn("Incoming File Trigger", node_names_w)
        self.assertIn("Create Note in Twenty CRM", node_names_w)

    async def test_cli_composio_and_n8n_status(self):
        """Test hermes twenty composio-status and n8n-status CLI commands."""
        # composio-status
        code_comp = await run_twenty_cli(["composio-status"], client=self.mock_client)
        self.assertEqual(code_comp, 0)

        # n8n-status
        code_n8n = await run_twenty_cli(["n8n-status"], client=self.mock_client)
        self.assertEqual(code_n8n, 0)


if __name__ == "__main__":
    unittest.main()
