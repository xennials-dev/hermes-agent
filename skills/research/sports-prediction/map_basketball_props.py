#!/usr/bin/env python3
"""
NBA Player Prop Mapping Script for Hermes Agent.
Parses commercial API JSON responses (e.g. The Odds API v4) and maps
player_points, player_assists, and player_rebounds using the Logarithmic Shin-Shortcut math engine.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hermes_sports.vig import VigStripper


class BasketballPropMapper:
    def __init__(self, sharp_book: str = "pinnacle", min_edge: float = 0.02):
        self.sharp_book = sharp_book.lower()
        self.min_edge = min_edge

    def parse_and_map(self, raw_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        alerts = []
        for event in raw_events:
            matchup = f"{event.get('away_team', 'Away')} @ {event.get('home_team', 'Home')}"
            bookmakers = {b["key"].lower(): b for b in event.get("bookmakers", [])}
            sharp = bookmakers.get(self.sharp_book)
            if not sharp:
                continue

            for market in sharp.get("markets", []):
                mkey = market.get("key", "")
                outcomes = market.get("outcomes", [])
                player_groups: Dict[str, Dict[str, Any]] = {}
                for o in outcomes:
                    pname = o.get("description", o.get("name", "Unknown"))
                    player_groups.setdefault(pname, {})[o.get("name", "").lower()] = o

                for pname, sides in player_groups.items():
                    if "over" in sides and "under" in sides:
                        sharp_over_odds = int(sides["over"]["price"])
                        sharp_under_odds = int(sides["under"]["price"])
                        point = float(sides["over"].get("point", 0.0))

                        fair_over, fair_under, overround = VigStripper.logarithmic_method(
                            sharp_over_odds, sharp_under_odds
                        )

                        # Check retail books
                        for bkey, bdata in bookmakers.items():
                            if bkey == self.sharp_book:
                                continue
                            for rm in bdata.get("markets", []):
                                if rm.get("key") == mkey:
                                    for ro in rm.get("outcomes", []):
                                        rname = ro.get("description", ro.get("name", ""))
                                        rpoint = float(ro.get("point", 0.0))
                                        rside = ro.get("name", "Over").upper()

                                        if rname == pname and rpoint == point:
                                            retail_odds = int(ro.get("price", 100))
                                            retail_ip = VigStripper.american_to_implied(retail_odds)
                                            sharp_fair_p = fair_over if rside == "OVER" else fair_under
                                            sharp_ip = VigStripper.american_to_implied(
                                                sharp_over_odds if rside == "OVER" else sharp_under_odds
                                            )

                                            ev_edge = (sharp_fair_p / retail_ip) - 1.0 if retail_ip > 0 else 0.0
                                            clv_edge = (
                                                ((sharp_ip / retail_ip) - 1.0) * 100.0 if retail_ip > 0 else 0.0
                                            )

                                            if ev_edge >= self.min_edge:
                                                alerts.append(
                                                    {
                                                        "player": pname,
                                                        "market_type": mkey,
                                                        "matchup": matchup,
                                                        "line": point,
                                                        "side": rside,
                                                        "retail_book": bdata.get("title", bkey),
                                                        "retail_odds": retail_odds,
                                                        "sharp_odds": sharp_over_odds if rside == "OVER" else sharp_under_odds,
                                                        "fair_probability": sharp_fair_p,
                                                        "ev_edge": ev_edge,
                                                        "clv_edge": clv_edge,
                                                        "math_method": "logarithmic",
                                                    }
                                                )
        return alerts


def print_pretty_alerts(alerts: List[Dict[str, Any]], sharp_book: str):
    print("=" * 88)
    print("                 HERMES AGENT: BASKETBALL PROP INEFFICIENCY ALERTS")
    print("=" * 88)
    if not alerts:
        print("  No basketball prop edges found matching the criteria.")
        print("-" * 88)
        return

    for i, a in enumerate(alerts, 1):
        market_label = a["market_type"].replace("_", " ").title()
        retail_str = f"+{a['retail_odds']}" if a["retail_odds"] > 0 else str(a["retail_odds"])
        sharp_str = f"+{a['sharp_odds']}" if a["sharp_odds"] > 0 else str(a["sharp_odds"])
        print(f"ALERT #{i}: {a['player']} ({a['matchup']})")
        print(f"  |-- Prop Market     : {market_label}")
        print(f"  |-- Prop Line       : {a['line']} Units")
        print(f"  |-- Direction       : {a['side']}")
        print(f"  |-- Retail Book     : {a['retail_book']} at Odds {retail_str}")
        print(f"  |-- Sharp Baseline  : {sharp_str} ({sharp_book})")
        print(f"  |-- Fair Probability: {a['fair_probability']:.2%}")
        print(f"  |-- Expected Value  : +{a['ev_edge']:.2%}")
        print(f"  \\-- Closing Line Val: +{a['clv_edge']:.2f}% (logarithmic model)")
        print("-" * 88)


def main():
    parser = argparse.ArgumentParser(description="Map Basketball Props with Logarithmic Vig Removal")
    parser.add_argument(
        "--json-file",
        default=str(Path(__file__).resolve().parent / "data" / "mock_basketball_props.json"),
        help="Path to JSON props file",
    )
    parser.add_argument("--sharp-book", default="pinnacle", help="Sharp anchor bookmaker")
    parser.add_argument("--format", choices=["pretty", "json"], default="pretty", help="Output format")
    parser.add_argument("--min-edge", type=float, default=0.02, help="Minimum EV edge threshold")

    args = parser.parse_args()

    with open(args.json_file, "r") as f:
        events = json.load(f)

    mapper = BasketballPropMapper(sharp_book=args.sharp_book, min_edge=args.min_edge)
    alerts = mapper.parse_and_map(events)

    if args.format == "json":
        print(json.dumps(alerts, indent=2))
    else:
        print_pretty_alerts(alerts, args.sharp_book)


if __name__ == "__main__":
    main()
