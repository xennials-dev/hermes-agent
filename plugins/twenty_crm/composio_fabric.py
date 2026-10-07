"""Composio Universal API Fabric for Twenty CRM & Hermes Agent.

Provides standardized B2B tool execution across 100+ platforms (Slack, Linear,
Gmail, Google Drive, GitHub) for automated action dispatch upon CRM lifecycle
events and task approvals. Supports live Composio API execution when COMPOSIO_API_KEY
is provided, or an auditable mock fabric writing to storage/composio_audit.jsonl.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

import httpx

logger = logging.getLogger(__name__)

COMPOSIO_BASE_URL = os.environ.get("COMPOSIO_BASE_URL", "https://backend.composio.dev/api/v1")
AUDIT_LOG_FILE = Path(__file__).resolve().parent.parent.parent / "twenty_crm" / "storage" / "composio_audit.jsonl"


class ComposioFabric:
    """Universal API fabric for dispatching external B2B operations."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("COMPOSIO_API_KEY", "")
        self.is_mock = not bool(self.api_key)
        self.audit_log_path = AUDIT_LOG_FILE

    def _record_audit(self, action: str, app: str, payload: Dict[str, Any], status: str = "SUCCESS") -> Dict[str, Any]:
        """Appends action record to audit log."""
        record = {
            "id": f"comp-{uuid.uuid4().hex[:10]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "app": app,
            "status": status,
            "mode": "MOCK" if self.is_mock else "LIVE",
            "payload": payload,
        }
        try:
            self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.audit_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            logger.warning("Failed to record Composio audit log: %s", e)
        return record

    async def execute_action(self, action_name: str, app_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Executes a Composio action either via live API or mock engine."""
        if self.is_mock:
            return self._record_audit(action_name, app_name, params, status="MOCK_EXECUTED")

        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        url = f"{COMPOSIO_BASE_URL.rstrip('/')}/actions/{action_name}/execute"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json={"input": params}, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                self._record_audit(action_name, app_name, params, status="SUCCESS")
                return {"success": True, "result": data}
        except Exception as e:
            logger.error("Composio action %s failed: %s", action_name, e)
            self._record_audit(action_name, app_name, params, status=f"FAILED: {e}")
            return {"success": False, "error": str(e)}

    # --- Standardized B2B Integrations ---

    async def send_slack_notification(self, channel: str, message: str) -> Dict[str, Any]:
        """Dispatches notification to Slack channel via Composio SLACK_CHAT_POST_MESSAGE."""
        return await self.execute_action(
            action_name="SLACK_CHAT_POST_MESSAGE",
            app_name="slack",
            params={"channel": channel, "text": message},
        )

    async def create_linear_issue(self, team_id: str, title: str, description: str, priority: int = 1) -> Dict[str, Any]:
        """Creates Linear issue via Composio LINEAR_CREATE_ISSUE."""
        return await self.execute_action(
            action_name="LINEAR_CREATE_ISSUE",
            app_name="linear",
            params={"teamId": team_id, "title": title, "description": description, "priority": priority},
        )

    async def send_gmail(self, recipient: str, subject: str, body: str) -> Dict[str, Any]:
        """Sends email via Composio GMAIL_SEND_EMAIL."""
        return await self.execute_action(
            action_name="GMAIL_SEND_EMAIL",
            app_name="gmail",
            params={"recipientEmail": recipient, "subject": subject, "body": body},
        )

    async def upload_google_drive_document(self, filename: str, content: str) -> Dict[str, Any]:
        """Creates document on Google Drive via Composio GOOGLEDRIVE_CREATE_FILE."""
        return await self.execute_action(
            action_name="GOOGLEDRIVE_CREATE_FILE",
            app_name="google_drive",
            params={"name": filename, "fileContent": content},
        )

    async def dispatch_task_approval_actions(self, task_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Orchestrates cross-app B2B execution when an AI_PROPOSED task is approved in Twenty CRM."""
        title = task_data.get("title", "Approved AI Task")
        body = task_data.get("body", "")
        task_id = task_data.get("id", "task-unknown")

        results = []

        # 1. Post notification to Slack sales engineering channel
        slack_msg = (
            f":white_check_mark: *Twenty CRM AI Task Approved*\n"
            f"*Task ID*: `{task_id}`\n"
            f"*Title*: {title}\n"
            f"*Context*: {body[:250]}..."
        )
        res_slack = await self.send_slack_notification(channel="#sales-deals", message=slack_msg)
        results.append({"platform": "slack", "result": res_slack})

        # 2. If task involves deliverables, sync to Linear
        if any(kw in title.lower() for kw in ("benchmark", "deliver", "spec", "sla", "engineering")):
            res_linear = await self.create_linear_issue(
                team_id="ENG",
                title=f"[CRM Task] {title}",
                description=f"Automated issue created from approved Twenty CRM task {task_id}.\n\n{body}",
                priority=1,
            )
            results.append({"platform": "linear", "result": res_linear})

        return results

    def get_audit_trail(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns recent Composio action logs."""
        if not self.audit_log_path.exists():
            return []
        records = []
        try:
            with open(self.audit_log_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        records.append(json.loads(line))
        except Exception:
            pass
        return records[-limit:]
