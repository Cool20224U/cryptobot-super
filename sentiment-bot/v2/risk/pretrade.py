"""V2 Risk desk: pre-trade risk as a SEPARATE service. Three-key authorization:
signal gate -> pre-trade risk -> executor. Validates every OrderIntent against
portfolio limits before the executor ever sees it."""
from __future__ import annotations

from dataclasses import dataclass, field

from core.schema import Direction, OrderIntent


@dataclass
class PortfolioLimits:
    net_exposure_pct: float = 0.30        # |sum exposure| <= 30% equity
    per_asset_pct: float = 0.10            # 10% equity per asset
    correlated_cluster_pct: float = 0.20  # alt-coin cluster treated as one beta


CORRELATED = {"SOL/USDT", "DOGE/USDT", "PEPE/USDT"}


class PreTradeRisk:
    def __init__(self, equity: float = 10_000.0, limits: PortfolioLimits | None = None) -> None:
        self.equity = equity
        self.limits = limits or PortfolioLimits()
        self.exposure: dict = {}

    def check(self, intent: OrderIntent) -> bool:
        if intent.direction == Direction.NEUTRAL:
            return False
        size = intent.size_quote
        if self.exposure.get(intent.pair, 0.0) + size > self.equity * self.limits.per_asset_pct:
            return False
        net = sum(self.exposure.values()) + size
        if abs(net) > self.equity * self.limits.net_exposure_pct:
            return False
        cluster = sum(v for k, v in self.exposure.items() if k in CORRELATED)
        if intent.pair in CORRELATED and cluster + size > self.equity * self.limits.correlated_cluster_pct:
            return False
        return True

    def on_fill(self, intent: OrderIntent) -> None:
        sign = 1 if intent.direction == Direction.LONG else -1
        self.exposure[intent.pair] = self.exposure.get(intent.pair, 0.0) + sign * intent.size_quote
