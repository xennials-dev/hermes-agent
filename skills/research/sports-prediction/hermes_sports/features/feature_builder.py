"""
Feature builder transforming raw sports data into statistical vectors.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ..data.base import ContextProviderBase, OddsProviderBase, StatsProviderBase
from ..utils import odds_to_implied_probability
from ..vig import remove_vig

logger = logging.getLogger("hermes_sports.features.builder")


class FeatureBuilder:
    """Builds unified multi-sport feature vectors."""

    def __init__(
        self,
        odds_provider: OddsProviderBase,
        stats_provider: StatsProviderBase,
        context_provider: ContextProviderBase,
    ):
        self.odds = odds_provider
        self.stats = stats_provider
        self.context = context_provider

    def build_features(
        self,
        event: Dict[str, Any],
        odds_data: Dict[str, Any],
        market: str,
        side: str,
        player: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        event_id = event["event_id"]
        sport = event.get("sport", "basketball_nba")
        home_team = event["home_team"]
        away_team = event["away_team"]

        features: Dict[str, Any] = {
            "event_id": event_id,
            "market": market,
            "side": side,
            "sport": sport,
            "home_team": home_team,
            "away_team": away_team,
        }

        # 1. Team Performance Metrics
        home_stats = self.stats.get_team_stats(home_team, sport)
        away_stats = self.stats.get_team_stats(away_team, sport)

        if "nba" in sport.lower() or "basketball" in sport.lower():
            h_wins = home_stats.get("wins", 40)
            h_losses = home_stats.get("losses", 42)
            a_wins = away_stats.get("wins", 40)
            a_losses = away_stats.get("losses", 42)

            h_win_pct = h_wins / max(h_wins + h_losses, 1)
            a_win_pct = a_wins / max(a_wins + a_losses, 1)

            h_off = home_stats.get("offensive_efficiency", 112.0)
            h_def = home_stats.get("defensive_efficiency", 112.0)
            a_off = away_stats.get("offensive_efficiency", 112.0)
            a_def = away_stats.get("defensive_efficiency", 112.0)

            features.update(
                {
                    "home_win_pct": h_win_pct,
                    "away_win_pct": a_win_pct,
                    "win_pct_diff": h_win_pct - a_win_pct,
                    "home_off_eff": h_off,
                    "home_def_eff": h_def,
                    "away_off_eff": a_off,
                    "away_def_eff": a_def,
                    "net_rating_diff": (h_off - h_def) - (a_off - a_def),
                    "pace_avg": (home_stats.get("pace", 100.0) + away_stats.get("pace", 100.0)) / 2.0,
                    "home_three_point_pct": home_stats.get("three_point_pct", 0.36),
                    "away_three_point_pct": away_stats.get("three_point_pct", 0.36),
                }
            )
        else:  # NFL / Football
            h_wins = home_stats.get("wins", 9)
            h_losses = home_stats.get("losses", 8)
            a_wins = away_stats.get("wins", 9)
            a_losses = away_stats.get("losses", 8)

            h_win_pct = h_wins / max(h_wins + h_losses, 1)
            a_win_pct = a_wins / max(a_wins + a_losses, 1)

            h_pf = home_stats.get("points_for", 23.0)
            h_pa = home_stats.get("points_against", 23.0)
            a_pf = away_stats.get("points_for", 23.0)
            a_pa = away_stats.get("points_against", 23.0)

            h_ypp = home_stats.get("offensive_yards_per_play", 5.4)
            a_ypp = away_stats.get("offensive_yards_per_play", 5.4)

            features.update(
                {
                    "home_win_pct": h_win_pct,
                    "away_win_pct": a_win_pct,
                    "win_pct_diff": h_win_pct - a_win_pct,
                    "home_point_diff": h_pf - h_pa,
                    "away_point_diff": a_pf - a_pa,
                    "point_diff_delta": (h_pf - h_pa) - (a_pf - a_pa),
                    "home_ypp": h_ypp,
                    "away_ypp": a_ypp,
                    "ypp_diff": h_ypp - a_ypp,
                    "turnover_diff": home_stats.get("turnover_differential", 0)
                    - away_stats.get("turnover_differential", 0),
                }
            )

        # 2. Market & Odds Features
        mkt_entries = odds_data.get(market, [])
        home_odds_list = [e["odds"] for e in mkt_entries if e.get("side") == "home"]
        away_odds_list = [e["odds"] for e in mkt_entries if e.get("side") == "away"]

        if home_odds_list and away_odds_list:
            best_home = max(home_odds_list)
            best_away = max(away_odds_list)
            fair_probs = remove_vig([best_home, best_away], method="shin")

            features["best_home_odds"] = best_home
            features["best_away_odds"] = best_away
            features["home_implied_prob"] = odds_to_implied_probability(best_home)
            features["away_implied_prob"] = odds_to_implied_probability(best_away)
            features["home_fair_prob"] = fair_probs[0]
            features["away_fair_prob"] = fair_probs[1]
            features["odds_dispersion"] = max(home_odds_list) - min(home_odds_list)
        else:
            features["home_fair_prob"] = 0.50
            features["away_fair_prob"] = 0.50
            features["odds_dispersion"] = 0.0

        # 3. Contextual & Environmental Factors
        rest_h = self.context.get_rest_days(home_team, sport)
        rest_a = self.context.get_rest_days(away_team, sport)
        features["rest_differential"] = rest_h - rest_a
        features["travel_distance"] = self.context.get_travel_distance(away_team, home_team, sport)
        features["motivation_index"] = self.context.get_motivation_indicator(event)

        weather = self.context.get_weather(home_team, event.get("start_time"))
        features["temperature"] = weather.get("temperature", 70.0)
        features["wind_speed"] = weather.get("wind_speed", 5.0)
        features["precipitation_prob"] = weather.get("precipitation_prob", 0.0)

        # 4. Injury Impacts
        injuries_h = self.stats.get_injury_report(home_team, sport)
        injuries_a = self.stats.get_injury_report(away_team, sport)
        features["home_injuries_count"] = len(injuries_h)
        features["away_injuries_count"] = len(injuries_a)
        features["injury_differential"] = len(injuries_a) - len(injuries_h)

        # 5. Player Props Specific Stats
        if market.startswith("player_") and player:
            features["player_name"] = player
            pstats = self.stats.get_player_stats(player, sport)
            if "nba" in sport.lower():
                features["player_ppg"] = pstats.get("points_per_game", 20.0)
                features["player_apg"] = pstats.get("assists_per_game", 5.0)
                features["player_rpg"] = pstats.get("rebounds_per_game", 5.0)
                features["player_usage"] = pstats.get("usage_rate", 0.25)
            else:
                features["player_pass_yds"] = pstats.get("passing_yards", 250.0)
                features["player_rush_yds"] = pstats.get("rushing_yards", 50.0)
                features["player_rec_yds"] = pstats.get("receiving_yards", 60.0)

        return features
