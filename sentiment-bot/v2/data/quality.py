"""V2 Data desk: data contracts + quality SLA. Freshness, gaps, sanity bounds.
Bad candles or stale quotes never reach the signal engine."""
from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class DataQualitySLA:
    max_quote_age_s: float = 30.0
    max_price_change: float = 0.25      # 25% single-tick move = almost surely bad data
    min_price: float = 0.0


class MarketDataValidator:
    def __init__(self, sla: DataQualitySLA | None = None) -> None:
        self.sla = sla or DataQualitySLA()
        self._last_price: dict = {}

    def validate(self, snap) -> bool:
        if snap.price <= self.sla.min_price or snap.rsi < 0 or snap.rsi > 100:
            return False
        if abs(time.time() - snap.ts.timestamp()) > self.sla.max_quote_age_s:
            return False
        last = self._last_price.get(snap.pair)
        if last and abs(snap.price / last - 1) > self.sla.max_price_change:
            return False
        self._last_price[snap.pair] = snap.price
        return True
