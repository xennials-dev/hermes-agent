"""
Configuration dataclasses for the Hermes Sports Prediction Suite.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class DataProviderConfig:
    odds_provider: str = "mock"  # "theoddsapi", "mock"
    stats_provider: str = "mock"  # "sportsdata", "mock"
    context_provider: str = "mock"  # "openweather", "mock"

    # API Keys (read from environment if not specified)
    odds_api_key: Optional[str] = field(default_factory=lambda: os.getenv("ODDS_API_KEY"))
    stats_api_key: Optional[str] = field(default_factory=lambda: os.getenv("SPORTSDATA_API_KEY"))
    weather_api_key: Optional[str] = field(default_factory=lambda: os.getenv("OPENWEATHER_API_KEY"))

    # Endpoints
    odds_api_base_url: str = "https://api.the-odds-api.com/v4"
    sportsdata_base_url: str = "https://api.sportsdata.io/v3"
    weather_base_url: str = "https://api.openweathermap.org/data/2.5"


@dataclass
class ModelConfig:
    model_type: str = "ensemble"  # "xgboost", "lightgbm", "logistic", "ensemble"
    models_dir: str = str(Path(__file__).parent.parent / "models")
    use_calibration: bool = True
    calibration_method: str = "isotonic"  # "isotonic", "platt"

    # Default Hyperparameters
    xgb_params: Dict = field(
        default_factory=lambda: {
            "max_depth": 4,
            "learning_rate": 0.03,
            "n_estimators": 200,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "eval_metric": "logloss",
        }
    )
    lgbm_params: Dict = field(
        default_factory=lambda: {
            "num_leaves": 20,
            "learning_rate": 0.03,
            "n_estimators": 200,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
        }
    )


@dataclass
class StrategyConfig:
    edge_threshold: float = 0.025  # Minimum 2.5% edge (model_prob - implied_prob)
    vig_removal_method: str = "shin"  # "shin", "proportional", "none"
    kelly_fraction: float = 0.25  # 1/4 Kelly
    max_stake_pct: float = 0.02  # Cap max bet at 2% of bankroll
    max_bets_per_day: int = 15
    min_odds: float = 1.20  # Minimum decimal odds
    max_odds: float = 4.50  # Maximum decimal odds


@dataclass
class ExecutionConfig:
    paper_trading: bool = True
    db_path: str = str(Path(__file__).parent.parent / "data" / "sports_betting.db")
    bet_log_table: str = "bets"
    prediction_log_table: str = "predictions"


@dataclass
class Config:
    sports: List[str] = field(default_factory=lambda: ["basketball_nba", "americanfootball_nfl"])
    markets: List[str] = field(
        default_factory=lambda: [
            "moneyline",
            "spread",
            "total",
            "player_points",
            "player_assists",
            "player_rebounds",
            "player_pass_yds",
            "player_rush_yds",
            "player_rec_yds",
        ]
    )
    bookmakers: List[str] = field(
        default_factory=lambda: ["draftkings", "fanduel", "bet365", "pinnacle", "caesars", "betmgm"]
    )
    bankroll: float = 1000.0
    data: DataProviderConfig = field(default_factory=DataProviderConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    strategy: StrategyConfig = field(default_factory=StrategyConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    log_level: str = "INFO"
