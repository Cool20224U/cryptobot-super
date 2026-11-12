"""IngestSource protocol. Every adapter (primary + fallbacks) implements this."""
from __future__ import annotations

import logging
import re
from typing import Iterable, Optional

from core.bus import EventBus
from core.schema import Direction, HealthEvent, RawPost, Severity

log = logging.getLogger("ingest")

INSTRUCTION_PATTERNS = re.compile(
    r"ignore (all |previous )?instructions|system prompt|you are now|disregard .{0,30}above",
    re.IGNORECASE,
)

TICKER_RE = re.compile(r"\$([A-Za-z0-9]{2,10})")


def extract_tickers(text: str) -> tuple:
    return tuple(m.upper() for m in TICKER_RE.findall(text))


def sanitize(text: str) -> Optional[str]:
    """Reject prompt-injection payloads: tweet text is data, never instructions."""
    if INSTRUCTION_PATTERNS.search(text):
        return None
    return text


class IngestSource:
    name = "base"

    def __init__(self, bus: EventBus) -> None:
        self.bus = bus

    def poll(self) -> Iterable[RawPost]:
        raise NotImplementedError

    def emit(self, post: RawPost) -> None:
        text = sanitize(post.text)
        if text is None:
            log.warning("dropped injection-like post from %s", post.source)
            return
        mentions = extract_tickers(text)
        post = RawPost(
            source=post.source,
            external_id=post.external_id,
            text=text,
            author_id=post.author_id,
            author_followers=post.author_followers,
            engagement=post.engagement,
            ts=post.ts,
            mentions=mentions or post.mentions,
        )
        self.bus.publish("posts.raw", post)
        self.bus.publish(
            "heartbeat", HealthEvent(module=f"ingest.{self.name}", severity=Severity.INFO, message="ok")
        )
