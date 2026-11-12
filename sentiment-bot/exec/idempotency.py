"""Client order IDs + state reconciliation. Prevents duplicate-order blowups:
on partial fill or timeout, reconcile from exchange state before any retry."""
from __future__ import annotations

import hashlib
from collections import deque
from typing import Deque, Set


def make_client_order_id(intent) -> str:
    seed = f"{intent.pair}:{intent.direction}:{intent.signal_id}"
    return "sb-" + hashlib.sha1(seed.encode()).hexdigest()[:16]


class IdempotencyLedger:
    def __init__(self, memory: int = 1000) -> None:
        self._seen: Set[str] = set()
        self._order: Deque[str] = deque(maxlen=memory)

    def register(self, coid: str) -> bool:
        """Returns False if this client order id was already submitted."""
        if coid in self._seen:
            return False
        self._seen.add(coid)
        self._order.append(coid)
        return True
