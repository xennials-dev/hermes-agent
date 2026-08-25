#!/usr/bin/env python3
"""
Hermes Agent: Quantitative Market Inefficiency & Prop Analysis CLI.
Isolates true sharp closing line fair probabilities using the Logarithmic (Shin-Shortcut)
and Multiplicative vig-stripping engines to surface +EV and CLV betting opportunities.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add hermes_sports to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from hermes_sports.vig import VigStripper


class PropAnalyzer:
    """
    Analyzes player props and market discrepancies between sharp anchors and retail books.
    """

    def __init__(self, sharp_book: str = "pinnacle", min_edge: float = 0.02):
        self.sharp_book = sharp_book.lower()
        self.min_edge = min_edge

    def calculate_edges(
        self, sharp_over: int, sharp_under: int, retail_odds: int, is_over: bool = True
    ) -> Dict[str, Any]:
        """
        Calculates Fair Logarithmic/Multiplicative Probabilities, +EV Edge, and CLV Edge.
        """
        # 1. Logarithmic Method (Shin-Shortcut)
        fair_over_log, fair_under_log, overround = VigStripper.logarithmic_method(sharp_over, sharp_under)
        # 2. Multiplicative Method
        fair_over_mult, fair_under_mult, _ = VigStripper.multiplicative_method(sharp_over, sharp_under)

        sharp_target_log = fair_over_log if is_over else fair_under_log
        sharp_target_mult = fair_over_mult if is_over else fair_under_mult

        # 3. Retail Implied Probability
        retail_implied = VigStripper.american_to_implied(retail_odds)
        sharp_implied = VigStripper.american_to_implied(sharp_over if is_over else sharp_under)

        # 4. Expected Value (+EV Edge) & Closing Line Value (CLV Edge %)
        ev_edge = (sharp_target_log / retail_implied) - 1.0 if retail_implied > 0 else 0.0
        clv_edge = ((sharp_implied / retail_implied) - 1.0) * 100.0 if retail_implied > 0 else 0.0

        return {
            "sharp_log_fair_prob": round(sharp_target_log, 4),
            "sharp_mult_fair_prob": round(sharp_target_mult, 4),
            "retail_implied_prob": round(retail_implied, 4),
            "ev_edge": round(ev_edge, 4),
            "clv_edge": round(clv_edge, 2),
            "overround": round(overround, 4),
        }

    def analyze_event(self, event_data: Dict[str, Any], target_market: str) -> List[Dict[str, Any]]:
        """
        Parses an event and extracts all matching prop opportunities beating the edge threshold.
        """
        alerts = []
        matchup = f"{event_data.get('away_team', 'Away')} @ {event_data.get('home_team', 'Home')}"
        bookmakers = {b["key"].lower(): b for b in event_data.get("bookmakers", [])}

        sharp_b = bookmakers.get(self.sharp_book)
        if not sharp_b:
            return alerts

        # Map sharp lines
        sharp_market_map: Dict[Tuple[str, float], Tuple[int, int]] = {}
        for m in sharp_b.get("markets", []):
            if m.get("key") == target_market:
                outcomes = m.get("outcomes", [])
                by_player: Dict[str, Dict[str, Any]] = {}
                for o in outcomes:
                    pname = o.get("description", o.get("name", "Unknown"))
                    by_player.setdefault(pname, {})[o.get("name", "").lower()] = o

                for pname, sides in by_player.items():
                    if "over" in sides and "under" in sides:
                        over_o = sides["over"]
                        under_o = sides["under"]
                        point = float(over_o.get("point", 0.0))
                        sharp_market_map[(pname, point)] = (int(over_o["price"]), int(under_o["price"]))

        # Scan retail bookmakers against sharp lines
        for bkey, bdata in bookmakers.items():
            if bkey == self.sharp_book:
                continue
            for m in bdata.get("markets", []):
                if m.get("key") == target_market:
                    for o in m.get("outcomes", []):
                        pname = o.get("description", o.get("name", "Unknown"))
                        point = float(o.get("point", 0.0))
                        side = o.get("name", "Over").upper()
                        is_over = side == "OVER"
                        key = (pname, point)

                        if key in sharp_market_map:
                            sharp_over, sharp_under = sharp_market_map[key]
                            retail_odds = int(o.get("price", 100))
                            edges = self.calculate_edges(sharp_over, sharp_under, retail_odds, is_over)

                            if edges["ev_edge"] >= self.min_edge:
                                alerts.append(
                                    {
                                        "player": pname,
                                        "market": target_market,
                                        "matchup": matchup,
                                        "line": point,
                                        "side": side,
                                        "retail_book": bdata.get("title", bkey),
                                        "retail_odds": retail_odds,
                                        "sharp_odds": sharp_over if is_over else sharp_under,
                                        **edges,
                                    }
                                )
        return alerts


def format_pretty_report(alerts: List[Dict[str, Any]], sport: str, market: str, sharp_book: str, min_edge: float) -> str:
    lines = [
        "=" * 88,
        "                     HERMES AGENT: MARKET INEFFICIENCY ALERT REPORT                     ",
        "=" * 88,
        f"Target Sport   : {sport}",
        f"Target Prop    : {market}",
        f"Sharp Anchor   : {sharp_book}",
        f"Min Edge Thresh: {min_edge:.2%}",
        "-" * 88,
    ]

    if not alerts:
        lines.append("  No market discrepancies found exceeding the minimum edge threshold.")
        lines.append("-" * 88)
        return "\n".join(lines)

    for i, a in enumerate(alerts, 1):
        odds_str = f"+{a['retail_odds']}" if a["retail_odds"] > 0 else str(a["retail_odds"])
        sharp_str = f"+{a['sharp_odds']}" if a["sharp_odds"] > 0 else str(a["sharp_odds"])
        lines.extend(
            [
                f"ALERT #{i}: {a['player']} ({a['matchup']})",
                f"  |-- Prop Line       : {a['line']} Units",
                f"  |-- Direction       : {a['side']}",
                f"  |-- Retail Book     : {a['retail_book']} at Odds {odds_str}",
                f"  |-- Sharp Market    : {sharp_str} ({sharp_book})",
                f"  |-- Log Fair Prob   : {a['sharp_log_fair_prob']:.2%}",
                f"  |-- Mult Fair Prob  : {a['sharp_mult_fair_prob']:.2%}",
                f"  |-- Expected Value  : +{a['ev_edge']:.2%}",
                f"  \\-- Closing Line Val: +{a['clv_edge']:.2f}%",
                "-" * 88,
            ]
        )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Hermes Agent Prop Inefficiency & +EV Scanner")
    parser.add_argument("--api-key", default=None, help="The Odds API Key")
    parser.add_argument("--sport", default="americanfootball_nfl", help="Sport key (e.g. americanfootball_nfl, basketball_nba)")
    parser.add_argument("--market", default="player_pass_yds", help="Market key (e.g. player_pass_yds, player_points, spreads_h1)")
    parser.add_argument("--sharp-book", default="pinnacle", help="Sharp anchor bookmaker")
    parser.add_argument("--format", choices=["pretty", "json"], default="pretty", help="Output format")
    parser.add_argument("--min-edge", type=float, default=0.02, help="Minimum EV edge threshold (e.g. 0.02 for 2%)")
    parser.add_argument("--json-file", default=None, help="Local mock JSON payload file path")

    args = parser.parse_args()

    # Load data from local mock or fallback to template
    data: List[Dict[str, Any]] = []
    if args.json_file and Path(args.json_file).exists():
        with open(args.json_file, "r") as f:
            data = json.load(f)
    else:
        # Default mock template for verification
        mock_path = Path(__file__).resolve().parent / "data" / "mock_basketball_props.json"
        if mock_path.exists() and "basketball" in args.sport:
            with open(mock_path, "r") as f:
                data = json.load(f)
        else:
            data = [
                {
                    "home_team": "Kansas City Chiefs",
                    "away_team": "Baltimore Ravens",
                    "bookmakers": [
                        {
                            "key": "pinnacle",
                            "title": "Pinnacle",
                            "markets": [
                                {
                                    "key": "player_pass_yds",
                                    "outcomes": [
                                        {"name": "Over", "description": "Patrick Mahomes", "price": -135, "point": 268.5},
                                        {"name": "Under", "description": "Patrick Mahomes", "price": 105, "point": 268.5},
                                    ],
                                }
                            ],
                        },
                        {
                            "key": "betrivers",
                            "title": "BetRivers",
                            "markets": [
                                {
                                    "key": "player_pass_yds",
                                    "outcomes": [
                                        {"name": "Over", "description": "Patrick Mahomes", "price": 105, "point": 268.5},
                                        {"name": "Under", "description": "Patrick Mahomes", "price": -135, "point": 268.5},
                                    ],
                                }
                            ],
                        },
                    ],
                }
            ]

    analyzer = PropAnalyzer(sharp_book=args.sharp_book, min_edge=args.min_edge)
    all_alerts = []
    for event in data:
        all_alerts.extend(analyzer.analyze_event(event, args.market))

    if args.format == "json":
        print(json.dumps(all_alerts, indent=2))
    else:
        print(format_pretty_report(all_alerts, args.sport, args.market, args.sharp_book, args.min_edge))


if __name__ == "__main__":
    main()
