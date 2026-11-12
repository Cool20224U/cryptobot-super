"""V2 Data desk: canonical entity resolution. Maps mentions to tradable
instruments with confidence; unmatched mentions NEVER become signals.
($PEPE meme stock vs $PEPE the token is a classic silent killer.)"""
from __future__ import annotations

from dataclasses import dataclass

CANONICAL = {
    "BTC": {"pair": "BTC/USDT", "confidence": 1.0},
    "ETH": {"pair": "ETH/USDT", "confidence": 1.0},
    "SOL": {"pair": "SOL/USDT", "confidence": 1.0},
    "PEPE": {"pair": "PEPE/USDT", "confidence": 0.9},
    "DOGE": {"pair": "DOGE/USDT", "confidence": 0.9},
}
ALIASES = {"BITCOIN": "BTC", "ETHEREUM": "ETH", "XBT": "BTC"}


@dataclass(frozen=True)
class Resolved:
    pair: str
    confidence: float


def resolve(mention: str):
    m = mention.upper().strip()
    m = ALIASES.get(m, m)
    hit = CANONICAL.get(m)
    if hit is None:
        return None
    return Resolved(pair=hit["pair"], confidence=hit["confidence"])
