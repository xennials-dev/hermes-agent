"""
Edge detection engine comparing statistical model forecasts with market implied prices.
"""

from __future__ import annotations

import logging
from typing import Optional

from ..utils import odds_to_implied_probability

logger = logging.getLogger("hermes_sports.strategy.edge")


class EdgeDetector:
    """Calculates positive expected value (+EV) and returns actionable edges."""

    def __init__(self, threshold: float = 0.025, vig_method: str = "shin"):
        self.threshold = threshold
        self.vig_method = vig_method

    def detect_edge(self, model_prob: float, odds: float) -> Optional[float]:
        """
        Calculate edge = model_prob - market_implied_prob.
        Returns edge float if >= threshold, else None.
        """
        if odds <= 1.0:
            return None

        implied_prob = odds_to_implied_probability(odds, format_type="decimal")
        edge = model_prob - implied_prob

        if edge >= self.threshold:
            return round(edge, 4)
        return None
