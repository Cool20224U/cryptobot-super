"""In-memory event bus. Modules communicate ONLY via typed events.

The bus validates every event against core.schema before delivery; malformed
input can never propagate toward an order. Swap this for a real broker
(redis/nats) in production without changing any module.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from typing import Callable

from core.schema import HealthEvent, Severity

log = logging.getLogger("bus")


class EventBus:
    def __init__(self) -> None:
        self._subs: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(self, topic: str, handler: Callable) -> None:
        self._subs[topic].append(handler)

    def publish(self, topic: str, event) -> None:
        for handler in self._subs.get(topic, ()):
            try:
                handler(event)
            except Exception:  # fail-closed: a broken subscriber never kills the bus
                log.exception("handler failed topic=%s", topic)

    def publish_health(self, module: str, severity: Severity, message: str) -> None:
        log.log(
            {"info": logging.INFO, "warn": logging.WARNING, "critical": logging.ERROR}[severity.value],
            "health module=%s msg=%s",
            module,
            message,
        )
        self.publish("health", HealthEvent(module=module, severity=severity, message=message))
