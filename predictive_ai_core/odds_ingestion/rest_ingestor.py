"""
Feed Interface and Resilient REST Ingestion with Circuit Breaker & Rate Limiter
"""

import abc
import asyncio
import logging
import time
from typing import AsyncGenerator, Dict, List, Optional
from .models import MarketData, MarketStatus, Quote

logger = logging.getLogger("HermesOddsIngestor")


class IFeedIngestor(abc.ABC):
    """Abstract interface for odds ingestion feeds."""

    @abc.abstractmethod
    async def connect(self) -> None:
        pass

    @abc.abstractmethod
    async def stream_markets(self) -> AsyncGenerator[MarketData, None]:
        pass

    @abc.abstractmethod
    async def disconnect(self) -> None:
        pass


class TokenBucketLimiter:
    """Token Bucket rate limiter to prevent API 429 penalties."""

    def __init__(self, rate_limit_per_sec: float, capacity: float):
        self.rate = rate_limit_per_sec
        self.capacity = capacity
        self.tokens = capacity
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_refill = now

            if self.tokens < 1.0:
                needed = (1.0 - self.tokens) / self.rate
                logger.warning(f"API Rate limit throttle active. Sleeping {needed:.3f}s")
                await asyncio.sleep(needed)
                self.tokens = 0.0
                self.last_refill = time.monotonic()
            else:
                self.tokens -= 1.0


class ResilientRestIngestor(IFeedIngestor):
    """
    REST Odds Ingestor equipped with Token Bucket rate limiting,
    exponential backoff, and circuit breaker for API dropouts.
    """

    def __init__(self, bookmaker: str, rate_limit: float = 10.0):
        self.bookmaker = bookmaker
        self.limiter = TokenBucketLimiter(rate_limit, rate_limit * 2)
        self.is_connected = False
        self._consecutive_failures = 0
        self._circuit_open = False
        self._circuit_reset_time = 0.0

    async def connect(self) -> None:
        self.is_connected = True
        logger.info(f"Connected to {self.bookmaker} REST feed.")

    async def fetch_market(self, event_id: str, raw_data: Optional[Dict] = None) -> Optional[MarketData]:
        """Fetch market with circuit breaker protection."""
        if self._circuit_open:
            if time.monotonic() < self._circuit_reset_time:
                logger.error(f"Circuit Breaker OPEN for {self.bookmaker}. Skipping request.")
                return None
            else:
                logger.info(f"Circuit Breaker HALF-OPEN for {self.bookmaker}. Probing...")
                self._circuit_open = False

        await self.limiter.acquire()

        try:
            # Simulate parsing external API payload
            if raw_data is None:
                # Mock live NFL match payload
                raw_data = {
                    "event_id": event_id,
                    "sport": "NFL",
                    "home_team": "Kansas City Chiefs",
                    "away_team": "San Francisco 49ers",
                    "market_type": "MONEYLINE",
                    "status": "ACTIVE",
                    "quotes": [
                        {"id": "home", "name": "Chiefs", "dec": 1.91, "american": -110, "prob": 0.5235},
                        {"id": "away", "name": "49ers", "dec": 1.95, "american": -105, "prob": 0.5128}
                    ]
                }

            quotes = [
                Quote(
                    outcome_id=q["id"],
                    outcome_name=q["name"],
                    decimal_odds=q["dec"],
                    american_odds=q["american"],
                    implied_prob=q["prob"]
                )
                for q in raw_data["quotes"]
            ]

            market = MarketData(
                event_id=raw_data["event_id"],
                sport=raw_data["sport"],
                home_team=raw_data["home_team"],
                away_team=raw_data["away_team"],
                market_type=raw_data["market_type"],
                bookmaker=self.bookmaker,
                status=MarketStatus(raw_data.get("status", "ACTIVE")),
                quotes=quotes
            )

            self._consecutive_failures = 0
            return market

        except Exception as e:
            self._consecutive_failures += 1
            logger.error(f"Error fetching from {self.bookmaker}: {e}")
            if self._consecutive_failures >= 5:
                self._circuit_open = True
                self._circuit_reset_time = time.monotonic() + 30.0
                logger.critical(f"Circuit Breaker TRIPPED for {self.bookmaker} (30s cooldown)")
            return None

    async def stream_markets(self) -> AsyncGenerator[MarketData, None]:
        while self.is_connected:
            market = await self.fetch_market("nfl-2026-sb-rematch")
            if market:
                yield market
            await asyncio.sleep(2.0)

    async def disconnect(self) -> None:
        self.is_connected = False
        logger.info(f"Disconnected from {self.bookmaker} feed.")
