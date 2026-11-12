"""In-process risk manager: sizing, daily loss limit, cooldowns, trade caps.
Limits are HARD: enforced in code, the bot cannot override them."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from core.schema import Direction, OrderIntent, Signal

log = logging.getLogger("risk")


@dataclass
class RiskLimits:
    max_risk_per_trade: float = 0.02      # 2% of equity
    daily_loss_limit: float = 0.03        # -3% -> flat + cooldown
    max_trades_per_day: int = 5
    cooldown_after_loss_streak: int = 3
    equity_quote: float = 10_000.0
    stop_loss_pct: float = 0.02


@dataclass
class RiskState:
    day_pnl: float = 0.0
    trades_today: int = 0
    loss_streak: int = 0
    in_cooldown: bool = False


class RiskManager:
    def __init__(self, limits: RiskLimits | None = None) -> None:
        self.limits = limits or RiskLimits()
        self.state = RiskState()

    def size_order(self, signal: Signal) -> OrderIntent:
        size = self.limits.equity_quote * self.limits.max_risk_per_trade / self.limits.stop_loss_pct
        return OrderIntent(
            pair=signal.pair,
            direction=signal.direction,
            size_quote=round(size, 4),
            signal_id=f"{signal.pair}:{signal.ts.isoformat()}",
        )

    def approve(self, intent: OrderIntent) -> bool:
        s = self.state
        if s.in_cooldown:
            return False
        if s.trades_today >= self.limits.max_trades_per_day:
            log.info("risk: daily trade cap hit")
            return False
        if s.day_pnl <= -self.limits.equity_quote * self.limits.daily_loss_limit:
            log.warning("risk: DAILY LOSS LIMIT - going flat + cooldown")
            s.in_cooldown = True
            return False
        if intent.size_quote > self.limits.equity_quote:
            return False
        s.trades_today += 1
        return True

    def record_fill(self, pnl: float) -> None:
        self.state.day_pnl += pnl
        if pnl < 0:
            self.state.loss_streak += 1
            if self.state.loss_streak >= self.limits.cooldown_after_loss_streak:
                self.state.in_cooldown = True
        else:
            self.state.loss_streak = 0

    def new_day(self) -> None:
        self.state = RiskState()
