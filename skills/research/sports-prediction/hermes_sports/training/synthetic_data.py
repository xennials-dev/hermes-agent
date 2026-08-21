"""
Dataset generator simulating historical NBA and NFL matchups with realistic statistical distributions.
"""

from __future__ import annotations

import logging
import math
import random
from typing import List, Tuple

logger = logging.getLogger("hermes_sports.training.synthetic")


def generate_training_dataset(
    sport: str = "basketball_nba", n_samples: int = 2500, random_state: int = 42
) -> Tuple[List[List[float]], List[int], List[str]]:
    """Generate realistic training feature matrices X and binary labels y."""
    random.seed(random_state)

    if "nba" in sport.lower():
        feature_names = [
            "home_win_pct",
            "away_win_pct",
            "win_pct_diff",
            "home_off_eff",
            "home_def_eff",
            "away_off_eff",
            "away_def_eff",
            "net_rating_diff",
            "pace_avg",
            "home_three_point_pct",
            "away_three_point_pct",
            "home_fair_prob",
            "away_fair_prob",
            "odds_dispersion",
            "rest_differential",
            "travel_distance",
            "motivation_index",
            "injury_differential",
        ]

        X: List[List[float]] = []
        y: List[int] = []

        for _ in range(n_samples):
            h_win_pct = random.uniform(0.25, 0.75)
            a_win_pct = random.uniform(0.25, 0.75)
            win_diff = h_win_pct - a_win_pct

            h_off = random.gauss(113.0, 3.5)
            h_def = random.gauss(113.0, 3.5)
            a_off = random.gauss(113.0, 3.5)
            a_def = random.gauss(113.0, 3.5)
            net_diff = (h_off - h_def) - (a_off - a_def)

            pace = random.gauss(99.0, 2.5)
            h_3pt = random.uniform(0.33, 0.39)
            a_3pt = random.uniform(0.33, 0.39)

            h_fair = max(0.15, min(0.85, 0.50 + 0.30 * (win_diff + net_diff / 25.0) + random.gauss(0, 0.04)))
            a_fair = 1.0 - h_fair

            odds_disp = random.expovariate(25.0)
            rest_diff = random.choice([-2, -1, 0, 1, 2])
            travel = random.uniform(100, 2200)
            motivation = random.uniform(0.5, 0.9)
            injury_diff = random.choice([-2, -1, 0, 1, 2])

            row = [
                h_win_pct,
                a_win_pct,
                win_diff,
                h_off,
                h_def,
                a_off,
                a_def,
                net_diff,
                pace,
                h_3pt,
                a_3pt,
                h_fair,
                a_fair,
                odds_disp,
                rest_diff,
                travel,
                motivation,
                injury_diff,
            ]
            X.append(row)

            # Logit
            logit = (
                0.15  # Home court advantage
                + 1.8 * win_diff
                + 0.08 * net_diff
                + 0.8 * (h_fair - 0.5)
                + 0.08 * rest_diff
                + 0.10 * injury_diff
            )
            prob = 1.0 / (1.0 + math.exp(-logit))
            label = 1 if random.random() < prob else 0
            y.append(label)

    else:  # NFL
        feature_names = [
            "home_win_pct",
            "away_win_pct",
            "win_pct_diff",
            "home_point_diff",
            "away_point_diff",
            "point_diff_delta",
            "home_ypp",
            "away_ypp",
            "ypp_diff",
            "turnover_diff",
            "home_fair_prob",
            "away_fair_prob",
            "odds_dispersion",
            "rest_differential",
            "travel_distance",
            "temperature",
            "wind_speed",
            "precipitation_prob",
            "injury_differential",
        ]

        X = []
        y = []

        for _ in range(n_samples):
            h_win_pct = random.uniform(0.20, 0.80)
            a_win_pct = random.uniform(0.20, 0.80)
            win_diff = h_win_pct - a_win_pct

            h_pd = random.gauss(0, 6.0)
            a_pd = random.gauss(0, 6.0)
            pd_delta = h_pd - a_pd

            h_ypp = random.gauss(5.4, 0.5)
            a_ypp = random.gauss(5.4, 0.5)
            ypp_diff = h_ypp - a_ypp

            to_diff = random.choice([-3, -2, -1, 0, 1, 2, 3])
            h_fair = max(0.15, min(0.85, 0.50 + 0.25 * win_diff + 0.015 * pd_delta + random.gauss(0, 0.04)))
            a_fair = 1.0 - h_fair

            odds_disp = random.expovariate(20.0)
            rest_diff = random.choice([-1, 0, 1])
            travel = random.uniform(100, 2500)
            temp = random.uniform(25, 85)
            wind = random.uniform(2, 22)
            precip = random.choice([0.0, 0.0, 0.0, 0.3, 0.8])
            injury_diff = random.choice([-2, -1, 0, 1, 2])

            row = [
                h_win_pct,
                a_win_pct,
                win_diff,
                h_pd,
                a_pd,
                pd_delta,
                h_ypp,
                a_ypp,
                ypp_diff,
                to_diff,
                h_fair,
                a_fair,
                odds_disp,
                rest_diff,
                travel,
                temp,
                wind,
                precip,
                injury_diff,
            ]
            X.append(row)

            logit = (
                0.12  # Home field advantage
                + 1.6 * win_diff
                + 0.06 * pd_delta
                + 0.35 * ypp_diff
                + 0.12 * to_diff
                + 0.9 * (h_fair - 0.5)
            )
            prob = 1.0 / (1.0 + math.exp(-logit))
            label = 1 if random.random() < prob else 0
            y.append(label)

    logger.info(f"Generated synthetic training dataset for {sport}: {len(X)} samples, {len(feature_names)} features.")
    return X, y, feature_names
