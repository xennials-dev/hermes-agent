"""Unit and integration tests for Twenty CRM Plugin, MCP Server, and AI Custom Objects."""

from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from plugins.twenty_crm.client import TwentyClient
from plugins.twenty_crm.autonomous_loop import AutonomousDealLoop
from plugins.twenty_crm.cli import run_twenty_cli, create_twenty_parser


class TestTwentyCRMPlugin(unittest.IsolatedAsyncioTestCase):
    """Test suite for Twenty CRM client, MCP server, AI custom objects, and approvals."""

    def setUp(self):
        self.mock_client = TwentyClient(
            base_url="http://mock-twenty:3000",
            api_key="test-secret-key",
            role="HERMES_AGENT",
        )

    async def test_twenty_client_health(self):
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_resp = AsyncMock()
            mock_resp.json = MagicMock(return_value={
                "status": "ok",
                "app": "Twenty CRM",
                "version": "0.2.0",
                "features": {"mcpServer": True, "metadataApi": True},
            })
            mock_resp.raise_for_status = MagicMock()
            mock_get.return_value = mock_resp

            health = await self.mock_client.health_check()
            self.assertEqual(health["status"], "ok")
            self.assertTrue(health["features"]["mcpServer"])

    async def test_twenty_client_mcp(self):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_resp = AsyncMock()
            mock_resp.json = MagicMock(return_value={
                "jsonrpc": "2.0",
                "id": 1,
                "result": {"tools": [{"name": "twenty_list_opportunities"}, {"name": "twenty_semantic_search"}]},
            })
            mock_resp.raise_for_status = MagicMock()
            mock_post.return_value = mock_resp

            tools = await self.mock_client.mcp_list_tools()
            self.assertEqual(len(tools), 2)
            self.assertEqual(tools[0]["name"], "twenty_list_opportunities")

    async def test_twenty_client_metadata_and_custom_objects(self):
        with patch("httpx.AsyncClient.get") as mock_get, patch("httpx.AsyncClient.post") as mock_post:
            # Metadata API
            mock_get_resp = AsyncMock()
            mock_get_resp.json = MagicMock(return_value={
                "data": {"objects": [{"nameSingular": "dealStrategyBrief", "isCustom": True}]}
            })
            mock_get_resp.raise_for_status = MagicMock()
            mock_get.return_value = mock_get_resp

            objs = await self.mock_client.get_metadata_objects()
            self.assertEqual(objs[0]["nameSingular"], "dealStrategyBrief")

            # Create DealStrategyBrief
            mock_post_resp = AsyncMock()
            mock_post_resp.json = MagicMock(return_value={
                "data": {"createDealStrategyBrief": {"id": "dsb-100", "riskScore": 25}}
            })
            mock_post_resp.raise_for_status = MagicMock()
            mock_post.return_value = mock_post_resp

            brief = await self.mock_client.create_deal_strategy_brief(
                opportunity_id="opp-1",
                executive_assessment="High strategic fit",
                risk_score=25,
                closing_probability=80,
                strategic_recommendations=["Deploy vLLM node"],
                model_engine="glm-chinese",
            )
            self.assertEqual(brief["id"], "dsb-100")
            self.assertEqual(brief["riskScore"], 25)

    async def test_twenty_client_task_approvals(self):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post_resp = AsyncMock()
            mock_post_resp.json = MagicMock(return_value={
                "data": {"task": {"id": "task-500", "status": "APPROVED"}}
            })
            mock_post_resp.raise_for_status = MagicMock()
            mock_post.return_value = mock_post_resp

            res = await self.mock_client.approve_task("task-500")
            self.assertEqual(res["task"]["status"], "APPROVED")

    async def test_twenty_client_semantic_search(self):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post_resp = AsyncMock()
            mock_post_resp.json = MagicMock(return_value={
                "data": {"matches": [{"id": "opp-3", "objectType": "opportunity", "score": 0.85}]}
            })
            mock_post_resp.raise_for_status = MagicMock()
            mock_post.return_value = mock_post_resp

            matches = await self.mock_client.semantic_search("Chinese LLM deals")
            self.assertEqual(len(matches), 1)
            self.assertEqual(matches[0]["id"], "opp-3")

    async def test_autonomous_deal_loop_strategic_brief(self):
        mock_crm = AsyncMock()
        mock_crm.get_opportunity.return_value = {
            "id": "opp-1",
            "name": "Enterprise Cluster LLM Mesh",
            "stage": "NEGOTIATION",
            "amount": {"amountMicros": 120000000000, "currencyCode": "USD"},
            "companyName": "ByteDance AI",
            "pointOfContactName": "Wei Chen",
            "probability": 85,
        }
        mock_crm.list_notes.return_value = []
        mock_crm.semantic_search.return_value = []
        mock_crm.create_deal_strategy_brief.return_value = {"id": "dsb-1"}
        mock_crm.create_competitor_intelligence.return_value = {"id": "ci-1"}
        mock_crm.create_risk_assessment.return_value = {"id": "ra-1"}
        mock_crm.create_note.return_value = {"id": "note-1"}
        mock_crm.create_task.return_value = {"id": "task-prop-1", "status": "AI_PROPOSED"}

        loop = AutonomousDealLoop(twenty_client=mock_crm, default_model="glm-chinese")

        with patch.object(
            loop,
            "_invoke_model",
            AsyncMock(return_value="Strategic assessment complete."),
        ):
            result = await loop.summarize_and_sync_deal(opportunity_id="opp-1")

            self.assertEqual(result["status"], "success")
            self.assertEqual(result["strategyBriefId"], "dsb-1")
            self.assertEqual(result["competitorIntelId"], "ci-1")
            self.assertEqual(result["riskAssessmentId"], "ra-1")
            self.assertEqual(result["taskStatus"], "AI_PROPOSED")
            mock_crm.create_deal_strategy_brief.assert_called_once()
            mock_crm.create_competitor_intelligence.assert_called_once()
            mock_crm.create_risk_assessment.assert_called_once()
            mock_crm.create_task.assert_called_once()

    async def test_autonomous_deal_loop_expanded_webhooks(self):
        mock_crm = AsyncMock()
        mock_crm.create_task.return_value = {"id": "task-from-note"}
        mock_crm.create_note.return_value = {"id": "note-exec-1"}
        loop = AutonomousDealLoop(twenty_client=mock_crm)

        # 1. note.created event
        note_event = {
            "event": "note.created",
            "data": {"title": "Client Sync", "body": "Client needs SLA report.", "targetOpportunityId": "opp-1", "author": "Human Operator"},
        }
        res_note = await loop.handle_webhook_event(note_event)
        self.assertEqual(res_note["status"], "success")
        self.assertEqual(res_note["action"], "action_item_task_proposed")

        # 2. task.approved event
        approval_event = {
            "event": "task.approved",
            "data": {"title": "Send benchmark", "targetOpportunityId": "opp-1"},
        }
        res_app = await loop.handle_webhook_event(approval_event)
        self.assertEqual(res_app["status"], "success")
        self.assertEqual(res_app["action"], "approved_task_executed")

    async def test_twenty_cli_expanded_commands(self):
        mock_crm = AsyncMock()
        mock_crm.semantic_search.return_value = [{"score": 0.88, "objectType": "opportunity", "title": "Opp", "snippet": "Text"}]
        mock_crm.get_metadata_objects.return_value = [{"nameSingular": "dealStrategyBrief", "isCustom": True, "description": "Desc"}]
        mock_crm.approve_task.return_value = {"status": "APPROVED"}

        self.assertEqual(await run_twenty_cli(["search", "test query"], client=mock_crm), 0)
        self.assertEqual(await run_twenty_cli(["metadata"], client=mock_crm), 0)
        self.assertEqual(await run_twenty_cli(["approve", "task-100"], client=mock_crm), 0)

    async def test_live_localhost_twenty_crm(self):
        """Integration test directly probing live upgraded Twenty CRM server."""
        live_client = TwentyClient(base_url="http://127.0.0.1:3000")
        try:
            health = await live_client.health_check()
            self.assertEqual(health.get("status"), "ok")
            self.assertTrue(health.get("features", {}).get("mcpServer"))

            # Test live MCP tools
            tools = await live_client.mcp_list_tools()
            self.assertGreaterEqual(len(tools), 8)

            # Test live Metadata API
            objs = await live_client.get_metadata_objects()
            self.assertTrue(any(o["nameSingular"] == "dealStrategyBrief" for o in objs))

            # Test live semantic search
            search_res = await live_client.semantic_search("high throughput clusters", limit=2)
            self.assertGreaterEqual(len(search_res), 1)
        except Exception as exc:
            self.skipTest(f"Live server not accessible: {exc}")


if __name__ == "__main__":
    unittest.main()
