"""Per-module health tracking + explicit degradation ladder.

Ladder: PRIMARY -> FALLBACK_A -> FALLBACK_B -> FLAT. Degrading always means
trading LESS (smaller size or no new entries), never more.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum

from core.bus import EventBus
from core.schema import HealthEvent, Severity

CHECK_INTERVAL = 60.0
STALE_AFTER = 180.0


class Level(str, Enum):
    PRIMARY = "primary"
    FALLBACK_A = "fallback_a"
    FALLBACK_B = "fallback_b"
    FLAT = "flat"


LADDER = [Level.PRIMARY, Level.FALLBACK_A, Level.FALLBACK_B, Level.FLAT]


@dataclass
class ModuleHealth:
    last_ok: float = 0.0
    current: Level = Level.PRIMARY

    def degrade(self) -> None:
        idx = LADDER.index(self.current)
        self.current = LADDER[min(idx + 1, len(LADDER) - 1)]


class HealthMonitor:
    def __init__(self, bus: EventBus, modules: list[str]) -> None:
        self.bus = bus
        self.state: dict[str, ModuleHealth] = {m: ModuleHealth() for m in modules}
        bus.subscribe("health", self._on_health)
        bus.subscribe("heartbeat", self._on_heartbeat)

    def _on_heartbeat(self, event: HealthEvent) -> None:
        h = self.state.get(event.module)
        if h is not None:
            h.last_ok = time.time()

    def _on_health(self, event: HealthEvent) -> None:
        h = self.state.get(event.module)
        if h is None:
            return
        if event.severity == Severity.CRITICAL:
            h.degrade()
            self.bus.publish_health("health", Severity.WARN, f"{event.module} -> {h.current.value}")

    def tick(self) -> None:
        now = time.time()
        for name, h in self.state.items():
            if h.last_ok and now - h.last_ok > STALE_AFTER and h.current != Level.FLAT:
                h.degrade()
                self.bus.publish_health("health", Severity.WARN, f"{name} stale -> {h.current.value}")

    def level(self, module: str) -> Level:
        return self.state[module].current
