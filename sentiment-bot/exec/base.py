"""Executor protocol. Only this module can place orders, and only from
OrderIntents that passed the signal gate AND pre-trade risk."""
from __future__ import annotations

import logging
from typing import Optional

from core.bus import EventBus
from core.schema import OrderIntent

log = logging.getLogger("exec")


class Executor:
    name = "base"

    def __init__(self, bus: EventBus) -> None:
        self.bus = bus

    def execute(self, intent: OrderIntent) -> Optional[str]:
        raise NotImplementedError

    def flatten(self) -> None:
        raise NotImplementedError
