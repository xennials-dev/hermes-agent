"""SCIM 2.0 (RFC 7643 / RFC 7644) Directory Provisioning Engine for Twenty CRM.

Enables automated enterprise employee onboarding, role mapping, and deprovisioning
from identity providers (Okta, Microsoft Entra ID, PingIdentity, Google Workspace).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import uuid


class SCIMProvider:
    """Enterprise SCIM 2.0 handler managing employee identity federation."""

    def __init__(self, db_employees: List[Dict[str, Any]], db_departments: List[Dict[str, Any]]) -> None:
        self.employees = db_employees
        self.departments = db_departments

    def list_users(self, filter_str: Optional[str] = None, start_index: int = 1, count: int = 50) -> Dict[str, Any]:
        resources = []
        for emp in self.employees:
            resources.append(self._format_scim_user(emp))

        return {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
            "totalResults": len(resources),
            "startIndex": start_index,
            "itemsPerPage": count,
            "Resources": resources,
        }

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        emp = next((e for e in self.employees if e["id"] == user_id), None)
        if not emp:
            return None
        return self._format_scim_user(emp)

    def create_user(self, scim_payload: Dict[str, Any]) -> Dict[str, Any]:
        user_name = scim_payload.get("userName") or "new.user@enterprise.com"
        name_obj = scim_payload.get("name", {})
        display_name = scim_payload.get("displayName") or f"{name_obj.get('givenName', '')} {name_obj.get('familyName', '')}".strip() or user_name

        emails = scim_payload.get("emails", [])
        email = emails[0].get("value") if emails else user_name

        emp_id = f"emp-{uuid.uuid4().hex[:6]}"
        new_emp = {
            "id": emp_id,
            "name": display_name,
            "email": email,
            "role": scim_payload.get("userType") or "EMPLOYEE",
            "departmentId": scim_payload.get("departmentId") or "dept-sales",
            "managerId": scim_payload.get("managerId") or "emp-101",
            "title": scim_payload.get("title") or "Account Representative",
            "quotaAnnual": 500000.0,
            "closedWonAmount": 0.0,
            "activeDealsCount": 0,
            "maxCapacityDeals": 15,
            "skills": scim_payload.get("skills") or ["Enterprise_Sales"],
            "isActive": scim_payload.get("active", True),
        }
        self.employees.append(new_emp)
        return self._format_scim_user(new_emp)

    def patch_user(self, user_id: str, operations: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        emp = next((e for e in self.employees if e["id"] == user_id), None)
        if not emp:
            return None

        for op in operations:
            val = op.get("value", {})
            if isinstance(val, dict):
                if "active" in val:
                    emp["isActive"] = bool(val["active"])
                if "title" in val:
                    emp["title"] = val["title"]
                if "departmentId" in val:
                    emp["departmentId"] = val["departmentId"]
            elif op.get("path") == "active":
                emp["isActive"] = bool(val)

        return self._format_scim_user(emp)

    def list_groups(self) -> Dict[str, Any]:
        resources = []
        for dept in self.departments:
            members = [
                {"value": e["id"], "display": e["name"]}
                for e in self.employees if e.get("departmentId") == dept["id"]
            ]
            resources.append({
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                "id": dept["id"],
                "displayName": dept["name"],
                "members": members,
            })
        return {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
            "totalResults": len(resources),
            "Resources": resources,
        }

    def _format_scim_user(self, emp: Dict[str, Any]) -> Dict[str, Any]:
        parts = emp["name"].split(" ", 1)
        given_name = parts[0]
        family_name = parts[1] if len(parts) > 1 else ""

        return {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "id": emp["id"],
            "userName": emp["email"],
            "name": {
                "givenName": given_name,
                "familyName": family_name,
                "formatted": emp["name"],
            },
            "displayName": emp["name"],
            "title": emp.get("title", ""),
            "userType": emp.get("role", "EMPLOYEE"),
            "active": emp.get("isActive", True),
            "emails": [{"value": emp["email"], "primary": True}],
            "department": emp.get("departmentId", ""),
            "meta": {
                "resourceType": "User",
                "location": f"/scim/v2/Users/{emp['id']}",
            },
        }
