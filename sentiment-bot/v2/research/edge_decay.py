"""V2 Edge-decay monitor: live rolling Sharpe vs backtest confidence band.
When live performance exits the band, the mode is auto-demoted - the fund
knows the edge is dead before the P&L proves it."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque


@dataclass
class DecayMonitor:
    backtest_sharpe: float
    band: float = 0.5       # live Sharpe below (backtest - band) -> demote
    window: int = 100        # trades in the rolling window

    def __init__(self, backtest_sharpe: float, band: float = 0.5, window: int = 100) -> None:
        self.backtest_sharpe = backtest_sharpe
        self.band = band
        self.window = window
        self._returns: Deque[float] = deque(maxlen=window)

    def record(self, ret: float) -> None:
        self._returns.append(ret)

    def live_sharpe(self) -> float:
        rs = list(self._returns)
        if len(rs) < 20:
            return self.backtest_sharpe  # not enough data: assume no decay
        mean = sum(rs) / len(rs)
        var = sum((r - mean) ** 2 for r in rs) / len(rs)
        sd = var ** 0.5
        if sd == 0:
            return 0.0
        return mean / sd * (len(rs) ** 0.5)

    def should_demote(self) -> bool:
        return self.live_sharpe() < self.backtest_sharpe - self.band
