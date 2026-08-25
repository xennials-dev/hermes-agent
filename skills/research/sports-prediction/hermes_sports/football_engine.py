"""
Hermes Agent: Football (NFL & CFB) CLV & Prop Market Inefficiency Engine.
Treats sports betting as high-frequency trading (HFT) by monitoring sharp market-making
anchors (Pinnacle / Circa) and detecting retail lag across spreads (1Q, 1H, Full Game)
and player props with key number crossing evaluation and logarithmic vig-stripping.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

from hermes_sports.vig import VigStripper

logger = logging.getLogger(__name__)

# Scoring cluster constants for football
PRIMARY_KEY_NUMBERS = [3, 7]
SECONDARY_KEY_NUMBERS = [6, 10, 14]
ALL_KEY_NUMBERS = PRIMARY_KEY_NUMBERS + SECONDARY_KEY_NUMBERS


class FootballKeyNumberEvaluator:
    """
    Weights expected value based on whether a retail line discrepancy crosses
    critical football scoring clusters (3, 7, 6, 10, 14).
    """

    @staticmethod
    def calculate_weighted_edge(
        retail_line: float, sharp_line: float, raw_ev_edge: float, is_cfb: bool = False
    ) -> float:
        """
        Applies key number crossing multipliers to scaled edges.
        """
        r_mag = abs(retail_line)
        s_mag = abs(sharp_line)
        low_bound = min(r_mag, s_mag)
        high_bound = max(r_mag, s_mag)

        # Detect key numbers strictly between the retail and sharp lines
        crossed_keys = [k for k in ALL_KEY_NUMBERS if low_bound < k < high_bound]

        if not crossed_keys:
            return round(raw_ev_edge, 4)

        multiplier = 1.0
        for k in crossed_keys:
            if k in PRIMARY_KEY_NUMBERS:
                multiplier += 1.5  # Critical primary keys (3, 7)
            else:
                multiplier += 0.8  # Secondary keys (6, 10, 14)

        if is_cfb:
            multiplier *= 1.15  # Additional volatility buffer for College Football

        return round(raw_ev_edge * multiplier, 4)


class FootballCLVEngine:
    """
    Real-time market scanning and discrepancy detection engine for NFL and CFB.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        sharp_anchors: Optional[List[str]] = None,
        min_ev_edge: float = 0.02,
    ):
        self.api_key = api_key or os.getenv("ODDS_API_KEY", "")
        self.sharp_anchors = [s.lower() for s in (sharp_anchors or ["pinnacle", "circa", "circa_sports"])]
        self.min_ev_edge = min_ev_edge

    def fetch_live_odds(
        self,
        sport: str = "americanfootball_nfl",
        markets: str = "spreads,spreads_h1,player_pass_yds,player_anytime_td",
        regions: str = "us,eu",
    ) -> List[Dict[str, Any]]:
        """
        Fetches structured real-time odds from The Odds API endpoint.
        """
        if not self.api_key:
            logger.warning("ODDS_API_KEY unconfigured. Returning mock dataset.")
            return self._generate_mock_football_payload(sport)

        url = (
            f"https://api.the-odds-api.com/v4/sports/{sport}/odds/?"
            + urllib.parse.urlencode(
                {
                    "apiKey": self.api_key,
                    "regions": regions,
                    "markets": markets,
                    "oddsFormat": "american",
                }
            )
        )

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Hermes-Agent-Sports-CLV/2.1"})
            with urllib.request.urlopen(req, timeout=12) as res:
                if res.status == 200:
                    return json.loads(res.read().decode("utf-8"))
        except Exception as e:
            logger.error(f"Failed to fetch live football odds: {e}")

        return self._generate_mock_football_payload(sport)

    def scan_market_discrepancies(
        self,
        events: List[Dict[str, Any]],
        sport_key: str = "americanfootball_nfl",
    ) -> List[Dict[str, Any]]:
        """
        Processes events, isolates sharp lines, strips vig via Logarithmic/Multiplicative models,
        applies key number weights, and surfaces +EV alerts.
        """
        alerts = []
        is_cfb = "ncaaf" in sport_key.lower()

        for event in events:
            home = event.get("home_team", "Home")
            away = event.get("away_team", "Away")
            matchup = f"{away} @ {home}"
            bookmakers = {b["key"].lower(): b for b in event.get("bookmakers", [])}

            # Find active sharp bookmaker
            sharp_b = None
            sharp_name = "pinnacle"
            for s_anchor in self.sharp_anchors:
                if s_anchor in bookmakers:
                    sharp_b = bookmakers[s_anchor]
                    sharp_name = s_anchor
                    break

            if not sharp_b:
                continue

            for s_market in sharp_b.get("markets", []):
                mkey = s_market.get("key", "")
                is_prop = mkey.startswith("player_")
                is_derivative = mkey in ("spreads_h1", "spreads_q1", "player_anytime_td")

                # Map sharp outcomes
                outcomes = s_market.get("outcomes", [])
                if len(outcomes) < 2:
                    continue

                if is_prop:
                    # Player Prop line matching
                    player_groups: Dict[str, Dict[str, Any]] = {}
                    for o in outcomes:
                        pname = o.get("description", o.get("name", "Unknown"))
                        player_groups.setdefault(pname, {})[o.get("name", "").lower()] = o

                    for pname, sides in player_groups.items():
                        if "over" in sides and "under" in sides:
                            s_over_odds = int(sides["over"]["price"])
                            s_under_odds = int(sides["under"]["price"])
                            point = float(sides["over"].get("point", 0.0))

                            # Logarithmic Shin-Shortcut for volatile props
                            fair_over, fair_under, overround = VigStripper.logarithmic_method(
                                s_over_odds, s_under_odds
                            )

                            for bkey, bdata in bookmakers.items():
                                if bkey in self.sharp_anchors:
                                    continue
                                for rm in bdata.get("markets", []):
                                    if rm.get("key") == mkey:
                                        for ro in rm.get("outcomes", []):
                                            rname = ro.get("description", ro.get("name", ""))
                                            rpoint = float(ro.get("point", 0.0))
                                            rside = ro.get("name", "Over").upper()

                                            if rname == pname and rpoint == point:
                                                r_odds = int(ro.get("price", 100))
                                                r_ip = VigStripper.american_to_implied(r_odds)
                                                target_fair = fair_over if rside == "OVER" else fair_under
                                                s_odds = s_over_odds if rside == "OVER" else s_under_odds
                                                s_ip = VigStripper.american_to_implied(s_odds)

                                                raw_ev = (target_fair / r_ip) - 1.0 if r_ip > 0 else 0.0
                                                clv = ((s_ip / r_ip) - 1.0) * 100.0 if r_ip > 0 else 0.0

                                                if raw_ev >= self.min_ev_edge:
                                                    alerts.append(
                                                        {
                                                            "type": "prop",
                                                            "market": mkey,
                                                            "player": pname,
                                                            "matchup": matchup,
                                                            "line": point,
                                                            "side": rside,
                                                            "retail_book": bdata.get("title", bkey),
                                                            "retail_odds": r_odds,
                                                            "sharp_book": sharp_name,
                                                            "sharp_odds": s_odds,
                                                            "fair_probability": round(target_fair, 4),
                                                            "ev_edge": round(raw_ev, 4),
                                                            "clv_edge": round(clv, 2),
                                                            "math_method": "logarithmic",
                                                        }
                                                    )
                else:
                    # Game Spread / Derivative Spread matching
                    s_home = next((o for o in outcomes if o.get("name") == home), None)
                    s_away = next((o for o in outcomes if o.get("name") == away), None)

                    if s_home and s_away:
                        s_h_odds = int(s_home.get("price", -110))
                        s_a_odds = int(s_away.get("price", -110))
                        s_h_point = float(s_home.get("point", 0.0))

                        # Choose Math Engine: Logarithmic for 1H/1Q, Multiplicative for Full Game
                        if is_derivative:
                            fair_h, fair_a, _ = VigStripper.logarithmic_method(s_h_odds, s_a_odds)
                            math_m = "logarithmic"
                        else:
                            fair_h, fair_a, _ = VigStripper.multiplicative_method(s_h_odds, s_a_odds)
                            math_m = "multiplicative"

                        for bkey, bdata in bookmakers.items():
                            if bkey in self.sharp_anchors:
                                continue
                            for rm in bdata.get("markets", []):
                                if rm.get("key") == mkey:
                                    r_home = next((o for o in rm.get("outcomes", []) if o.get("name") == home), None)
                                    if r_home:
                                        r_odds = int(r_home.get("price", -110))
                                        r_point = float(r_home.get("point", 0.0))
                                        r_ip = VigStripper.american_to_implied(r_odds)
                                        s_ip = VigStripper.american_to_implied(s_h_odds)

                                        price_ev = (fair_h / r_ip) - 1.0 if r_ip > 0 else 0.0
                                        # Point difference advantage (e.g., getting -2.5 when sharp is -3.5)
                                        point_advantage = (r_point - s_h_point) if s_h_point < 0 else (s_h_point - r_point)
                                        point_edge = max(0.0, point_advantage * 0.035)
                                        base_ev = max(price_ev, price_ev + point_edge if point_advantage > 0 else price_ev)

                                        weighted_ev = FootballKeyNumberEvaluator.calculate_weighted_edge(
                                            r_point, s_h_point, base_ev, is_cfb=is_cfb
                                        )
                                        clv = ((s_ip / r_ip) - 1.0) * 100.0 if r_ip > 0 else 0.0

                                        if weighted_ev >= self.min_ev_edge:
                                            alerts.append(
                                                {
                                                    "type": "spread",
                                                    "market": mkey,
                                                    "team": home,
                                                    "matchup": matchup,
                                                    "retail_line": r_point,
                                                    "sharp_line": s_h_point,
                                                    "retail_book": bdata.get("title", bkey),
                                                    "retail_odds": r_odds,
                                                    "sharp_book": sharp_name,
                                                    "sharp_odds": s_h_odds,
                                                    "fair_probability": round(fair_h, 4),
                                                    "ev_edge": round(weighted_ev, 4),
                                                    "clv_edge": round(clv, 2),
                                                    "math_method": math_m,
                                                }
                                            )
        return alerts

    def send_telegram_alert(
        self,
        alert: Dict[str, Any],
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
    ) -> bool:
        """
        Sends an instantaneous Telegram message when a +EV CLV edge is detected.
        """
        token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        cid = chat_id or os.getenv("TELEGRAM_CHAT_ID", "13143483944")

        if not token:
            logger.info("[TELEGRAM MOCK ALERT] " + json.dumps(alert))
            return True

        if alert.get("type") == "prop":
            text = (
                f"🏈 *HERMES +EV CLV PROP ALERT*\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"👤 *Player:* {alert['player']}\n"
                f"🏟️ *Matchup:* {alert['matchup']}\n"
                f"🎯 *Market:* `{alert['market']}` ({alert['line']} Units)\n"
                f"⚡ *Direction:* *{alert['side']}*\n"
                f"🏦 *Retail Book:* {alert['retail_book']} (Odds `{alert['retail_odds']:+d}`)\n"
                f"⚓ *Sharp Anchor:* {alert['sharp_book']} (`{alert['sharp_odds']:+d}`)\n"
                f"📊 *Fair Prob:* `{alert['fair_probability']:.2%}` ({alert['math_method']})\n"
                f"💰 *Expected Value (+EV):* `+{alert['ev_edge']:.2%}`\n"
                f"📈 *Closing Line Value:* `+{alert['clv_edge']:.2%}`\n"
            )
        else:
            text = (
                f"🏈 *HERMES +EV FOOTBALL SPREAD ALERT*\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"🏟️ *Matchup:* {alert['matchup']}\n"
                f"🛡️ *Target Team:* *{alert.get('team', '')}*\n"
                f"🎯 *Market:* `{alert['market']}`\n"
                f"🏦 *Retail Line:* {alert['retail_book']} `{alert['retail_line']:+.1f}` (Odds `{alert['retail_odds']:+d}`)\n"
                f"⚓ *Sharp Line:* {alert['sharp_book']} `{alert['sharp_line']:+.1f}` (Odds `{alert['sharp_odds']:+d}`)\n"
                f"💰 *Weighted +EV Edge:* `+{alert['ev_edge']:.2%}`\n"
                f"📈 *Closing Line Value:* `+{alert['clv_edge']:.2%}`\n"
            )

        send_url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = json.dumps({"chat_id": cid, "text": text, "parse_mode": "Markdown"}).encode("utf-8")

        try:
            req = urllib.request.Request(
                send_url, data=payload, headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status == 200
        except Exception as e:
            logger.error(f"Failed to deliver Telegram alert: {e}")
            return False

    def _generate_mock_football_payload(self, sport: str) -> List[Dict[str, Any]]:
        return [
            {
                "id": "game_chiefs_ravens_2026",
                "sport_key": sport,
                "home_team": "Kansas City Chiefs",
                "away_team": "Baltimore Ravens",
                "bookmakers": [
                    {
                        "key": "pinnacle",
                        "title": "Pinnacle",
                        "markets": [
                            {
                                "key": "spreads_h1",
                                "outcomes": [
                                    {"name": "Kansas City Chiefs", "price": -115, "point": -3.5},
                                    {"name": "Baltimore Ravens", "price": -105, "point": 3.5},
                                ],
                            },
                            {
                                "key": "player_pass_yds",
                                "outcomes": [
                                    {"name": "Over", "description": "Patrick Mahomes", "price": -135, "point": 268.5},
                                    {"name": "Under", "description": "Patrick Mahomes", "price": 105, "point": 268.5},
                                ],
                            },
                        ],
                    },
                    {
                        "key": "draftkings",
                        "title": "DraftKings",
                        "markets": [
                            {
                                "key": "spreads_h1",
                                "outcomes": [
                                    {"name": "Kansas City Chiefs", "price": -110, "point": -2.5},
                                    {"name": "Baltimore Ravens", "price": -110, "point": 2.5},
                                ],
                            },
                            {
                                "key": "player_pass_yds",
                                "outcomes": [
                                    {"name": "Over", "description": "Patrick Mahomes", "price": 105, "point": 268.5},
                                    {"name": "Under", "description": "Patrick Mahomes", "price": -135, "point": 268.5},
                                ],
                            },
                        ],
                    },
                ],
            }
        ]
