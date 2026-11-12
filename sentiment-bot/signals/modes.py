"""Mode stack, strict priority (not a vote): contrarian > momentum > TA-only.

The highest-priority mode with valid inputs fires. Sentiment-only is never
allowed; TA-only is the floor that keeps the bot alive when degraded.
"""
from __future__ import annotations

from collections import defaultdict, deque
from typing import Deque

from core.schema import Direction, MarketSnapshot, ScoredPost, Signal
from signals.regime import Regime, SentimentBaseline


class ModeStack:
    def __init__(self, experiment_id: str = "exp-001-sentiment-v1") -> None:
        self.baseline = SentimentBaseline()
        self._per_asset: dict = defaultdict(lambda: deque(maxlen=100))
        self.experiment_id = experiment_id

    def aggregate(self, scored: ScoredPost) -> None:
        w = 1.0 + min(3.0, scored.post.author_followers / 100_000) + min(2.0, scored.post.engagement / 1000)
        s = scored.confidence * (1 if scored.direction == Direction.LONG else -1) * w
        for m in scored.post.mentions or ("BTC",):
            self._per_asset[m].append((s, scored.is_uncertain))

    def asset_score(self, asset: str) -> tuple:
        entries = [s for s, u in self._per_asset.get(asset, ()) if not u]
        if not entries:
            return 0.0, 0
        return sum(entries) / len(entries), len(entries)

    def evaluate(self, asset: str, snap: MarketSnapshot, regime: Regime) -> Signal | None:
        score, n = self.asset_score(asset)
        self.baseline.update(score)
        pct = self.baseline.percentile(score)

        # Mode 1 (primary): contrarian at statistical extremes
        if pct > 0.95:
            return Signal(pair=asset, direction=Direction.SHORT, mode="contrarian", confidence=0.7, reason=f"euphoria extreme p={pct:.2f}", experiment_id=self.experiment_id)
        if pct < 0.05 and n >= 5:
            return Signal(pair=asset, direction=Direction.LONG, mode="contrarian", confidence=0.7, reason=f"capitulation stabilizing p={pct:.2f}", experiment_id=self.experiment_id)

        # Mode 2: momentum shift with TA agreement
        if abs(score) > 0.6 and n >= 5:
            direction = Direction.LONG if score > 0 else Direction.SHORT
            if self._ta_agrees(direction, snap, regime):
                return Signal(pair=asset, direction=direction, mode="momentum", confidence=min(0.9, abs(score)), reason=f"sentiment momentum score={score:.2f} n={n}", experiment_id=self.experiment_id)
            return None  # sentiment-only is vetoed: no TA agreement, no trade

        # Mode 3: TA-only floor
        if self._ta_agrees(Direction.LONG, snap, regime) and snap.rsi < 30:
            return Signal(pair=asset, direction=Direction.LONG, mode="ta_only", confidence=0.5, reason="oversold in bull regime", experiment_id=self.experiment_id)
        return None

    @staticmethod
    def _ta_agrees(direction: Direction, snap: MarketSnapshot, regime: Regime) -> bool:
        if direction == Direction.LONG:
            return regime == Regime.BULL and snap.price > snap.ema50 and snap.rsi > 40
        return regime == Regime.BEAR and snap.price < snap.ema50 and snap.rsi < 60
