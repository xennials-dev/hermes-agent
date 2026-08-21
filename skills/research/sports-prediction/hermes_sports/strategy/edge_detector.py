"""
Edge detection engine comparing statistical model forecasts with market implied prices.
"""

from __future__ import annotations

import logging
from typing import Optional

try:
    from ..utils import odds_to_implied_probability  # type: ignore
except (ImportError, ValueError):
    from hermes_sports.utils import odds_to_implied_probability  # type: ignore

logger = logging.getLogger("hermes_sports.strategy.edge")


class EdgeDetector:
    """Calculates positive expected value (+EV) and returns actionable edges."""

    def __init__(self, threshold: float = 0.025, vig_method: str = "shin"):
        self.threshold = threshold
        self.vig_method = vig_method

    def calculate_edge(self, model_prob: float, offered_odds: float) -> Optional[float]:
        """Calculates expected edge = (model_prob * decimal_odds) - 1.0."""
        if offered_odds <= 1.0 or model_prob <= 0.0:
            return None

        edge = (model_prob * offered_odds) - 1.0
        if edge >= self.threshold:
            return edge
        return None

    def detect_edge(self, model_prob: float, offered_odds: float) -> Optional[float]:
        """Alias for calculate_edge."""
        return self.calculate_edge(model_prob, offered_odds)
