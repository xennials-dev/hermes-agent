"""
Algorithms for removing bookmaker vigorish (margin) from market odds.
Includes the Logarithmic Method (Shin-Shortcut / Power Method) for skewed/derivative markets.
"""

from __future__ import annotations

import math
from typing import List, Tuple, Union


class VigStripper:
    """
    Comprehensive suite of vigorish (margin) stripping algorithms for sports betting markets.
    """

    @staticmethod
    def american_to_implied(odds: Union[int, float]) -> float:
        """Convert American odds (+150, -110) to raw Implied Probability."""
        if odds > 0:
            return 100.0 / (float(odds) + 100.0)
        else:
            abs_odds = abs(float(odds))
            return abs_odds / (abs_odds + 100.0)

    @staticmethod
    def decimal_to_implied(odds: float) -> float:
        """Convert Decimal odds (2.10, 1.91) to raw Implied Probability."""
        return 1.0 / odds if odds > 1.0 else 0.0

    @staticmethod
    def logarithmic_method(
        over_odds: Union[int, float], under_odds: Union[int, float], is_american: bool = True
    ) -> Tuple[float, float, float]:
        """
        Logarithmic Method (Shin-Shortcut / Power Method) for heavily skewed and derivative markets.
        Accounts for the favorite-longshot bias by solving for exponent k:
            (IP_over)^k + (IP_under)^k = 1.0
        Returns: (fair_over_prob, fair_under_prob, juice)
        """
        # 1. Convert odds to raw Implied Probabilities
        if is_american or (isinstance(over_odds, int) and (over_odds > 100 or over_odds < -100)):
            ip_over = VigStripper.american_to_implied(over_odds)
            ip_under = VigStripper.american_to_implied(under_odds)
        else:
            ip_over = VigStripper.decimal_to_implied(float(over_odds))
            ip_under = VigStripper.decimal_to_implied(float(under_odds))

        overround = ip_over + ip_under
        juice = max(0.0, overround - 1.0)

        # 2. Objective function: solve for k where (ip_over^k + ip_under^k) == 1.0
        def objective(k: float) -> float:
            return ((ip_over**k) + (ip_under**k) - 1.0) ** 2

        k = 1.0
        try:
            from scipy.optimize import minimize_scalar  # type: ignore

            res = minimize_scalar(objective, bounds=(0.1, 10.0), method="bounded")
            if res.success:
                k = float(res.x)
            else:
                raise ValueError("scipy minimization did not converge")
        except Exception:
            # High-precision numerical bisection solver fallback (zero dependency)
            low, high = 0.1, 10.0
            for _ in range(60):
                mid = (low + high) / 2.0
                val = (ip_over**mid) + (ip_under**mid)
                if abs(val - 1.0) < 1e-8:
                    k = mid
                    break
                elif val > 1.0:
                    low = mid
                else:
                    high = mid
                k = mid

        # 3. Calculate final true fair probabilities
        fair_over = ip_over**k
        fair_under = ip_under**k

        # Normalize to guarantee exact 1.0 sum
        total = fair_over + fair_under
        if total > 0:
            fair_over /= total
            fair_under /= total

        return fair_over, fair_under, juice

    @staticmethod
    def multiplicative_method(
        over_odds: Union[int, float], under_odds: Union[int, float], is_american: bool = True
    ) -> Tuple[float, float, float]:
        """
        Multiplicative (Proportional) Vig Removal for highly liquid standard main markets.
        Fast O(1) calculation: fair_prob = IP / (IP_over + IP_under)
        """
        if is_american or (isinstance(over_odds, int) and (over_odds > 100 or over_odds < -100)):
            ip_over = VigStripper.american_to_implied(over_odds)
            ip_under = VigStripper.american_to_implied(under_odds)
        else:
            ip_over = VigStripper.decimal_to_implied(float(over_odds))
            ip_under = VigStripper.decimal_to_implied(float(under_odds))

        overround = ip_over + ip_under
        juice = max(0.0, overround - 1.0)

        if overround > 0:
            fair_over = ip_over / overround
            fair_under = ip_under / overround
        else:
            fair_over, fair_under = 0.5, 0.5

        return fair_over, fair_under, juice


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

    p1 = (math.sqrt(best_z**2 + 4.0 * (1.0 - best_z) * (inv1**2 / overround)) - best_z) / (2.0 * (1.0 - best_z))
    p2 = 1.0 - p1
    return [max(0.01, min(0.99, p1)), max(0.01, min(0.99, p2))]


def logarithmic_vig_removal(over_odds: Union[int, float], under_odds: Union[int, float]) -> Tuple[float, float, float]:
    """Shortcut function for VigStripper.logarithmic_method."""
    return VigStripper.logarithmic_method(over_odds, under_odds)


def remove_vig(
    odds: List[float], method: str = "auto", market_type: str = "main"
) -> List[float]:
    """
    Calculate fair vig-free outcome probabilities using intelligent market routing:
    - Derivative / Props markets (spreads_h1, player_pass_yds) -> Logarithmic Method (Shin-Shortcut)
    - Liquid main markets (moneylines) -> Multiplicative / Shin Method
    """
    # Auto-routing based on market type
    derivative_markets = {
        "derivative",
        "spreads_h1",
        "spreads_q1",
        "player_pass_yds",
        "player_anytime_td",
        "player_points",
        "props",
    }

    if (method == "logarithmic" or (method == "auto" and market_type in derivative_markets)) and len(odds) == 2:
        fair_over, fair_under, _ = VigStripper.logarithmic_method(odds[0], odds[1], is_american=False)
        return [fair_over, fair_under]

    if method in ("shin", "auto") and len(odds) == 2:
        return shin_vig_removal(odds)

    return proportional_vig_removal(odds)
