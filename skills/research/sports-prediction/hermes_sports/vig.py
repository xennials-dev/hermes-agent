"""
Algorithms for removing the bookmaker vigorish (margin) from market odds.
"""

from __future__ import annotations

import math
from typing import List


def proportional_vig_removal(odds: List[float]) -> List[float]:
    """
    Remove vig proportionally across all possible market outcomes.
    Normalized fair probability = (1 / odds_i) / sum(1 / odds_j)
    """
    implied = [1.0 / o if o > 1.0 else 0.0 for o in odds]
    total_implied = sum(implied)
    if total_implied <= 0:
        return [1.0 / len(odds)] * len(odds)
    return [p / total_implied for p in implied]


def shin_vig_removal(odds: List[float]) -> List[float]:
    """
    Shin's method for vig removal in 2-way binary betting markets.
    Shin assumes a fraction z of bettors are 'insiders' with perfect information.
    """
    if len(odds) != 2 or any(o <= 1.0 for o in odds):
        return proportional_vig_removal(odds)

    o1, o2 = odds[0], odds[1]
    inv1, inv2 = 1.0 / o1, 1.0 / o2
    overround = inv1 + inv2

    if overround <= 1.0:
        return [inv1, inv2]

    # Iterative bisection search for optimal z (insider proportion parameter)
    low, high = 0.0, 0.5
    best_z = 0.0
    for _ in range(50):
        mid = (low + high) / 2.0
        # Compute Shin's implied probabilities for this z
        p1 = (math.sqrt(mid**2 + 4.0 * (1.0 - mid) * (inv1**2 / overround)) - mid) / (2.0 * (1.0 - mid))
        p2 = (math.sqrt(mid**2 + 4.0 * (1.0 - mid) * (inv2**2 / overround)) - mid) / (2.0 * (1.0 - mid))
        diff = (p1 + p2) - 1.0

        if abs(diff) < 1e-6:
            best_z = mid
            break
        elif diff > 0:
            low = mid
        else:
            high = mid
        best_z = mid

    # Final probabilities with best_z
    p1 = (math.sqrt(best_z**2 + 4.0 * (1.0 - best_z) * (inv1**2 / overround)) - best_z) / (2.0 * (1.0 - best_z))
    p2 = 1.0 - p1
    return [max(0.01, min(0.99, p1)), max(0.01, min(0.99, p2))]


def remove_vig(odds: List[float], method: str = "shin") -> List[float]:
    """Calculate fair vig-free outcome probabilities using the specified method."""
    if method == "shin" and len(odds) == 2:
        return shin_vig_removal(odds)
    return proportional_vig_removal(odds)
