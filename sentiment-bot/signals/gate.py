"""Two-key trade authorization: sentiment intent AND independent TA check must
agree. Structurally immune to a compromised upstream stage: no single module
can produce a Signal on its own."""
from __future__ import annotations

import logging

from core.schema import Direction, MarketSnapshot, Signal, validate_signal

log = logging.getLogger("gate")


class SignalGate:
    def __init__(self, ta_check) -> None:
        self._ta_check = ta_check  # independent TA/risk callable: (signal, snapshot) -> bool

    def authorize(self, signal: Signal, snap: MarketSnapshot | None) -> Signal | None:
        if not validate_signal(signal):
            log.info("gate: invalid signal dropped %s", signal)
            return None
        if snap is None:
            return None
        if not self._ta_check(signal, snap):
            log.info("gate: TA veto for %s %s", signal.pair, signal.mode)
            return None
        if signal.mode == "contrarian":
            ok = (signal.direction == Direction.SHORT and snap.volume_ratio > 1.2) or (
                signal.direction == Direction.LONG and snap.volume_ratio > 0.8
            )
            if not ok:
                return None
        return signal
