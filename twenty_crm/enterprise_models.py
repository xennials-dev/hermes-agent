"""Enterprise Data Models for Twenty CRM & Hermes Agent Fleet.

Defines:
- Department & Team hierarchy
- Employee profiles, reporting lines, capacities, and skills
- Role-based permissions (SUPER_ADMIN, DEPT_HEAD, MANAGER, EMPLOYEE, AUDITOR, HERMES_AGENT)
- Lead & task assignment algorithms
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EnterpriseRole(str, Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    DEPT_HEAD = "DEPT_HEAD"
    MANAGER = "MANAGER"
    EMPLOYEE = "EMPLOYEE"
    AUDITOR = "AUDITOR"
    HERMES_AGENT = "HERMES_AGENT"


class JobPriority(str, Enum):
    CRITICAL = "CRITICAL"   # P1: Immediate execution (executive SLA)
    HIGH = "HIGH"           # P2: Active negotiation / deal closing
    NORMAL = "NORMAL"       # P3: Daily standard operations
    LOW = "LOW"             # P4: Nightly maintenance / bulk archiving


class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class Department(BaseModel):
    id: str
    name: str
    code: str
    headEmployeeId: Optional[str] = None
    budgetTokens: int = 10_000_000
    tokensUsed: int = 0
    costAccruedUsd: float = 0.0
    createdAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Employee(BaseModel):
    id: str
    name: str
    email: str
    role: EnterpriseRole = EnterpriseRole.EMPLOYEE
    departmentId: str
    managerId: Optional[str] = None
    title: str
    quotaAnnual: float = 500_000.0
    closedWonAmount: float = 0.0
    activeDealsCount: int = 0
    maxCapacityDeals: int = 15
    skills: List[str] = Field(default_factory=list)
    isActive: bool = True
    createdAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def capacityUtilizationPct(self) -> float:
        if self.maxCapacityDeals <= 0:
            return 100.0
        return round((self.activeDealsCount / self.maxCapacityDeals) * 100, 1)


class EnterpriseJob(BaseModel):
    id: str
    jobType: str
    priority: JobPriority = JobPriority.NORMAL
    status: JobStatus = JobStatus.QUEUED
    progressPct: int = 0
    submittedByEmployeeId: Optional[str] = None
    departmentId: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retryCount: int = 0
    maxRetries: int = 3
    createdAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    startedAt: Optional[str] = None
    completedAt: Optional[str] = None
    workerId: Optional[str] = None


class AuditLogEntry(BaseModel):
    id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    actor: str                # e.g., emp-101 or HERMES_AGENT
    actorRole: str
    action: str               # CREATE, UPDATE, DELETE, AI_INFERENCE, APPROVE_TASK, ESCALATE, JOB_SUBMIT
    entityType: str           # opportunity, employee, job, note, etc.
    entityId: str
    details: Dict[str, Any] = Field(default_factory=dict)
    previousHash: str
    currentHash: str
