"""
Unit and integration tests for the hermes_sports prediction suite.
Supports both pytest and standard python execution.
"""

from __future__ import annotations

import math
import shutil
import sys
import tempfile
from pathlib import Path

# Add package root to sys.path
package_root = Path(__file__).resolve().parent.parent
if str(package_root) not in sys.path:
    sys.path.insert(0, str(package_root))

from hermes_sports.config import Config, DataProviderConfig, ExecutionConfig, StrategyConfig  # type: ignore
from hermes_sports.data.mock_providers import MockContextProvider, MockOddsProvider, MockStatsProvider  # type: ignore
from hermes_sports.execution.bet_executor import BetExecutor  # type: ignore
from hermes_sports.execution.performance import PerformanceEvaluator  # type: ignore
from hermes_sports.features.feature_builder import FeatureBuilder  # type: ignore
from hermes_sports.features.feature_store import FeatureStore  # type: ignore
from hermes_sports.models.calibration import CalibratedModel  # type: ignore
from hermes_sports.models.ensemble import EnsembleModel  # type: ignore
from hermes_sports.models.logistic_model import LogisticModel  # type: ignore
from hermes_sports.models.xgb_model import XGBoostModel  # type: ignore
from hermes_sports.strategy.edge_detector import EdgeDetector  # type: ignore
from hermes_sports.strategy.staking import KellyStaking  # type: ignore
from hermes_sports.training.synthetic_data import generate_training_dataset  # type: ignore
from hermes_sports.utils import (  # type: ignore
    american_to_decimal,
    decimal_to_american,
    odds_to_implied_probability,
)
from hermes_sports.vig import remove_vig, shin_vig_removal  # type: ignore


def test_odds_conversions():
    # American to Decimal
    assert american_to_decimal(100) == 2.0
    assert round(american_to_decimal(-110), 4) == 1.9091
    assert round(american_to_decimal(150), 4) == 2.5000

    # Decimal to American
    assert decimal_to_american(2.0) == 100
    assert decimal_to_american(1.9091) == -110

    # Implied probabilities
    assert round(odds_to_implied_probability(2.0), 4) == 0.5000
    assert round(odds_to_implied_probability(1.9091), 4) == 0.5238


def test_vig_removal():
    # Symmetric odds with vig
    fair_probs = remove_vig([1.9091, 1.9091], method="shin")
    assert round(sum(fair_probs), 4) == 1.0000
    assert round(fair_probs[0], 2) == 0.50
    assert round(fair_probs[1], 2) == 0.50

    # Proportional vig removal
    fair_prop = remove_vig([1.50, 2.70], method="proportional")
    assert round(sum(fair_prop), 4) == 1.0000


def test_mock_providers():
    odds_prov = MockOddsProvider()
    events = odds_prov.get_upcoming_events("basketball_nba")
    assert len(events) > 0
    event_id = events[0]["event_id"]

    odds = odds_prov.get_current_odds(event_id, ["moneyline", "spread", "total", "player_points"])
    assert "moneyline" in odds
    assert len(odds["moneyline"]) > 0

    best_odds, book = odds_prov.get_best_odds(odds, "moneyline", "home")
    assert best_odds is not None
    assert book is not None

    stats_prov = MockStatsProvider()
    t_stats = stats_prov.get_team_stats("Lakers", "basketball_nba")
    assert "offensive_efficiency" in t_stats
    p_stats = stats_prov.get_player_stats("LeBron James", "basketball_nba")
    assert "points_per_game" in p_stats

    ctx_prov = MockContextProvider()
    weather = ctx_prov.get_weather("Los Angeles")
    assert "temperature" in weather


def test_feature_builder_and_store(tmp_path=None):
    temp_dir = Path(tempfile.mkdtemp()) if tmp_path is None else Path(tmp_path)
    try:
        stats_prov = MockStatsProvider()
        ctx_prov = MockContextProvider()
        odds_prov = MockOddsProvider()

        builder = FeatureBuilder(stats_provider=stats_prov, context_provider=ctx_prov, odds_provider=odds_prov)
        events = odds_prov.get_upcoming_events("basketball_nba")
        event = events[0]
        odds = odds_prov.get_current_odds(event["event_id"], ["moneyline"])

        features = builder.build_features(event=event, odds_data=odds, market="moneyline", side="home")
        assert "home_fair_prob" in features
        assert "win_pct_diff" in features

        db_file = str(temp_dir / "test_features.db")
        store = FeatureStore(db_path=db_file)
        store.save_features(event["event_id"], "moneyline", "home", features)
        loaded = store.get_features(event["event_id"], "moneyline", "home")
        assert loaded is not None
        assert loaded["event_id"] == event["event_id"]
    finally:
        if tmp_path is None and temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


def test_model_training_and_calibration(tmp_path=None):
    temp_dir = Path(tempfile.mkdtemp()) if tmp_path is None else Path(tmp_path)
    try:
        X, y, feat_names = generate_training_dataset(sport="basketball_nba", n_samples=300)
        assert len(X) == 300
        assert len(feat_names) > 0

        xgb = XGBoostModel()
        xgb.train(X[:200], y[:200], feat_names)

        logreg = LogisticModel()
        logreg.train(X[:200], y[:200], feat_names)

        ensemble = EnsembleModel(models=[xgb, logreg], weights=[0.6, 0.4])
        calibrated = CalibratedModel(ensemble, method="platt")
        calibrated.fit_calibrator(X[200:250], y[200:250])

        sample_features = {name: val for name, val in zip(feat_names, X[260])}
        prob = calibrated.predict_proba(sample_features)
        assert 0.0 <= prob <= 1.0

        model_path = str(temp_dir / "test_model.joblib")
        calibrated.save(model_path)
        assert Path(model_path).exists()
    finally:
        if tmp_path is None and temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


def test_strategy_and_staking():
    detector = EdgeDetector(threshold=0.025)
    # 55% win rate at 2.0 (+10% edge)
    edge = detector.detect_edge(0.55, 2.0)
    assert edge is not None
    assert round(edge, 2) == 0.10

    # 48% win rate at 2.0 (-4% edge -> None)
    no_edge = detector.detect_edge(0.48, 2.0)
    assert no_edge is None

    # Staking
    staking = KellyStaking(fraction=0.25, max_bankroll_pct=0.02)
    stake = staking.calculate_stake(bankroll=1000.0, edge=0.10, decimal_odds=2.0)
    assert 0.0 < stake <= 20.0  # Respects 2% cap


def test_execution_and_performance(tmp_path=None):
    temp_dir = Path(tempfile.mkdtemp()) if tmp_path is None else Path(tmp_path)
    try:
        db_file = str(temp_dir / "test_bets.db")
        executor = BetExecutor(db_path=db_file, paper_trading=True)

        bet = executor.place_bet(
            event_id="ev-123",
            sport="basketball_nba",
            market="moneyline",
            side="home",
            odds=2.10,
            stake=25.0,
            bookmaker="pinnacle",
            model_prob=0.55,
            implied_prob=0.476,
            edge=0.155,
        )
        assert bet["status"] == "paper"

        evaluator = PerformanceEvaluator(db_path=db_file)
        summary = evaluator.get_summary_report()
        assert summary["total_bets"] == 1
        assert summary["total_staked"] == 25.0
    finally:
        if tmp_path is None and temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    tests = [
        ("Odds Conversions", test_odds_conversions),
        ("Vig Removal", test_vig_removal),
        ("Mock Providers", test_mock_providers),
        ("Feature Builder & Store", test_feature_builder_and_store),
        ("Model Training & Calibration", test_model_training_and_calibration),
        ("Strategy & Kelly Staking", test_strategy_and_staking),
        ("Execution & Performance", test_execution_and_performance),
    ]

    print("Running hermes_sports test suite...")
    passed = 0
    for name, t in tests:
        try:
            t()
            print(f"  [PASS] {name}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")
            raise

    print(f"\nAll {passed}/{len(tests)} tests passed successfully!")
