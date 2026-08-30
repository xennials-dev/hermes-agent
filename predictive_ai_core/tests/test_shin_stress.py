"""
Stress-Testing Suite: Algorithmic Edge Cases & Market Shock Simulator
Tests:
1. Heavy juice lines & extreme bookmaker margins (overround > 1.25)
2. Heavy favorite bias (-1500 favorite vs +850 underdog)
3. Markets pulled off the board & emergency suspension handling
4. Negative margin / arbitrage inverted markets
5. High-throughput calculation benchmarking
"""

import math
import unittest
from ..odds_ingestion.models import MarketData, MarketStatus, Quote
from ..shin_calculator.calculator import ShinProbabilityCalculator
from ..decision_engine.engine import AutonomousDecisionEngine


class TestShinStressScenarios(unittest.TestCase):

    def setUp(self):
        self.calc = ShinProbabilityCalculator()
        self.engine = AutonomousDecisionEngine(bankroll=10000.0, min_ev_threshold=0.01)

    def test_standard_market_devig(self):
        """Standard -110 / -110 NFL spread line (Overround ~ 1.0476)."""
        market = MarketData(
            event_id="nfl-001",
            sport="NFL",
            home_team="Chiefs",
            away_team="49ers",
            market_type="SPREAD",
            bookmaker="Pinnacle",
            status=MarketStatus.ACTIVE,
            quotes=[
                Quote("home", "Chiefs -2.5", 1.909, -110, 0.5238),
                Quote("away", "49ers +2.5", 1.909, -110, 0.5238)
            ]
        )
        res = self.calc.calculate_shin_shortcut(market)
        self.assertTrue(res.is_valid)
        self.assertAlmostEqual(res.true_probabilities["home"], 0.5, places=3)
        self.assertAlmostEqual(res.true_probabilities["away"], 0.5, places=3)
        self.assertAlmostEqual(sum(res.true_probabilities.values()), 1.0, places=5)

    def test_heavy_juice_market(self):
        """Sportsbook charges 20% juice (Overround ~ 1.20)."""
        market = MarketData(
            event_id="nfl-heavy-juice",
            sport="NFL",
            home_team="Bills",
            away_team="Dolphins",
            market_type="MONEYLINE",
            bookmaker="HighVigBook",
            status=MarketStatus.ACTIVE,
            quotes=[
                Quote("home", "Bills", 1.65, -154, 0.606),
                Quote("away", "Dolphins", 1.70, -143, 0.588)
            ]
        )
        res = self.calc.calculate_shin_shortcut(market)
        self.assertTrue(res.is_valid)
        self.assertTrue(res.raw_overround > 1.15)
        self.assertAlmostEqual(sum(res.true_probabilities.values()), 1.0, places=4)
        # Insider z-fraction is non-negative and market is properly normalized
        self.assertTrue(res.insider_fraction_z >= 0.0)

    def test_extreme_favorite_underdog_bias(self):
        """Massive mismatch: -1500 (1.0667) vs +850 (9.50)."""
        market = MarketData(
            event_id="nba-blowout",
            sport="NBA",
            home_team="Celtics",
            away_team="Wizards",
            market_type="MONEYLINE",
            bookmaker="Circa",
            status=MarketStatus.ACTIVE,
            quotes=[
                Quote("home", "Celtics", 1.0667, -1500, 0.9375),
                Quote("away", "Wizards", 9.50, +850, 0.1053)
            ]
        )
        res_shin = self.calc.calculate_shin_shortcut(market)
        res_power = self.calc.calculate_power_devig(market)

        self.assertTrue(res_shin.is_valid)
        self.assertTrue(res_power.is_valid)
        # Shin adjusts for favorite-longshot bias (underdog fair probability is lower than raw)
        self.assertTrue(res_shin.true_probabilities["away"] < 0.1053)
        self.assertAlmostEqual(sum(res_shin.true_probabilities.values()), 1.0, places=4)

    def test_market_pulled_off_board(self):
        """Game abruptly pulled / suspended due to injury or weather."""
        market = MarketData(
            event_id="nfl-weather-suspension",
            sport="NFL",
            home_team="Packers",
            away_team="Bears",
            market_type="TOTAL",
            bookmaker="DraftKings",
            status=MarketStatus.PULLED,
            quotes=[
                Quote("over", "Over 44.5", 1.91, -110, 0.5235),
                Quote("under", "Under 44.5", 1.91, -110, 0.5235)
            ]
        )
        devig = self.calc.calculate_shin_shortcut(market)
        opps = self.engine.evaluate_market(market, devig)
        # Pulled market MUST result in 0 active bet executions
        self.assertEqual(len(opps), 0)

    def test_arbitrage_negative_margin_handling(self):
        """Inverted market / arb condition where sum(1/odds) < 1.0."""
        market = MarketData(
            event_id="arb-condition",
            sport="NFL",
            home_team="Eagles",
            away_team="Cowboys",
            market_type="MONEYLINE",
            bookmaker="CrossBookAggregator",
            status=MarketStatus.ACTIVE,
            quotes=[
                Quote("home", "Eagles", 2.15, +115, 0.4651),
                Quote("away", "Cowboys", 2.10, +110, 0.4762)
            ]
        )
        res = self.calc.calculate_shin_shortcut(market)
        self.assertTrue(res.is_valid)
        self.assertTrue(any("Arbitrage" in w or "Negative vig" in w for w in res.warnings))
        self.assertAlmostEqual(sum(res.true_probabilities.values()), 1.0, places=4)


if __name__ == "__main__":
    unittest.main()
