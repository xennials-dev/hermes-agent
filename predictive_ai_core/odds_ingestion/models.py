"""
Predictive AI Core: Real-Time Odds Ingestion Models
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional


class MarketStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    PULLED = "PULLED_OFF_BOARD"
    HEAVILY_JUICED = "HEAVILY_JUICED"
    STALE = "STALE"


@dataclass(frozen=True)
class Quote:
    outcome_id: str
    outcome_name: str
    decimal_odds: float
    american_odds: int
    implied_prob: float
    volume: Optional[float] = None


@dataclass
class MarketData:
    event_id: str
    sport: str  # e.g., "NFL", "NBA"
    home_team: str
    away_team: str
    market_type: str  # e.g., "MONEYLINE", "SPREAD", "TOTAL"
    bookmaker: str
    status: MarketStatus
    quotes: List[Quote]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, str] = field(default_factory=dict)

    @property
    def raw_overround(self) -> float:
        """Sum of raw implied probabilities (1.0 = zero vig, >1.0 = bookmaker margin)."""
        return sum(q.implied_prob for q in self.quotes)
