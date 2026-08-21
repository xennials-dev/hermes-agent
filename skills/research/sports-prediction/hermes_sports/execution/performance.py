"""
Performance evaluation and ROI calculation for historical bets.
"""

from __future__ import annotations

import logging
import sqlite3
from typing import Any, Dict

logger = logging.getLogger("hermes_sports.execution.performance")


class PerformanceEvaluator:
    """Computes win rates, ROI, net profit, and average edge from SQLite database."""

    def __init__(self, db_path: str = "data/sports_betting.db"):
        self.db_path = db_path

    def get_summary_report(self) -> Dict[str, Any]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*), SUM(stake), AVG(edge), AVG(odds) FROM bets")
        total_bets, total_staked, avg_edge, avg_odds = cursor.fetchone()

        total_bets = total_bets or 0
        total_staked = total_staked or 0.0
        avg_edge = avg_edge or 0.0
        avg_odds = avg_odds or 0.0

        cursor.execute("SELECT COUNT(*) FROM bets WHERE won = 1")
        settled_wins = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM bets WHERE won IS NOT NULL")
        settled_total = cursor.fetchone()[0] or 0

        cursor.execute("SELECT SUM(payout) - SUM(stake) FROM bets WHERE won IS NOT NULL")
        net_profit = cursor.fetchone()[0] or 0.0

        win_rate = (settled_wins / settled_total * 100.0) if settled_total > 0 else 0.0
        roi = (net_profit / total_staked * 100.0) if total_staked > 0 else 0.0

        # Breakdown by sport
        cursor.execute("SELECT sport, COUNT(*), AVG(edge) FROM bets GROUP BY sport")
        by_sport = {row[0]: {"bets": row[1], "avg_edge": round(row[2] or 0.0, 4)} for row in cursor.fetchall()}

        conn.close()

        return {
            "total_bets": total_bets,
            "total_staked": round(total_staked, 2),
            "settled_bets": settled_total,
            "settled_wins": settled_wins,
            "win_rate_pct": round(win_rate, 2),
            "net_profit": round(net_profit, 2),
            "roi_pct": round(roi, 2),
            "avg_edge_pct": round(avg_edge * 100.0, 2),
            "avg_odds": round(avg_odds, 2),
            "by_sport": by_sport,
        }
