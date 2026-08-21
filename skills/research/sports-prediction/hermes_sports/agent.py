"""
Main orchestrator for the Hermes Sports Prediction Agent.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import Config
from .data.context import OpenWeatherMapProvider
from .data.mock_providers import MockContextProvider, MockOddsProvider, MockStatsProvider
from .data.odds_api import TheOddsAPIProvider
from .data.sportsdata_io import SportsDataIOProvider
from .execution.bet_executor import BetExecutor
from .features.feature_builder import FeatureBuilder
from .features.feature_store import FeatureStore
from .models.base import BaseModel
from .models.ensemble import EnsembleModel
from .models.lgbm_model import LightGBMModel
from .models.logistic_model import LogisticModel
from .models.xgb_model import XGBoostModel
from .strategy.edge_detector import EdgeDetector
from .strategy.staking import KellyStaking
from .utils import odds_to_implied_probability, setup_logging


class SportsPredictionAgent:
    """Autonomous closed-loop prediction & +EV betting agent."""

    def __init__(self, config: Config):
        self.config = config
        self.logger = setup_logging(config.log_level)

        # 1. Initialize Data Providers
        self.odds_provider = self._init_odds_provider()
        self.stats_provider = self._init_stats_provider()
        self.context_provider = self._init_context_provider()

        # 2. Feature Building & Store
        self.feature_store = FeatureStore(db_path=str(Path(config.execution.db_path).parent / "features.db"))
        self.feature_builder = FeatureBuilder(
            odds_provider=self.odds_provider,
            stats_provider=self.stats_provider,
            context_provider=self.context_provider,
        )

        # 3. Strategy & Staking
        self.edge_detector = EdgeDetector(
            threshold=config.strategy.edge_threshold,
            vig_method=config.strategy.vig_removal_method,
        )
        self.staking = KellyStaking(
            kelly_fraction=config.strategy.kelly_fraction,
            max_stake_pct=config.strategy.max_stake_pct,
        )

        # 4. Execution Engine
        self.executor = BetExecutor(
            paper_trading=config.execution.paper_trading,
            db_path=config.execution.db_path,
        )
        self.bankroll = config.bankroll

        # 5. Loaded models cache
        self._models: Dict[str, BaseModel] = {}

    def _init_odds_provider(self):
        if self.config.data.odds_provider == "theoddsapi" and self.config.data.odds_api_key:
            self.logger.info("Connecting to live The Odds API...")
            return TheOddsAPIProvider(
                api_key=self.config.data.odds_api_key,
                base_url=self.config.data.odds_api_base_url,
                bookmakers=self.config.bookmakers,
            )
        self.logger.info("Using offline MockOddsProvider.")
        return MockOddsProvider(bookmakers=self.config.bookmakers)

    def _init_stats_provider(self):
        if self.config.data.stats_provider == "sportsdata" and self.config.data.stats_api_key:
            self.logger.info("Connecting to live Sportsdata.io stats feed...")
            return SportsDataIOProvider(
                api_key=self.config.data.stats_api_key,
                base_url=self.config.data.sportsdata_base_url,
            )
        self.logger.info("Using offline MockStatsProvider.")
        return MockStatsProvider()

    def _init_context_provider(self):
        if self.config.data.context_provider == "openweather" and self.config.data.weather_api_key:
            self.logger.info("Connecting to live OpenWeatherMap API...")
            return OpenWeatherMapProvider(
                api_key=self.config.data.weather_api_key,
                base_url=self.config.data.weather_base_url,
            )
        self.logger.info("Using offline MockContextProvider.")
        return MockContextProvider()

    def _get_model(self, sport: str) -> BaseModel:
        if sport in self._models:
            return self._models[sport]

        model_file = Path(self.config.model.models_dir) / f"{sport}_{self.config.model.model_type}.joblib"
        if model_file.exists():
            model = EnsembleModel()
            model.load(str(model_file))
            self._models[sport] = model
            return model

        # Fallback to default in-memory model
        xgb = XGBoostModel()
        lgbm = LightGBMModel()
        logreg = LogisticModel()
        ensemble = EnsembleModel(models=[xgb, lgbm, logreg])
        self._models[sport] = ensemble
        return ensemble

    def run_cycle(self) -> List[Dict[str, Any]]:
        """Run one complete scan of all sports and markets for +EV betting opportunities."""
        placed_wagers = []

        self.logger.info(f"Starting prediction cycle for sports: {self.config.sports} | Bankroll: ${self.bankroll:,.2f}")

        for sport in self.config.sports:
            events = self.odds_provider.get_upcoming_events(sport)
            self.logger.info(f"Found {len(events)} upcoming events for {sport}.")
            model = self._get_model(sport)

            for event in events:
                event_id = event["event_id"]
                h_team, a_team = event["home_team"], event["away_team"]
                odds_data = self.odds_provider.get_current_odds(event_id, self.config.markets)

                for market in self.config.markets:
                    if market not in odds_data or not odds_data[market]:
                        continue

                    sides = self._get_sides_for_market(market)
                    for side in sides:
                        # Extract player target if player prop market
                        player_name = None
                        if market.startswith("player_"):
                            entries = odds_data.get(market, [])
                            if entries:
                                player_name = entries[0].get("player")

                        features = self.feature_builder.build_features(
                            event=event,
                            odds_data=odds_data,
                            market=market,
                            side=side,
                            player=player_name,
                        )
                        if not features:
                            continue

                        # Save features to point-in-time feature store
                        self.feature_store.save_features(event_id, market, side, features)

                        # Model probability forecast
                        try:
                            model_prob = model.predict_proba(features)
                        except Exception as e:
                            self.logger.debug(f"Prediction failed for {event_id} {market} {side}: {e}")
                            model_prob = features.get("home_fair_prob" if side == "home" else "away_fair_prob", 0.50)

                        # Fetch highest available bookmaker odds
                        best_odds, best_book = self.odds_provider.get_best_odds(
                            odds_data=odds_data,
                            market=market,
                            side=side,
                            player=player_name,
                        )

                        if not best_odds or not best_book or best_odds < self.config.strategy.min_odds:
                            continue

                        implied_p = odds_to_implied_probability(best_odds)

                        # Log prediction to SQLite
                        self.executor.log_prediction(
                            event_id=event_id,
                            sport=sport,
                            market=market,
                            side=side,
                            model_prob=model_prob,
                            fair_prob=features.get("home_fair_prob", 0.50),
                            features=features,
                        )

                        # Check for Positive Expected Value (+EV)
                        edge = self.edge_detector.detect_edge(model_prob, best_odds)
                        if edge and edge > 0:
                            stake = self.staking.calculate_stake(self.bankroll, edge, best_odds)
                            if stake > 0:
                                bet_record = self.executor.place_bet(
                                    event_id=event_id,
                                    sport=sport,
                                    market=market,
                                    side=side,
                                    odds=best_odds,
                                    stake=stake,
                                    bookmaker=best_book,
                                    model_prob=model_prob,
                                    implied_prob=implied_p,
                                    edge=edge,
                                    player=player_name,
                                )
                                placed_wagers.append(bet_record)
                                self.bankroll -= stake

                                if len(placed_wagers) >= self.config.strategy.max_bets_per_day:
                                    self.logger.info("Reached daily maximum bet threshold.")
                                    return placed_wagers

        self.logger.info(f"Cycle completed. Found {len(placed_wagers)} +EV opportunities.")
        return placed_wagers

    def _get_sides_for_market(self, market: str) -> List[str]:
        if market in ["moneyline", "spread"]:
            return ["home", "away"]
        elif market == "total" or market.startswith("player_"):
            return ["over", "under"]
        return []
