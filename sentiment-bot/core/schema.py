"""Typed contracts for every module boundary. Fail-closed: invalid events are dropped."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Direction(str, Enum):
    LONG = "long"
    SHORT = "short"
    NEUTRAL = "neutral"


class Confidence(float, Enum):
    """Clamped confidence values only - LLM free-text never reaches downstream."""
    LOW = 0.3
    MEDIUM = 0.6
    HIGH = 0.9


class Severity(str, Enum):
    INFO = "info"
    WARN = "warn"
    CRITICAL = "critical"


@dataclass(frozen=True)
class RawPost:
    """Untrusted upstream content. Text is DATA, never instructions."""
    source: str
    external_id: str
    text: str
    author_id: str
    author_followers: int = 0
    engagement: int = 0
    ts: datetime = field(default_factory=utcnow)
    mentions: tuple = ()

    def dedupe_key(self) -> str:
        return f"{self.source}:{self.external_id}"


@dataclass(frozen=True)
class ScoredPost:
    post: RawPost
    direction: Direction
    confidence: float
    is_uncertain: bool = False
    scorer: str = "unknown"


@dataclass(frozen=True)
class MarketSnapshot:
    pair: str
    price: float
    ema50: float
    rsi: float
    volume_ratio: float
    ts: datetime = field(default_factory=utcnow)


@dataclass(frozen=True)
class Signal:
    """Output of the signal engine. Requires intent + TA agreement to exist."""
    pair: str
    direction: Direction
    mode: str  # contrarian | momentum | ta_only
    confidence: float
    reason: str
    experiment_id: str = "none"
    ts: datetime = field(default_factory=utcnow)


@dataclass(frozen=True)
class OrderIntent:
    pair: str
    direction: Direction
    size_quote: float
    order_type: str = "limit"
    client_order_id: str = ""
    signal_id: str = ""
    ts: datetime = field(default_factory=utcnow)


@dataclass(frozen=True)
class HealthEvent:
    module: str
    severity: Severity
    message: str
    ts: datetime = field(default_factory=utcnow)


def validate_signal(sig: Signal) -> bool:
    if sig.direction == Direction.NEUTRAL:
        return False
    if not 0.0 <= sig.confidence <= 1.0:
        return False
    return bool(sig.pair and sig.mode)
