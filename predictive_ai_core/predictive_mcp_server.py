#!/usr/bin/env python3
"""
Predictive AI Core MCP Server (Model Context Protocol)
Exposes Shin-Shortcut Probability Calculation and Autonomous Decision Engine
as native tools for Hermes Agent.
"""

import sys
import os
import json
import traceback

# Ensure the parent scratch directory is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from predictive_ai_core.odds_ingestion.models import MarketData, MarketStatus, Quote
from predictive_ai_core.shin_calculator.calculator import ShinProbabilityCalculator
from predictive_ai_core.decision_engine.engine import AutonomousDecisionEngine


TOOLS = [
    {
        "name": "calculate_shin_shortcut",
        "description": "Calculates Shin-Shortcut true probabilities and market overround using Shin's market microstructure model (1993/1998) to de-vig sports betting odds and detect insider trading (z).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string", "description": "Identifier for the sporting event (e.g. nfl-kc-sf)"},
                "sport": {"type": "string", "description": "Sport category (e.g. NFL, NBA, MLB)"},
                "home_team": {"type": "string", "description": "Home team name"},
                "away_team": {"type": "string", "description": "Away team name"},
                "bookmaker": {"type": "string", "description": "Bookmaker or exchange name (e.g. Circa, Pinnacle)", "default": "Consensus"},
                "quotes": {
                    "type": "array",
                    "description": "List of outcome quotes with decimal odds",
                    "items": {
                        "type": "object",
                        "properties": {
                            "outcome_id": {"type": "string", "description": "Outcome ID (e.g. home, away)"},
                            "outcome_name": {"type": "string", "description": "Outcome label (e.g. Kansas City Chiefs)"},
                            "decimal_odds": {"type": "number", "description": "Decimal odds offered (e.g. 2.05, 1.87)"}
                        },
                        "required": ["outcome_id", "outcome_name", "decimal_odds"]
                    }
                }
            },
            "required": ["event_id", "sport", "home_team", "away_team", "quotes"]
        }
    },
    {
        "name": "calculate_power_devig",
        "description": "Calculates true probabilities using the multiplicative Power De-Vig method for sports betting markets.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string", "description": "Event identifier"},
                "sport": {"type": "string", "description": "Sport category"},
                "home_team": {"type": "string", "description": "Home team name"},
                "away_team": {"type": "string", "description": "Away team name"},
                "bookmaker": {"type": "string", "description": "Bookmaker name", "default": "Consensus"},
                "quotes": {
                    "type": "array",
                    "description": "List of outcome quotes with decimal odds",
                    "items": {
                        "type": "object",
                        "properties": {
                            "outcome_id": {"type": "string"},
                            "outcome_name": {"type": "string"},
                            "decimal_odds": {"type": "number"}
                        },
                        "required": ["outcome_id", "outcome_name", "decimal_odds"]
                    }
                }
            },
            "required": ["event_id", "sport", "home_team", "away_team", "quotes"]
        }
    },
    {
        "name": "evaluate_betting_decisions",
        "description": "Evaluates live sports betting markets using Shin true probabilities against bookmaker prices to find positive expected value (+EV) and calculate optimal bankroll allocations using Fractional Kelly staking.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string", "description": "Event identifier"},
                "sport": {"type": "string", "description": "Sport category"},
                "home_team": {"type": "string", "description": "Home team name"},
                "away_team": {"type": "string", "description": "Away team name"},
                "bookmaker": {"type": "string", "description": "Bookmaker name", "default": "Consensus"},
                "bankroll": {"type": "number", "description": "Total available bankroll in dollars (default: 10000.0)", "default": 10000.0},
                "min_ev_threshold": {"type": "number", "description": "Minimum +EV percentage required to trigger a BET action (default: 0.015 = 1.5%)", "default": 0.015},
                "fractional_kelly": {"type": "number", "description": "Fractional Kelly multiplier (e.g. 0.25 for quarter Kelly)", "default": 0.25},
                "quotes": {
                    "type": "array",
                    "description": "List of outcome quotes with decimal odds",
                    "items": {
                        "type": "object",
                        "properties": {
                            "outcome_id": {"type": "string"},
                            "outcome_name": {"type": "string"},
                            "decimal_odds": {"type": "number"}
                        },
                        "required": ["outcome_id", "outcome_name", "decimal_odds"]
                    }
                }
            },
            "required": ["event_id", "sport", "home_team", "away_team", "quotes"]
        }
    },
    {
        "name": "run_live_predictive_demo",
        "description": "Runs the full demonstration pipeline of the Shin-Shortcut calculator across sample NFL and NBA markets.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }
]


def _build_market(arguments: dict) -> MarketData:
    quotes = []
    for q in arguments.get("quotes", []):
        dec_odds = float(q["decimal_odds"])
        # Approximate american odds for display
        if dec_odds >= 2.0:
            us_odds = int(round((dec_odds - 1.0) * 100))
        else:
            us_odds = int(round(-100.0 / (dec_odds - 1.0))) if dec_odds > 1.0 else -9999
        implied_p = 1.0 / dec_odds if dec_odds > 0 else 0.0
        quotes.append(Quote(
            outcome_id=str(q["outcome_id"]),
            outcome_name=str(q["outcome_name"]),
            decimal_odds=dec_odds,
            american_odds=us_odds,
            implied_probability=implied_p
        ))

    return MarketData(
        event_id=arguments.get("event_id", "event-001"),
        sport=arguments.get("sport", "Generic"),
        home_team=arguments.get("home_team", "Home"),
        away_team=arguments.get("away_team", "Away"),
        market_type=arguments.get("market_type", "MONEYLINE"),
        bookmaker=arguments.get("bookmaker", "Consensus"),
        status=MarketStatus.ACTIVE,
        quotes=quotes
    )


def handle_tool_call(name: str, arguments: dict) -> dict:
    calc = ShinProbabilityCalculator()

    if name == "calculate_shin_shortcut":
        market = _build_market(arguments)
        res = calc.calculate_shin_shortcut(market)
        return {
            "event_id": market.event_id,
            "matchup": f"{market.away_team} @ {market.home_team}",
            "bookmaker": market.bookmaker,
            "method": res.method,
            "raw_overround": round(res.raw_overround, 5),
            "insider_fraction_z": round(res.insider_fraction_z, 6),
            "true_probabilities": {k: round(v, 6) for k, v in res.true_probabilities.items()},
            "is_valid": res.is_valid,
            "warnings": res.warnings
        }

    elif name == "calculate_power_devig":
        market = _build_market(arguments)
        res = calc.calculate_power_devig(market)
        return {
            "event_id": market.event_id,
            "matchup": f"{market.away_team} @ {market.home_team}",
            "method": res.method,
            "raw_overround": round(res.raw_overround, 5),
            "true_probabilities": {k: round(v, 6) for k, v in res.true_probabilities.items()},
            "is_valid": res.is_valid,
            "warnings": res.warnings
        }

    elif name == "evaluate_betting_decisions":
        market = _build_market(arguments)
        res = calc.calculate_shin_shortcut(market)
        bankroll = float(arguments.get("bankroll", 10000.0))
        min_ev = float(arguments.get("min_ev_threshold", 0.015))
        f_kelly = float(arguments.get("fractional_kelly", 0.25))

        engine = AutonomousDecisionEngine(bankroll=bankroll, min_ev_threshold=min_ev, fractional_kelly=f_kelly)
        opps = engine.evaluate_market(market, res)

        results = []
        for opp in opps:
            results.append({
                "outcome_id": opp.outcome_id,
                "outcome_name": opp.outcome_name,
                "offered_decimal_odds": opp.offered_decimal_odds,
                "true_probability_pct": round(opp.true_probability * 100, 2),
                "expected_value_pct": round(opp.expected_value_pct, 2),
                "action": opp.action,
                "recommended_stake_dollars": round(opp.recommended_stake_dollars, 2),
                "confidence_score": round(opp.confidence_score, 2),
                "insider_activity_index": round(opp.insider_activity_index, 4)
            })

        return {
            "event_id": market.event_id,
            "matchup": f"{market.away_team} @ {market.home_team}",
            "bankroll": bankroll,
            "min_ev_threshold_pct": min_ev * 100,
            "fractional_kelly": f_kelly,
            "opportunities": results
        }

    elif name == "run_live_predictive_demo":
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
        engine = AutonomousDecisionEngine(bankroll=10000.0, min_ev_threshold=0.015, fractional_kelly=0.25)
        demo_results = []
        for m in sample_markets:
            devig = calc.calculate_shin_shortcut(m)
            opps = engine.evaluate_market(m, devig)
            demo_results.append({
                "event": f"{m.away_team} @ {m.home_team}",
                "sport": m.sport,
                "bookmaker": m.bookmaker,
                "overround": round(devig.raw_overround, 4),
                "shin_z": round(devig.insider_fraction_z, 4),
                "true_probs": {k: round(v, 4) for k, v in devig.true_probabilities.items()},
                "opportunities": [
                    {
                        "outcome": o.outcome_name,
                        "odds": o.offered_decimal_odds,
                        "ev_pct": round(o.expected_value_pct, 2),
                        "action": o.action,
                        "stake": round(o.recommended_stake_dollars, 2)
                    } for o in opps
                ]
            })
        return {"status": "success", "demo_markets": demo_results}

    else:
        raise ValueError(f"Unknown tool: {name}")


def main():
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue

            req = json.loads(line)
            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params", {})

            if method == "initialize":
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "predictive-ai-core",
                            "version": "1.0.0"
                        }
                    }
                }
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()

            elif method == "notifications/initialized":
                pass

            elif method == "tools/list":
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "tools": TOOLS
                    }
                }
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()

            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                try:
                    result = handle_tool_call(tool_name, arguments)
                    resp = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(result, indent=2)
                                }
                            ]
                        }
                    }
                except Exception as e:
                    resp = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {
                            "code": -32603,
                            "message": str(e),
                            "data": traceback.format_exc()
                        }
                    }
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()

            elif method == "ping":
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {}
                }
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()

            else:
                if req_id is not None:
                    resp = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {
                            "code": -32601,
                            "message": f"Method '{method}' not found"
                        }
                    }
                    sys.stdout.write(json.dumps(resp) + "\n")
                    sys.stdout.flush()

        except Exception as e:
            sys.stderr.write(f"MCP Server error: {e}\n")
            sys.stderr.flush()


if __name__ == "__main__":
    main()
