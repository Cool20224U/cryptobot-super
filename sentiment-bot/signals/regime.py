"""Market regime detection: bull / bear / chop + rolling sentiment baseline."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Deque

from core.schema import MarketSnapshot


class Regime(str, Enum):
    BULL = "bull"
    BEAR = "bear"
    CHOP = "chop"


@dataclass
class RegimeDetector:
    window: int = 200

    def __init__(self, window: int = 200) -> None:
        self.window = window
        self._closes: Deque[float] = deque(maxlen=window)

    def update(self, snap: MarketSnapshot) -> Regime:
        self._closes.append(snap.price)
        if len(self._closes) < 50:
            return Regime.CHOP
        recent = list(self._closes)
        fast, slow = sum(recent[-20:]) / 20, sum(recent) / len(recent)
        vol = max(recent) / min(recent) - 1
        if vol < 0.02:
            return Regime.CHOP
        return Regime.BULL if fast > slow else Regime.BEAR


class SentimentBaseline:
    """Rolling percentile bands for contrarian extremes (95th / 5th)."""

    def __init__(self, window: int = 500) -> None:
        self._scores: Deque[float] = deque(maxlen=window)

    def update(self, score: float) -> None:
        self._scores.append(score)

    def percentile(self, score: float) -> float:
        if not self._scores:
            return 0.5
        below = sum(1 for s in self._scores if s <= score)
        return below / len(self._scores)
