"""PRIMARY for development: paper executor - logs orders, touches no money.
Promote a ccxt-backed executor only after backtest + dry-run pass."""
from __future__ import annotations

import logging

from core.schema import OrderIntent
from exec.base import Executor
from exec.idempotency import IdempotencyLedger, make_client_order_id

log = logging.getLogger("exec.paper")


class PaperExecutor(Executor):
    name = "paper"

    def __init__(self, bus) -> None:
        super().__init__(bus)
        self.ledger = IdempotencyLedger()

    def execute(self, intent: OrderIntent):
        coid = intent.client_order_id or make_client_order_id(intent)
        if not self.ledger.register(coid):
            log.warning("duplicate order blocked %s", coid)
            return None
        log.info("PAPER FILL %s %s %s %.4f (%s)", coid, intent.pair, intent.direction.value, intent.size_quote, intent.order_type)
        self.bus.publish("orders.filled", {"client_order_id": coid, "pair": intent.pair, "size_quote": intent.size_quote})
        return coid

    def flatten(self) -> None:
        log.info("PAPER FLAT: cancel all, protective stops only")
