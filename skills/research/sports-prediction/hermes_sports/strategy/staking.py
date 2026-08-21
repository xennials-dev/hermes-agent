"""
Fractional Kelly Criterion bankroll staking and exposure management.
"""

from __future__ import annotations

import logging

logger = logging.getLogger("hermes_sports.strategy.staking")


class KellyStaking:
    """Calculates position sizing via Fractional Kelly Criterion with hard safety caps."""

    def __init__(self, kelly_fraction: float = 0.25, max_stake_pct: float = 0.02):
        self.kelly_fraction = kelly_fraction
        self.max_stake_pct = max_stake_pct

    def calculate_stake(self, bankroll: float, edge: float, odds: float) -> float:
        """
        Calculate recommended monetary wager.
        f* = (b*p - q) / b where b = decimal_odds - 1, p = win_prob, q = 1 - p.
        """
        if odds <= 1.0 or edge <= 0.0 or bankroll <= 0.0:
            return 0.0

        b = odds - 1.0
        p = (1.0 / odds) + edge  # Model estimated win probability
        q = 1.0 - p

        raw_kelly = (b * p - q) / b
        if raw_kelly <= 0.0:
            return 0.0

        fractional_kelly = raw_kelly * self.kelly_fraction
        capped_kelly = min(fractional_kelly, self.max_stake_pct)

        stake = round(bankroll * capped_kelly, 2)
        return max(0.0, stake)
