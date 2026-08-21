---
name: sports-prediction
description: "Autonomous sports outcome prediction and +EV betting intelligence suite for NBA and NFL."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [SportsBetting, MachineLearning, NBA, NFL, OddsComparison, KellyCriterion, EV, Analytics]
    related_skills: [web-extraction, auto-scraper, shopping-comparison]
---

# Autonomous Sports Prediction & +EV Betting Intelligence Agent

A modular, statistical machine-learning prediction and betting intelligence engine designed for Hermes Agent. It combines real-time/historical odds, team efficiencies, pace metrics, situational data (weather, rest, injuries), and vig-free fair price calculations to detect positive expected value (+EV) betting opportunities across NBA and NFL markets.

---

## 1. Features

- **Multi-Sport Coverage**: Full support for **NBA (Basketball)** and **NFL (American Football)**, including Moneyline, Spreads, Over/Under Totals, and Player Props (Points, Rebounds, Assists, Passing/Rushing/Receiving Yards).
- **Vig-Free Fair Odds**: Calculates true implied probabilities using Shin's method and proportional normalization across major sportsbooks (DraftKings, FanDuel, Bet365, Pinnacle, etc.).
- **Machine Learning Ensemble**: XGBoost, LightGBM, and regularized Logistic Regression with Platt Scaling / Isotonic Calibration to output true probabilities instead of raw scores.
- **Risk Management & Staking**: Dynamic Fractional Kelly Criterion staking (e.g., 1/4 Kelly) with hard bankroll percentage caps to protect capital against drawdowns.
- **Paper Trading by Default**: Safe SQLite-backed simulation database tracking every prediction, wager, closing line value (CLV), and historical ROI before risking capital.
- **Offline Mock & Live API Dual-Mode**: Built-in mock data generator for instant zero-dependency testing, alongside live API connectors for **The Odds API**, **Sportsdata.io**, and **OpenWeatherMap**.

---

## 2. Quick Invocation

Run from the command line or inside Hermes:

```bash
# 1. Train & calibrate the prediction models
python skills/research/sports-prediction/scripts/run_sports_prediction.py --action train --sport basketball_nba

# 2. Run an autonomous paper-trading prediction cycle for NBA
python skills/research/sports-prediction/scripts/run_sports_prediction.py --action run --sport basketball_nba --paper

# 3. Run a prediction cycle for NFL with custom bankroll and edge threshold
python skills/research/sports-prediction/scripts/run_sports_prediction.py --action run --sport americanfootball_nfl --bankroll 2500 --edge-threshold 0.03

# 4. View historical betting performance, win rates, and ROI
python skills/research/sports-prediction/scripts/run_sports_prediction.py --action report
```

---

## 3. Architecture & Data Flow

```
[The Odds API / Sportsdata.io / OpenWeatherMap / Mock Data]
                         │
                         ▼
           1. Unified Ingestion & Normalization
          (Standardizes odds, markets, team names)
                         │
                         ▼
        2. Feature Engineering & Feature Store
       (Efficiencies, pace, rest days, injuries, Shin vig)
                         │
                         ▼
         3. Calibrated ML Probability Models
           (XGBoost / LightGBM / Logistic Ensemble)
                         │
                         ▼
         4. Edge Detection & Kelly Staking
       (Identifies +EV wagers & computes optimal stake)
                         │
                         ▼
     5. Execution & SQLite Analytics Database
       (Logs predictions, wagers, and tracks CLV / ROI)
```

---

## 4. API Keys & Configuration (Optional)

Configure via environment variables or `~/.hermes/.env`:
- `ODDS_API_KEY`: API key for [The Odds API](https://the-odds-api.com/)
- `SPORTSDATA_API_KEY`: API key for [Sportsdata.io](https://sportsdata.io/)
- `OPENWEATHER_API_KEY`: API key for [OpenWeatherMap](https://openweathermap.org/)

*If no keys are provided, the suite automatically falls back to high-fidelity mock data providers for seamless testing.*
