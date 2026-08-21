"""
Utility functions for odds conversions, market normalization, and logging.
"""

from __future__ import annotations

import logging
import math
from typing import Any, Dict


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Set up and return a structured logger."""
    logger = logging.getLogger("hermes_sports")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - [%(levelname)s] - %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    return logger


def odds_to_implied_probability(odds: float, format_type: str = "decimal") -> float:
    """Convert odds to an implied probability percentage (0.0 to 1.0)."""
    if format_type == "decimal":
        if odds <= 1.0:
            return 0.0
        return 1.0 / odds
    elif format_type == "american":
        if odds > 0:
            return 100.0 / (odds + 100.0)
        else:
            return -odds / (-odds + 100.0)
    return 0.0


def implied_probability_to_decimal(prob: float) -> float:
    """Convert implied probability into decimal odds."""
    if prob <= 0.0 or prob >= 1.0:
        return 1.01
    return round(1.0 / prob, 4)


def american_to_decimal(american: float) -> float:
    """Convert American format odds (+150, -110) to Decimal (2.50, 1.9091)."""
    if american > 0:
        return round(1.0 + (american / 100.0), 4)
    else:
        return round(1.0 - (100.0 / american), 4)


def decimal_to_american(decimal: float) -> int:
    """Convert Decimal odds (1.91) to American (-110)."""
    if decimal >= 2.0:
        return int(round((decimal - 1.0) * 100.0))
    elif decimal > 1.0:
        return int(round(-100.0 / (decimal - 1.0)))
    return 100


def normalize_market_name(raw_name: str) -> str:
    """Convert raw bookmaker market name to a standard internal identifier."""
    raw = raw_name.lower().strip().replace(" ", "_").replace("-", "_")
    mapping = {
        "h2h": "moneyline",
        "ml": "moneyline",
        "winner": "moneyline",
        "moneyline": "moneyline",
        "spreads": "spread",
        "point_spread": "spread",
        "spread": "spread",
        "totals": "total",
        "total": "total",
        "over_under": "total",
        "o_u": "total",
        "player_points": "player_points",
        "player_assists": "player_assists",
        "player_rebounds": "player_rebounds",
        "player_pass_yds": "player_pass_yds",
        "player_rush_yds": "player_rush_yds",
        "player_rec_yds": "player_rec_yds",
    }
    return mapping.get(raw, raw)
