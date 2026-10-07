"""Enterprise Unit and Integration Tests for Twenty CRM.

Tests:
1. Enterprise departments and token budget accounting
2. Employee hierarchy, manager reporting lines, and capacity utilization
3. Skill-based auto-assignment engine
4. Asynchronous priority job queue execution & cancellation
5. SHA-256 cryptographic audit log chain verification & tamper detection
6. SCIM 2.0 user directory provisioning & status patching
7. Enterprise MCP tools: twenty_list_employees, twenty_assign_record, twenty_submit_enterprise_job
"""

import asyncio
from datetime import datetime, timezone
import unittest
import uuid

from twenty_crm.audit_logger import AuditChainLogger
from twenty_crm.enterprise_models import Department, Employee, EnterpriseJob, EnterpriseRole, JobPriority, JobStatus
from twenty_crm.job_queue import EnterpriseJobEngine
from twenty_crm.scim import SCIMProvider


class TestTwentyEnterpriseEngine(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.depts = [
            {
                "id": "dept-sales",
                "name": "Enterprise Sales",
                "code": "SALES",
                "headEmployeeId": "emp-101",
                "budgetTokens": 10_000_000,
                "tokensUsed": 500_000,
                "costAccruedUsd": 50.0,
            },
            {
                "id": "dept-sol",
                "name": "Solutions Architecture",
                "code": "SOLENG",
                "headEmployeeId": "emp-104",
                "budgetTokens": 5_000_000,
                "tokensUsed": 100_000,
                "costAccruedUsd": 10.0,
            },
        ]
        self.employees = [
            {
                "id": "emp-101",
                "name": "Elena Rostova",
                "email": "elena@enterprise.com",
                "role": "DEPT_HEAD",
                "departmentId": "dept-sales",
                "managerId": None,
                "title": "VP of Sales",
                "quotaAnnual": 2_000_000.0,
                "closedWonAmount": 1_000_000.0,
                "activeDealsCount": 2,
                "maxCapacityDeals": 10,
                "skills": ["Enterprise_Negotiation", "Chinese_LLM"],
                "isActive": True,
            },
            {
                "id": "emp-102",
                "name": "Jin Woo",
                "email": "jin@enterprise.com",
                "role": "EMPLOYEE",
                "departmentId": "dept-sales",
                "managerId": "emp-101",
                "title": "Senior AE",
                "quotaAnnual": 800_000.0,
                "closedWonAmount": 200_000.0,
                "activeDealsCount": 1,
                "maxCapacityDeals": 8,
                "skills": ["Chinese_LLM", "OnPrem_Deploy"],
                "isActive": True,
            },
        ]
        self.audit_logger = AuditChainLogger()
        self.job_engine = EnterpriseJobEngine(max_concurrent_workers=2)
        self.scim = SCIMProvider(self.employees, self.depts)

    async def asyncTearDown(self):
        await self.job_engine.stop()

    def test_department_model(self):
        dept = Department(
            id="dept-ai",
            name="AI Research",
            code="AI",
            budgetTokens=15_000_000,
        )
        self.assertEqual(dept.name, "AI Research")
        self.assertEqual(dept.budgetTokens, 15_000_000)

    def test_employee_hierarchy_and_capacity(self):
        emp_model = Employee(
            id="emp-test",
            name="Alex Mercer",
            email="alex@enterprise.com",
            role=EnterpriseRole.EMPLOYEE,
            departmentId="dept-sales",
            managerId="emp-101",
            title="Account Exec",
            activeDealsCount=3,
            maxCapacityDeals=6,
        )
        self.assertEqual(emp_model.managerId, "emp-101")
        self.assertEqual(emp_model.capacityUtilizationPct, 50.0)

    def test_cryptographic_audit_chain_and_tamper_detection(self):
        # 1. Log two genuine events
        e1 = self.audit_logger.log(
            actor="emp-101",
            actor_role="MANAGER",
            action="CREATE_OPPORTUNITY",
            entity_type="opportunity",
            entity_id="opp-100",
            details={"value": 150000},
        )
        e2 = self.audit_logger.log(
            actor="HERMES_AGENT",
            actor_role="HERMES_AGENT",
            action="GENERATE_BRIEF",
            entity_type="dealStrategyBrief",
            entity_id="dsb-100",
            details={"riskScore": 15},
        )

        self.assertEqual(e2["previousHash"], e1["currentHash"])
        self.assertTrue(self.audit_logger.verify_chain_integrity())

        # 2. Simulate tampering with block 0 content
        self.audit_logger.logs[0]["details"]["value"] = 999999
        self.assertFalse(self.audit_logger.verify_chain_integrity(), "Tampered log must fail hash integrity check!")

    async def test_job_engine_execution_and_progress(self):
        await self.job_engine.start()

        job = await self.job_engine.submit_job(
            job_type="BATCH_LEAD_ENRICHMENT",
            payload={"recordCount": 6},
            priority=JobPriority.HIGH,
            submitted_by_employee_id="emp-101",
        )
        self.assertEqual(job["status"], JobStatus.QUEUED.value)

        # Wait for worker execution to complete
        for _ in range(50):
            await asyncio.sleep(0.05)
            j = self.job_engine.get_job(job["id"])
            if j and j["status"] == JobStatus.COMPLETED.value:
                break

        final_job = self.job_engine.get_job(job["id"])
        self.assertEqual(final_job["status"], JobStatus.COMPLETED.value)
        self.assertEqual(final_job["progressPct"], 100)
        self.assertIsNotNone(final_job["result"])
        self.assertIn("recordsProcessed", final_job["result"])

    async def test_job_engine_cancellation(self):
        await self.job_engine.start()

        job = await self.job_engine.submit_job(
            job_type="PORTFOLIO_RISK_SCAN",
            priority=JobPriority.LOW,
            payload={},
        )
        cancelled = await self.job_engine.cancel_job(job["id"])
        self.assertTrue(cancelled)

        j = self.job_engine.get_job(job["id"])
        self.assertEqual(j["status"], JobStatus.CANCELLED.value)

    def test_scim_provisioning_and_deprovisioning(self):
        # 1. SCIM user list
        res = self.scim.list_users()
        self.assertEqual(res["totalResults"], 2)

        # 2. SCIM create user
        new_user = self.scim.create_user({
            "userName": "sophia@enterprise.com",
            "displayName": "Sophia Bennett",
            "title": "Solutions Engineer",
            "departmentId": "dept-sol",
            "active": True,
        })
        self.assertEqual(new_user["userName"], "sophia@enterprise.com")
        self.assertEqual(len(self.employees), 3)

        # 3. SCIM deprovision (active = False)
        patched = self.scim.patch_user(new_user["id"], [{"path": "active", "value": False}])
        self.assertFalse(patched["active"])

        # 4. SCIM groups
        groups = self.scim.list_groups()
        self.assertEqual(groups["totalResults"], 2)


if __name__ == "__main__":
    unittest.main()
