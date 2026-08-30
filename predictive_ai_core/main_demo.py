"""
Predictive AI Core: End-to-End Orchestrator & Live Demonstration
"""

import asyncio
import json
from .odds_ingestion.models import MarketData, MarketStatus, Quote
from .shin_calculator.calculator import ShinProbabilityCalculator
from .decision_engine.engine import AutonomousDecisionEngine
from .video_synthesis.promo_generator import SportsPromoVideoGenerator


async def run_predictive_pipeline():
    print("=" * 70)
    print(" HERMES PREDICTIVE AI AGENT • SHIN-SHORTCUT & DECISION CORE")
    print("=" * 70)

    # 1. Simulate Live Market Ingestion
    sample_markets = [
        MarketData(
            event_id="nfl-kc-sf",
            sport="NFL",
            home_team="Kansas City Chiefs",
            away_team="San Francisco 49ers",
            market_type="MONEYLINE",
            bookmaker="Circa Sports",
            status=MarketStatus.ACTIVE,
            quotes=[
                Quote("home", "Chiefs", 2.05, +105, 0.4878),
                Quote("away", "49ers", 1.87, -115, 0.5348)
            ]
        ),
        MarketData(
            event_id="nba-bos-phi",
            sport="NBA",
            home_team="Boston Celtics",
            away_team="Philadelphia 76ers",
            market_type="SPREAD",
            bookmaker="Pinnacle",
            status=MarketStatus.ACTIVE,
            quotes=[
                Quote("home", "Celtics -6.5", 1.952, -105, 0.5123),
                Quote("away", "76ers +6.5", 1.952, -105, 0.5123)
            ]
        )
    ]

    calc = ShinProbabilityCalculator()
    engine = AutonomousDecisionEngine(bankroll=10000.0, min_ev_threshold=0.015, fractional_kelly=0.25)
    video_gen = SportsPromoVideoGenerator(bpm=96.0)

    all_opportunities = []

    for market in sample_markets:
        print(f"\n[1] Ingested Live Market: {market.away_team} @ {market.home_team} ({market.sport})")
        print(f"    Bookmaker: {market.bookmaker} | Raw Overround: {market.raw_overround:.4f}")

        # Shin-Shortcut Probability Calculation
        devig_res = calc.calculate_shin_shortcut(market)
        power_res = calc.calculate_power_devig(market)

        print(f"    [Shin Fair Probs]  : {devig_res.true_probabilities} (z={devig_res.insider_fraction_z})")
        print(f"    [Power DeVig Probs]: {power_res.true_probabilities}")

        # Autonomous Decision Evaluation
        opps = engine.evaluate_market(market, devig_res)
        for opp in opps:
            print(f"    -> Outcome: {opp.outcome_name:18} | True: {opp.true_probability*100:.1f}% | Dec Odds: {opp.offered_decimal_odds:.3f} | EV: {opp.expected_value_pct:+5.2f}% | Kelly: ${opp.recommended_stake_dollars:6.2f} | Action: {opp.action}")
            if opp.action == "BET":
                all_opportunities.append(opp)

    # Cross-Domain Multimedia Collision
    print("\n" + "=" * 70)
    print(" MULTIMEDIA PRODUCTION COLLISION: AUTO PROMO STORYBOARD")
    print("=" * 70)
    storyboard = video_gen.build_promo_storyboard(all_opportunities)
    print(f"Generated Promo Video: '{storyboard['project_name']}'")
    print(f"Tempo: {storyboard['music_metadata']['tempo_bpm']} BPM | Runtime: {storyboard['total_runtime_sec']}s | Audio: {storyboard['music_metadata']['track']}")
    print("\nKeyframe Timeline Breakdown:")
    for event in storyboard["timeline_events"]:
        print(f"  [{event['start_time']:05.2f}s - {event['end_time']:05.2f}s] {event['scene_name']:<32} | Cue: {event['audio_cue']}")
        print(f"      Overlay: {event['overlay_text']}")

    print("\n" + "=" * 70)
    print(" PIPELINE EXECUTION COMPLETED SUCCESSFULLY")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_predictive_pipeline())
