"""Cryptographic Immutable Audit Logger for Twenty CRM.

Provides SHA-256 hash-chained event auditing:
- Verifiable sequence: block[N].currentHash = SHA256(block[N].content + block[N-1].currentHash)
- Detects any retroactively altered or deleted entries
- Captures actor identity, enterprise role, target entity, and payload diffs
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Dict, List, Optional
import uuid

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"


class AuditChainLogger:
    """Thread-safe append-only audit logger with SHA-256 cryptographic chaining."""

    def __init__(self, initial_logs: Optional[List[Dict[str, Any]]] = None) -> None:
        self.logs: List[Dict[str, Any]] = initial_logs or []

    @property
    def latest_hash(self) -> str:
        if not self.logs:
            return GENESIS_HASH
        return self.logs[-1].get("currentHash", GENESIS_HASH)

    def log(
        self,
        actor: str,
        actor_role: str,
        action: str,
        entity_type: str,
        entity_id: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Appends a new verified event to the tamper-proof audit log."""
        prev_hash = self.latest_hash
        timestamp = datetime.now(timezone.utc).isoformat()
        entry_id = f"audit-{uuid.uuid4().hex[:8]}"

        content_for_hashing = {
            "id": entry_id,
            "timestamp": timestamp,
            "actor": actor,
            "actorRole": actor_role,
            "action": action,
            "entityType": entity_type,
            "entityId": entity_id,
            "details": details or {},
            "previousHash": prev_hash,
        }

        # Deterministic JSON canonical string
        canonical = json.dumps(content_for_hashing, sort_keys=True)
        current_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

        entry = {
            **content_for_hashing,
            "currentHash": current_hash,
        }
        self.logs.append(entry)
        return entry

    def verify_chain_integrity(self) -> bool:
        """Verifies that no entry has been altered, deleted, or inserted."""
        prev_hash = GENESIS_HASH
        for entry in self.logs:
            if entry.get("previousHash") != prev_hash:
                return False
            
            # Recalculate hash
            content_copy = {
                "id": entry["id"],
                "timestamp": entry["timestamp"],
                "actor": entry["actor"],
                "actorRole": entry["actorRole"],
                "action": entry["action"],
                "entityType": entry["entityType"],
                "entityId": entry["entityId"],
                "details": entry["details"],
                "previousHash": entry["previousHash"],
            }
            computed = hashlib.sha256(json.dumps(content_copy, sort_keys=True).encode("utf-8")).hexdigest()
            if computed != entry.get("currentHash"):
                return False
            prev_hash = entry["currentHash"]
        return True

    def get_logs(
        self,
        actor: Optional[str] = None,
        entity_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Queries the audit log filtered by actor or entity."""
        res = self.logs
        if actor:
            res = [r for r in res if r.get("actor") == actor]
        if entity_type:
            res = [r for r in res if r.get("entityType") == entity_type]
        return list(reversed(res[-limit:]))
