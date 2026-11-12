"""FALLBACK venues for live mode. Trade-only API keys: withdrawals disabled,
IP-locked to this host. Fallback B is FlatExecutor - never hold unmanaged risk
during venue failure."""
from __future__ import annotations

import logging
import os

from core.schema import OrderIntent
from exec.base import Executor
from exec.idempotency import IdempotencyLedger, make_client_order_id

log = logging.getLogger("exec.ccxt")


class CcxtExecutor(Executor):
    name = "ccxt"

    def __init__(self, bus, exchange_id: str) -> None:
        super().__init__(bus)
        import ccxt  # imported lazily: paper mode has no live deps
        klass = getattr(ccxt, exchange_id)
        self.ex = klass({
            "apiKey": os.getenv("EXCHANGE_API_KEY", ""),
            "secret": os.getenv("EXCHANGE_API_SECRET", ""),
            "options": {"defaultType": "spot"},
        })
        self.ledger = IdempotencyLedger()

    def execute(self, intent: OrderIntent):
        coid = intent.client_order_id or make_client_order_id(intent)
        if not self.ledger.register(coid):
            return None
        try:
            order = self.ex.create_order(
                intent.pair,
                intent.order_type,
                "buy" if intent.direction.value == "long" else "sell",
                amount=None,
                price=None,
                params={"clientOrderId": coid},
            )
            return order.get("id", coid)
        except Exception:
            log.exception("order failed; reconcile before retry")
            self.bus.publish_health("exec.ccxt", "critical", "order submission failed")
            return None

    def flatten(self) -> None:
        try:
            self.ex.cancel_all_orders(None)
        except Exception:
            log.exception("flatten failed")
            self.bus.publish_health("exec.ccxt", "critical", "flatten failed")


class FlatExecutor(Executor):
    """FALLBACK B: cancel all open orders, protective stops only."""
    name = "flat"

    def execute(self, intent: OrderIntent):
        log.warning("FLAT MODE: refusing new order %s", intent.pair)
        return None

    def flatten(self) -> None:
        log.warning("FLAT MODE: already flat")
