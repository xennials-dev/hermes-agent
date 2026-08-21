"""
Multi-sport feature engineering pipeline for NBA and NFL matchups.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

try:
    from ..data.base import ContextProviderBase, OddsProviderBase, StatsProviderBase  # type: ignore
    from ..utils import odds_to_implied_probability  # type: ignore
    from ..vig import remove_vig  # type: ignore
except (ImportError, ValueError):
    from hermes_sports.data.base import ContextProviderBase, OddsProviderBase, StatsProviderBase  # type: ignore
    from hermes_sports.utils import odds_to_implied_probability  # type: ignore
    from hermes_sports.vig import remove_vig  # type: ignore

logger = logging.getLogger("hermes_sports.features.builder")


class FeatureBuilder:
    """Extracts domain and situational features for sports events."""

    def __init__(
        self,
        stats_provider: StatsProviderBase,
        context_provider: ContextProviderBase,
        odds_provider: Optional[OddsProviderBase] = None,
        vig_method: str = "shin",
    ):
        self.stats_provider = stats_provider
        self.context_provider = context_provider
        self.odds_provider = odds_provider
        self.vig_method = vig_method

    def build_features(
        self,
        event: Dict[str, Any],
        odds_data: Dict[str, Any],
        market: str = "moneyline",
        side: str = "home",
        player: Optional[str] = None,
        player_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        target_player = player or player_name
        sport = event.get("sport", "basketball_nba")
        home_team = event.get("home_team", "")
        away_team = event.get("away_team", "")

        features: Dict[str, Any] = {
            "event_id": event.get("event_id"),
            "sport": sport,
            "market": market,
            "home_team": home_team,
            "away_team": away_team,
        }

        # Market-derived baseline implied probabilities & vig removal
        ml_odds = odds_data.get("moneyline", [])
        h_odds = [o["odds"] for o in ml_odds if o["side"] == "home"]
        a_odds = [o["odds"] for o in ml_odds if o["side"] == "away"]

        if h_odds and a_odds:
            avg_h = sum(h_odds) / len(h_odds)
            avg_a = sum(a_odds) / len(a_odds)
            fair_h, fair_a = remove_vig([avg_h, avg_a], method=self.vig_method)
            features["home_fair_prob"] = fair_h
            features["away_fair_prob"] = fair_a
            features["odds_dispersion"] = max(h_odds) - min(h_odds)
        else:
            features["home_fair_prob"] = 0.50
            features["away_fair_prob"] = 0.50
            features["odds_dispersion"] = 0.0

        # Situational & Context features
        features["rest_home"] = self.context_provider.get_rest_days(home_team, sport)
        features["rest_away"] = self.context_provider.get_rest_days(away_team, sport)
        features["rest_differential"] = features["rest_home"] - features["rest_away"]
        features["travel_distance"] = self.context_provider.get_travel_distance(away_team, home_team, sport)
        features["motivation_index"] = self.context_provider.get_motivation_indicator(event)

        # Team stats & sport-specific metrics
        h_stats = self.stats_provider.get_team_stats(home_team, sport)
        a_stats = self.stats_provider.get_team_stats(away_team, sport)

        if "nba" in sport.lower():
            features.update(self._build_nba_features(h_stats, a_stats))
        else:  # NFL
            features.update(self._build_nfl_features(h_stats, a_stats, home_team, event.get("start_time")))

        # Player-specific features for props
        if target_player:
            p_stats = self.stats_provider.get_player_stats(target_player, sport)
            features.update(self._build_player_features(p_stats, sport))

        # Injuries
        h_inj = self.stats_provider.get_injury_report(home_team, sport)
        a_inj = self.stats_provider.get_injury_report(away_team, sport)
        features["home_injury_count"] = len(h_inj)
        features["away_injury_count"] = len(a_inj)
        features["injury_differential"] = len(a_inj) - len(h_inj)

        return features

    def _build_nba_features(self, h: Dict[str, Any], a: Dict[str, Any]) -> Dict[str, Any]:
        h_wins = h.get("wins", 20)
        h_loss = h.get("losses", 20)
        a_wins = a.get("wins", 20)
        a_loss = a.get("losses", 20)

        h_wpct = h_wins / max(1, h_wins + h_loss)
        a_wpct = a_wins / max(1, a_wins + a_loss)

        h_off = h.get("offensive_efficiency", 112.0)
        h_def = h.get("defensive_efficiency", 112.0)
        a_off = a.get("offensive_efficiency", 112.0)
        a_def = a.get("defensive_efficiency", 112.0)

        return {
            "home_win_pct": h_wpct,
            "away_win_pct": a_wpct,
            "win_pct_diff": h_wpct - a_wpct,
            "home_off_eff": h_off,
            "home_def_eff": h_def,
            "away_off_eff": a_off,
            "away_def_eff": a_def,
            "net_rating_diff": (h_off - h_def) - (a_off - a_def),
            "pace_avg": (h.get("pace", 99.0) + a.get("pace", 99.0)) / 2.0,
            "home_three_point_pct": h.get("three_point_pct", 0.36),
            "away_three_point_pct": a.get("three_point_pct", 0.36),
        }

    def _build_nfl_features(
        self, h: Dict[str, Any], a: Dict[str, Any], city: str, event_time: Optional[str]
    ) -> Dict[str, Any]:
        h_wins = h.get("wins", 8)
        h_loss = h.get("losses", 8)
        a_wins = a.get("wins", 8)
        a_loss = a.get("losses", 8)

        h_wpct = h_wins / max(1, h_wins + h_loss)
        a_wpct = a_wins / max(1, a_wins + a_loss)

        h_pd = h.get("points_for", 21.0) - h.get("points_against", 21.0)
        a_pd = a.get("points_for", 21.0) - a.get("points_against", 21.0)

        weather = self.context_provider.get_weather(city, event_time)

        return {
            "home_win_pct": h_wpct,
            "away_win_pct": a_wpct,
            "win_pct_diff": h_wpct - a_wpct,
            "home_point_diff": h_pd,
            "away_point_diff": a_pd,
            "point_diff_delta": h_pd - a_pd,
            "home_ypp": h.get("offensive_yards_per_play", 5.3),
            "away_ypp": a.get("offensive_yards_per_play", 5.3),
            "ypp_diff": h.get("offensive_yards_per_play", 5.3) - a.get("offensive_yards_per_play", 5.3),
            "turnover_diff": h.get("turnover_differential", 0) - a.get("turnover_differential", 0),
            "temperature": weather.get("temperature", 70.0),
            "wind_speed": weather.get("wind_speed", 5.0),
            "precipitation_prob": weather.get("precipitation_prob", 0.0),
        }

    def _build_player_features(self, p: Dict[str, Any], sport: str) -> Dict[str, Any]:
        if "nba" in sport.lower():
            return {
                "player_mpg": p.get("minutes_per_game", 25.0),
                "player_ppg": p.get("points_per_game", 15.0),
                "player_apg": p.get("assists_per_game", 4.0),
                "player_rpg": p.get("rebounds_per_game", 5.0),
                "player_usage": p.get("usage_rate", 0.20),
            }
        else:  # NFL
            return {
                "player_pass_yds": p.get("passing_yards", 0.0),
                "player_rush_yds": p.get("rushing_yards", 0.0),
                "player_rec_yds": p.get("receiving_yards", 0.0),
            }
