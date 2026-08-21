"""
SQLite-backed feature store for point-in-time correct snapshots.
"""

from __future__ import annotations

import datetime
import json
import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("hermes_sports.features.store")


class FeatureStore:
    """Stores and retrieves feature vectors for events and markets."""

    def __init__(self, db_path: str = "data/features.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS features (
                event_id TEXT,
                market TEXT,
                side TEXT,
                timestamp TEXT,
                features_json TEXT,
                PRIMARY KEY (event_id, market, side)
            )
            """
        )
        self.conn.commit()

    def save_features(self, event_id: str, market: str, side: str, features: Dict[str, Any]):
        features_json = json.dumps(features)
        now_ts = datetime.datetime.now().isoformat()
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO features (event_id, market, side, timestamp, features_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (event_id, market, side, now_ts, features_json),
        )
        self.conn.commit()

    def get_features(self, event_id: str, market: str, side: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT features_json FROM features WHERE event_id=? AND market=? AND side=?",
            (event_id, market, side),
        )
        row = cursor.fetchone()
        if row:
            return json.loads(row[0])
        return None

    def close(self):
        if self.conn:
            self.conn.close()
