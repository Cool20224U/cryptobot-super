"""V1 runner: logger-first wiring. Ingest -> bot filter -> scorers -> mode stack
-> gate -> risk -> executor, all on the event bus, everything stored.

Default mode is LOGGER-ONLY (paper executor, no exchange keys). Do not promote
to a live executor until backtest + fallback drills pass.
"""
from __future__ import annotations

import logging
import os
import time

from core.bus import EventBus
from core.health import HealthMonitor
from core.schema import Direction, MarketSnapshot, RawPost, ScoredPost, Severity
from exec.paper import PaperExecutor
from ingest.coarse import CoarseSource
from ingest.x_stream import XStream
from risk.manager import RiskManager
from score.base import BotFilter
from score.lexicon import LexiconScorer
from score.llm import LLMScorer
from signals.gate import SignalGate
from signals.modes import ModeStack
from signals.regime import RegimeDetector
from ops.store import EventStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("main")

POLL_SECONDS = int(os.getenv("POLL_SECONDS", "60"))


def ta_check(signal, snap) -> bool:
    if signal.direction == Direction.LONG:
        return snap.price > snap.ema50 and snap.rsi > 40
    return snap.price < snap.ema50 and snap.rsi < 60


def main() -> None:
    bus = EventBus()
    store = EventStore(os.getenv("EVENT_STORE", "data/events.jsonl"))
    health = HealthMonitor(bus, ["ingest.x_stream", "ingest.aggregator", "ingest.coarse", "score.llm"])
    for topic in ("posts.raw", "posts.scored", "signals", "orders", "health"):
        bus.subscribe(topic, (lambda t: (lambda ev: store.append(t, ev)))(topic))

    sources = [XStream(bus), CoarseSource(bus)]
    bot_filter = BotFilter()
    lexicon = LexiconScorer(bus)
    llm = LLMScorer(bus)
    modes = ModeStack()
    gate = SignalGate(ta_check)
    risk = RiskManager()
    executor = PaperExecutor(bus)
    regime = RegimeDetector()

    def on_raw(post: RawPost) -> None:
        if not bot_filter.allow(post):
            return
        scored = llm.score_batch([post]) or lexicon.score_batch([post])
        for s in scored:
            if not s.is_uncertain:
                bus.publish("posts.scored", s)
                modes.aggregate(s)

    bus.subscribe("posts.raw", on_raw)

    def on_snapshot(snap: MarketSnapshot) -> None:
        r = regime.update(snap)
        for asset in list(modes._per_asset.keys()) or ["BTC"]:
            sig = modes.evaluate(asset, snap, r)
            if sig is None:
                continue
            bus.publish("signals", sig)
            if gate.authorize(sig, snap) is None:
                continue
            intent = risk.size_order(sig)
            if risk.approve(intent):
                executor.execute(intent)

    bus.subscribe("market.snapshot", on_snapshot)

    log.info("sentiment-bot V1 starting in LOGGER-ONLY mode (paper executor)")
    while True:
        health.tick()
        for src in sources:
            try:
                for post in src.poll():
                    src.emit(post)
            except Exception:
                bus.publish_health(f"ingest.{src.name}", Severity.CRITICAL, "poll failed")
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
