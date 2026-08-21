"""
Paper trading execution engine and persistent SQLite logging.
"""

from __future__ import annotations

import datetime
import json
import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("hermes_sports.execution.bet_executor")


class BetExecutor:
    """Executes paper bets and persists predictions and wagers into SQLite."""

    def __init__(self, paper_trading: bool = True, db_path: str = "data/sports_betting.db"):
        self.paper_trading = paper_trading
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS bets (
                bet_id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT,
                sport TEXT,
                market TEXT,
                side TEXT,
                player TEXT,
                odds REAL,
                stake REAL,
                bookmaker TEXT,
                model_prob REAL,
                implied_prob REAL,
                edge REAL,
                timestamp TEXT,
                status TEXT,
                won INTEGER DEFAULT NULL,
                payout REAL DEFAULT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT,
                sport TEXT,
                market TEXT,
                side TEXT,
                model_prob REAL,
                fair_prob REAL,
                features_json TEXT,
                timestamp TEXT
            )
            """
        )
        self.conn.commit()

    def place_bet(
        self,
        event_id: str,
        sport: str,
        market: str,
        side: str,
        odds: float,
        stake: float,
        bookmaker: str,
        model_prob: float,
        implied_prob: float,
        edge: float,
        player: Optional[str] = None,
    ) -> Dict[str, Any]:
        status = "paper" if self.paper_trading else "live"
        now_ts = datetime.datetime.now().isoformat()

        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO bets (
                event_id, sport, market, side, player, odds, stake, bookmaker,
                model_prob, implied_prob, edge, timestamp, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                sport,
                market,
                side,
                player,
                odds,
                stake,
                bookmaker,
                model_prob,
                implied_prob,
                edge,
                now_ts,
                status,
            ),
        )
        self.conn.commit()
        bet_id = cursor.lastrowid

        record = {
            "bet_id": bet_id,
            "event_id": event_id,
            "sport": sport,
            "market": market,
            "side": side,
            "player": player,
            "odds": odds,
            "stake": stake,
            "bookmaker": bookmaker,
            "model_prob": model_prob,
            "edge": edge,
            "status": status,
            "timestamp": now_ts,
        }
        logger.info(f"[{status.upper()}] Placed Bet #{bet_id}: {market} ({side}) @ {odds} | Stake: ${stake:.2f} [{bookmaker}]")
        return record

    def log_prediction(
        self,
        event_id: str,
        sport: str,
        market: str,
        side: str,
        model_prob: float,
        fair_prob: float,
        features: Dict[str, Any],
    ):
        now_ts = datetime.datetime.now().isoformat()
        feat_json = json.dumps(features)
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO predictions (event_id, sport, market, side, model_prob, fair_prob, features_json, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (event_id, sport, market, side, model_prob, fair_prob, feat_json, now_ts),
        )
        self.conn.commit()

    def close(self):
        if self.conn:
            self.conn.close()
