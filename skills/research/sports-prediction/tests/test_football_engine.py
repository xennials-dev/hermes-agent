"""
Unit and integration tests for FootballCLVEngine and Key Number Evaluators.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add root
sports_root = Path(__file__).resolve().parent.parent
if str(sports_root) not in sys.path:
    sys.path.insert(0, str(sports_root))

from hermes_sports.football_engine import FootballCLVEngine, FootballKeyNumberEvaluator
from hermes_sports.vig import VigStripper


def test_key_number_weighting():
    # Crossing key number 3 (-3.5 to -2.5) -> weighted up heavily
    weighted_edge = FootballKeyNumberEvaluator.calculate_weighted_edge(-2.5, -3.5, 0.035, is_cfb=False)
    assert weighted_edge > 0.035
    assert round(weighted_edge, 4) == round(0.035 * (1.0 + 1.5), 4)

    # Dead number crossing (-5.5 to -4.5) -> retains raw edge
    dead_edge = FootballKeyNumberEvaluator.calculate_weighted_edge(-4.5, -5.5, 0.035, is_cfb=False)
    assert dead_edge == 0.035


def test_football_clv_engine_scan():
    engine = FootballCLVEngine(sharp_anchors=["pinnacle"], min_ev_edge=0.02)
    events = engine.fetch_live_odds(sport="americanfootball_nfl")
    assert len(events) > 0

    alerts = engine.scan_market_discrepancies(events, sport_key="americanfootball_nfl")
    assert len(alerts) >= 2

    # Check prop alert
    prop_alert = next((a for a in alerts if a["type"] == "prop"), None)
    assert prop_alert is not None
    assert prop_alert["player"] == "Patrick Mahomes"
    assert prop_alert["ev_edge"] > 0.02
    assert prop_alert["math_method"] == "logarithmic"

    # Check spread alert
    spread_alert = next((a for a in alerts if a["type"] == "spread"), None)
    assert spread_alert is not None
    assert spread_alert["team"] == "Kansas City Chiefs"
    assert spread_alert["ev_edge"] > 0.02


def test_telegram_mock_alert():
    engine = FootballCLVEngine(sharp_anchors=["pinnacle"])
    sample_alert = {
        "type": "prop",
        "market": "player_pass_yds",
        "player": "Patrick Mahomes",
        "matchup": "Baltimore Ravens @ Kansas City Chiefs",
        "line": 268.5,
        "side": "OVER",
        "retail_book": "DraftKings",
        "retail_odds": 105,
        "sharp_book": "pinnacle",
        "sharp_odds": -135,
        "fair_probability": 0.5525,
        "ev_edge": 0.1327,
        "clv_edge": 17.77,
        "math_method": "logarithmic",
    }
    sent = engine.send_telegram_alert(sample_alert)
    assert sent is True


if __name__ == "__main__":
    tests = [
        ("Key Number Weighting", test_key_number_weighting),
        ("Football CLV Engine Sweep", test_football_clv_engine_scan),
        ("Telegram Alert Formatter", test_telegram_mock_alert),
    ]

    print("Running Football CLV Engine test suite...")
    for name, fn in tests:
        fn()
        print(f"  [PASS] {name}")
    print("\nAll Football Engine tests passed successfully!")
