"""
Autonomous Decision-Making Engine: Expected Value (+EV) & Fractional Kelly Staking
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from ..odds_ingestion.models import MarketData, MarketStatus, Quote
from ..shin_calculator.calculator import DeVIgResult


@dataclass
class BettingOpportunity:
    event_id: str
    sport: str
    matchup: str
    outcome_id: str
    outcome_name: str
    offered_decimal_odds: float
    true_probability: float
    implied_probability: float
    expected_value_pct: float
    full_kelly_fraction: float
    recommended_stake_fraction: float
    recommended_stake_dollars: float
    confidence_score: float
    insider_activity_index: float
    action: str  # "BET", "PASS", "HEDGE"


class AutonomousDecisionEngine:
    """
    Evaluates de-vigged fair probabilities against live market odds
    to determine mathematical edge (+EV) and optimal stake sizing.
    """

    def __init__(
        self,
        bankroll: float = 10000.0,
        min_ev_threshold: float = 0.015,  # 1.5% minimum +EV
        fractional_kelly: float = 0.25,   # Quarter Kelly for variance shield
        max_stake_cap: float = 0.03       # Max 3.0% bankroll per position
    ):
        self.bankroll = bankroll
        self.min_ev = min_ev_threshold
        self.kelly_multiplier = fractional_kelly
        self.max_stake_cap = max_stake_cap

    def evaluate_market(
        self,
        market: MarketData,
        devig_result: DeVIgResult
    ) -> List[BettingOpportunity]:
        """
        Evaluates all quotes in a market against their Shin true probabilities.
        """
        opportunities = []

        if market.status != MarketStatus.ACTIVE:
            return []

        for quote in market.quotes:
            true_p = devig_result.true_probabilities.get(quote.outcome_id, 0.0)
            if true_p <= 0.0:
                continue

            dec_odds = quote.decimal_odds
            implied_p = quote.implied_prob

            # Expected Value formula: EV = (p * dec_odds) - 1.0
            ev_pct = (true_p * dec_odds) - 1.0

            # Kelly Criterion: f* = (b * p - q) / b where b = dec_odds - 1, q = 1 - p
            b = dec_odds - 1.0
            q = 1.0 - true_p
            full_kelly = max(0.0, (b * true_p - q) / b) if b > 0 else 0.0

            # Apply Fractional Kelly & Max Stake Cap
            frac_kelly = full_kelly * self.kelly_multiplier
            bounded_stake_fraction = min(self.max_stake_cap, frac_kelly)
            recommended_dollars = round(bounded_stake_fraction * self.bankroll, 2)

            # Confidence score factoring insider z-index
            confidence = min(1.0, max(0.0, (ev_pct * 10.0) + (devig_result.insider_fraction_z * 0.5)))

            action = "BET" if (ev_pct >= self.min_ev and recommended_dollars > 0) else "PASS"

            opp = BettingOpportunity(
                event_id=market.event_id,
                sport=market.sport,
                matchup=f"{market.away_team} @ {market.home_team}",
                outcome_id=quote.outcome_id,
                outcome_name=quote.outcome_name,
                offered_decimal_odds=dec_odds,
                true_probability=round(true_p, 4),
                implied_probability=round(implied_p, 4),
                expected_value_pct=round(ev_pct * 100.0, 2),
                full_kelly_fraction=round(full_kelly, 4),
                recommended_stake_fraction=round(bounded_stake_fraction, 4),
                recommended_stake_dollars=recommended_dollars,
                confidence_score=round(confidence, 3),
                insider_activity_index=devig_result.insider_fraction_z,
                action=action
            )
            opportunities.append(opp)

        return opportunities
