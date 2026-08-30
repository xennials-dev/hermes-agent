"""
Shin Probability Calculator & Multi-Method De-Vig Engine
Exact Shin (1993) / Clarke (1998) formulation:
Term: c_i = (beta_i^2) / sum(beta_k)
Condition: sum_i sqrt(z^2 + 4(1-z) * c_i) = 2 - z
True Probability: p_i = (sqrt(z^2 + 4(1-z) * c_i) - z) / (2 * (1-z))
"""

import math
from dataclasses import dataclass
from typing import Dict, List
from ..odds_ingestion.models import MarketData, Quote


@dataclass
class DeVIgResult:
    method: str
    true_probabilities: Dict[str, float]
    insider_fraction_z: float
    raw_overround: float
    is_valid: bool
    warnings: List[str]


class ShinProbabilityCalculator:
    """
    High-precision probability extraction engine using Shin's market microstructure model
    with exact Newton-Raphson solver and Shin-Shortcut acceleration.
    """

    def __init__(self, tolerance: float = 1e-7, max_iterations: int = 100):
        self.tolerance = tolerance
        self.max_iterations = max_iterations

    def calculate_shin_shortcut(self, market: MarketData) -> DeVIgResult:
        """
        Solves for z in Shin's model:
        c_i = (beta_i^2) / sum(beta_k)
        sum_i sqrt(z^2 + 4(1-z) * c_i) = 2 - z
        """
        quotes = market.quotes
        n = len(quotes)
        warnings = []

        if n < 2:
            return DeVIgResult("Shin", {}, 0.0, 0.0, False, ["Market requires at least 2 quotes."])

        # Implied raw probabilities (beta_i = 1 / decimal_odds)
        betas = [1.0 / q.decimal_odds for q in quotes]
        sum_betas = sum(betas)

        if sum_betas < 1.0:
            warnings.append(f"Negative vig / Arbitrage condition detected (Overround: {sum_betas:.4f})")
        elif sum_betas > 1.25:
            warnings.append(f"Extreme bookmaker juice/vig detected (Overround: {sum_betas:.4f})")

        # Shin c_i terms: c_i = (beta_i^2) / sum_betas
        c_terms = [(b**2) / sum_betas for b in betas]

        # Initial estimate for z: z0 = (sum_betas - 1) / (sum(sqrt(betas)) - 1) or bounded
        sqrt_sum = sum(math.sqrt(b) for b in betas)
        if sqrt_sum > 1.0 and sum_betas > 1.0:
            z0 = min(0.4, (sum_betas - 1.0) / (sqrt_sum - 1.0))
        else:
            z0 = 0.01

        z = max(0.0, min(z0, 0.5))

        # Newton-Raphson solver for exact z: f(z) = sum(sqrt(z^2 + 4(1-z)*c_i)) + z - 2 = 0
        for _ in range(self.max_iterations):
            f_val = z - 2.0
            f_prime = 1.0

            for c in c_terms:
                radicand = max(1e-12, z**2 + 4.0 * (1.0 - z) * c)
                sqrt_val = math.sqrt(radicand)
                f_val += sqrt_val
                # Derivative of sqrt(z^2 + 4(1-z)c) w.r.t z is (2z - 4c) / (2*sqrt(...)) = (z - 2c) / sqrt(...)
                f_prime += (z - 2.0 * c) / sqrt_val

            if abs(f_val) < self.tolerance:
                break

            if abs(f_prime) > 1e-12:
                z_next = z - f_val / f_prime
                z = max(0.0, min(z_next, 0.999))
            else:
                break

        # Calculate fair probabilities p_i = (sqrt(z^2 + 4(1-z)*c_i) - z) / (2*(1-z))
        probs = []
        if z >= 0.99 or abs(1.0 - z) < 1e-6:
            probs = [b / sum_betas for b in betas]
        else:
            denom = 2.0 * (1.0 - z)
            for c in c_terms:
                radicand = max(0.0, z**2 + 4.0 * (1.0 - z) * c)
                p = (math.sqrt(radicand) - z) / denom
                probs.append(max(0.0, p))

        # Strict sum-to-1 normalization
        total_p = sum(probs)
        if total_p > 0:
            normalized_probs = {q.outcome_id: (p / total_p) for q, p in zip(quotes, probs)}
        else:
            normalized_probs = {q.outcome_id: (1.0 / n) for q in quotes}

        return DeVIgResult(
            method="Shin",
            true_probabilities=normalized_probs,
            insider_fraction_z=round(z, 6),
            raw_overround=round(sum_betas, 4),
            is_valid=True,
            warnings=warnings
        )

    def calculate_power_devig(self, market: MarketData) -> DeVIgResult:
        """Solves for k such that sum((1/d_i)^k) = 1.0."""
        quotes = market.quotes
        betas = [1.0 / q.decimal_odds for q in quotes]
        sum_betas = sum(betas)

        low, high = 1.0, 5.0 if sum_betas > 1.0 else 0.1
        k = 1.0
        for _ in range(self.max_iterations):
            mid = (low + high) / 2.0
            val = sum(b**mid for b in betas)
            if abs(val - 1.0) < self.tolerance:
                k = mid
                break
            if val > 1.0:
                low = mid
            else:
                high = mid

        probs = [b**k for b in betas]
        total_p = sum(probs)
        normalized_probs = {q.outcome_id: (p / total_p) for q, p in zip(quotes, probs)}

        return DeVIgResult(
            method="Power-DeVig",
            true_probabilities=normalized_probs,
            insider_fraction_z=0.0,
            raw_overround=round(sum_betas, 4),
            is_valid=True,
            warnings=[]
        )

    def calculate_multiplicative(self, market: MarketData) -> DeVIgResult:
        """Standard proportional overround reduction."""
        quotes = market.quotes
        betas = [1.0 / q.decimal_odds for q in quotes]
        sum_betas = sum(betas)
        normalized_probs = {q.outcome_id: (b / sum_betas) for q, b in zip(quotes, betas)}

        return DeVIgResult(
            method="Multiplicative",
            true_probabilities=normalized_probs,
            insider_fraction_z=0.0,
            raw_overround=round(sum_betas, 4),
            is_valid=True,
            warnings=[]
        )
