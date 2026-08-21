#!/usr/bin/env python3
"""
CLI Runner for the Hermes Autonomous Sports Prediction & +EV Betting Agent.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add package root to sys.path so hermes_sports can be imported cleanly
current_dir = Path(__file__).resolve().parent
package_root = current_dir.parent
if str(package_root) not in sys.path:
    sys.path.insert(0, str(package_root))

from hermes_sports.agent import SportsPredictionAgent  # type: ignore
from hermes_sports.config import Config, DataProviderConfig, ExecutionConfig, ModelConfig, StrategyConfig  # type: ignore
from hermes_sports.execution.performance import PerformanceEvaluator  # type: ignore
from hermes_sports.training.train import train_prediction_pipeline  # type: ignore


def main():
    parser = argparse.ArgumentParser(
        description="Hermes Sports Outcome Prediction & +EV Betting Intelligence Agent"
    )
    parser.add_argument(
        "--action",
        choices=["run", "train", "report"],
        default="run",
        help="Action to perform: run (live/paper cycle), train (train models), report (view ROI & win rates)",
    )
    parser.add_argument(
        "--sport",
        choices=["basketball_nba", "americanfootball_nfl", "all"],
        default="all",
        help="Sport league to target",
    )
    parser.add_argument(
        "--bankroll",
        type=float,
        default=1000.0,
        help="Starting simulation bankroll amount",
    )
    parser.add_argument(
        "--edge-threshold",
        type=float,
        default=0.025,
        help="Minimum edge required to place a wager (default: 0.025 = 2.5%)",
    )
    parser.add_argument(
        "--kelly-fraction",
        type=float,
        default=0.25,
        help="Fractional Kelly staking multiplier (default: 0.25 = 1/4 Kelly)",
    )
    parser.add_argument(
        "--paper",
        action="store_true",
        default=True,
        help="Enable paper trading simulation (default: True)",
    )
    parser.add_argument(
        "--live-data",
        action="store_true",
        default=False,
        help="Use real external APIs if keys are available in environment",
    )

    args = parser.parse_args()

    sports = (
        ["basketball_nba", "americanfootball_nfl"]
        if args.sport == "all"
        else [args.sport]
    )

    data_cfg = DataProviderConfig(
        odds_provider="theoddsapi" if args.live_data else "mock",
        stats_provider="sportsdata" if args.live_data else "mock",
        context_provider="openweather" if args.live_data else "mock",
    )

    strat_cfg = StrategyConfig(
        edge_threshold=args.edge_threshold,
        kelly_fraction=args.kelly_fraction,
    )

    exec_cfg = ExecutionConfig(
        paper_trading=args.paper,
    )

    config = Config(
        sports=sports,
        bankroll=args.bankroll,
        data=data_cfg,
        strategy=strat_cfg,
        execution=exec_cfg,
    )

    if args.action == "train":
        print("\n" + "=" * 65)
        print("  HERMES SPORTS PREDICTION -- MODEL TRAINING PIPELINE")
        print("=" * 65)
        for s in sports:
            res = train_prediction_pipeline(config=config, sport=s)
            print(f"\n[OK] Trained {s.upper()} Model:")
            print(f"    * Samples:      {res['samples']}")
            print(f"    * Log Loss:     {res['log_loss']}")
            print(f"    * Brier Score:  {res['brier_score']}")
            print(f"    * ROC AUC:      {res['roc_auc']}")
            print(f"    * Saved Model:  {res['model_path']}")
        print("\n" + "=" * 65 + "\n")

    elif args.action == "report":
        evaluator = PerformanceEvaluator(db_path=config.execution.db_path)
        report = evaluator.get_summary_report()
        print("\n" + "=" * 65)
        print("  HERMES SPORTS PREDICTION -- PERFORMANCE & ROI ANALYTICS")
        print("=" * 65)
        print(f"  * Total Wagers Logged:    {report['total_bets']}")
        print(f"  * Total Capital Staked:   ${report['total_staked']:,.2f}")
        print(f"  * Settled Wagers:         {report['settled_bets']}")
        print(f"  * Win Rate:               {report['win_rate_pct']}%")
        print(f"  * Net Profit / Loss:      ${report['net_profit']:,.2f}")
        print(f"  * Realized ROI:           {report['roi_pct']}%")
        print(f"  * Average Edge Detected:  {report['avg_edge_pct']}%")
        print(f"  * Average Odds:           {report['avg_odds']}")
        if report.get("by_sport"):
            print("\n  Breakdown by Sport:")
            for sp, data in report["by_sport"].items():
                print(f"    - {sp}: {data['bets']} bets (Avg Edge: {data['avg_edge']*100:.2f}%)")
        print("=" * 65 + "\n")

    elif args.action == "run":
        agent = SportsPredictionAgent(config=config)
        wagers = agent.run_cycle()

        print("\n" + "=" * 65)
        print("  HERMES SPORTS PREDICTION -- +EV BETTING OPPORTUNITIES")
        print("=" * 65)
        if not wagers:
            print(f"\n  No +EV opportunities exceeding {args.edge_threshold*100:.1f}% edge found.")
        else:
            for i, w in enumerate(wagers, 1):
                player_str = f" ({w['player']})" if w.get("player") else ""
                print(
                    f"  {i}. [{w['sport'].upper()}] {w['market']}{player_str} -> {w['side'].upper()}"
                )
                print(
                    f"     * Best Odds:  {w['odds']} ({w['bookmaker']})"
                )
                print(
                    f"     * Model Prob: {w['model_prob']*100:.1f}% | Edge: +{w['edge']*100:.1f}%"
                )
                print(
                    f"     * Stake:      ${w['stake']:,.2f} ({'Paper' if w['status']=='paper' else 'Live'})"
                )
                print()
        print(f"  Updated Available Bankroll: ${agent.bankroll:,.2f}")
        print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
