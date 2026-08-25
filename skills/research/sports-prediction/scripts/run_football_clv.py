#!/usr/bin/env python3
"""
Hermes Agent: Autonomous 24/7 Football CLV & Prop Scanner Runner.
Executes periodic sweeps across NFL/CFB spreads and player props, solves for fair
probabilities, and broadcasts +EV closing line opportunities.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add sports prediction root to path
sports_root = Path(__file__).resolve().parent.parent
if str(sports_root) not in sys.path:
    sys.path.insert(0, str(sports_root))

from hermes_sports.football_engine import FootballCLVEngine


def main():
    parser = argparse.ArgumentParser(description="Hermes Autonomous Football CLV Engine")
    parser.add_argument("--sport", default="americanfootball_nfl", help="Sport key (e.g. americanfootball_nfl, americanfootball_ncaaf)")
    parser.add_argument("--markets", default="spreads,spreads_h1,player_pass_yds,player_anytime_td", help="Target markets")
    parser.add_argument("--sharp-book", default="pinnacle", help="Sharp market-making anchor")
    parser.add_argument("--min-edge", type=float, default=0.02, help="Minimum EV edge threshold")
    parser.add_argument("--format", choices=["pretty", "json"], default="pretty", help="Terminal format")
    parser.add_argument("--notify-telegram", action="store_true", help="Send live telegram alert notifications")

    args = parser.parse_args()

    engine = FootballCLVEngine(sharp_anchors=[args.sharp_book], min_ev_edge=args.min_edge)
    events = engine.fetch_live_odds(sport=args.sport, markets=args.markets)
    alerts = engine.scan_market_discrepancies(events, sport_key=args.sport)

    if args.notify_telegram:
        for alert in alerts:
            engine.send_telegram_alert(alert)

    if args.format == "json":
        print(json.dumps(alerts, indent=2))
    else:
        print("=" * 88)
        print("          [NFL/CFB] HERMES AGENT: FOOTBALL MARKET INEFFICIENCY & CLV SWEEP")
        print("=" * 88)
        print(f"Sport: {args.sport} | Sharp Anchor: {args.sharp_book} | Min Edge: {args.min_edge:.2%}")
        print(f"Discrepancies Found: {len(alerts)}")
        print("-" * 88)

        for i, a in enumerate(alerts, 1):
            if a["type"] == "prop":
                print(f"ALERT #{i} [PROP]: {a['player']} ({a['matchup']})")
                print(f"  |-- Prop Market    : {a['market']} ({a['line']} Units)")
                print(f"  |-- Direction      : {a['side']}")
                print(f"  |-- Retail Book    : {a['retail_book']} at Odds {a['retail_odds']:+d}")
                print(f"  |-- Sharp Baseline : {a['sharp_odds']:+d} ({a['sharp_book']})")
                print(f"  |-- Fair Prob (Log): {a['fair_probability']:.2%}")
                print(f"  |-- Expected Value : +{a['ev_edge']:.2%}")
                print(f"  \\-- CLV Edge       : +{a['clv_edge']:.2f}%")
            else:
                print(f"ALERT #{i} [SPREAD]: {a['team']} ({a['matchup']})")
                print(f"  |-- Market         : {a['market']}")
                print(f"  |-- Retail Line    : {a['retail_book']} {a['retail_line']:+.1f} (Odds {a['retail_odds']:+d})")
                print(f"  |-- Sharp Anchor   : {a['sharp_book']} {a['sharp_line']:+.1f} (Odds {a['sharp_odds']:+d})")
                print(f"  |-- Fair Prob      : {a['fair_probability']:.2%}")
                print(f"  |-- Weighted +EV   : +{a['ev_edge']:.2%}")
                print(f"  \\-- CLV Edge       : +{a['clv_edge']:.2f}%")
            print("-" * 88)


if __name__ == "__main__":
    main()
