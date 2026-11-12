"""Scorer protocol + bot-farm filtering (a security control, not just hygiene)."""
from __future__ import annotations

import hashlib
import re
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Deque, Dict, Iterable

from core.bus import EventBus
from core.schema import Direction, RawPost, ScoredPost

URL_RE = re.compile(r"https?://\S+|@\w+|#\w+")
TOKEN_RE = re.compile(r"[^a-z0-9$ ]+")


def clean_text(text: str) -> str:
    return TOKEN_RE.sub(" ", URL_RE.sub(" ", text.lower())).strip()


def simhash16(text: str) -> int:
    h = hashlib.sha1(text.encode()).digest()
    return int.from_bytes(h[:2], "big")


@dataclass
class BotFilter:
    """Near-duplicate + author-flood detection. Single-author floods (pump
    groups) and template spam are dropped before any scorer sees them."""
    window: int = 120
    max_per_author: int = 5
    max_dup_hash: int = 3

    def __init__(self) -> None:
        self._seen: Deque = deque(maxlen=self.window)
        self._hashes: Dict[int, int] = defaultdict(int)
        self._authors: Dict[str, int] = defaultdict(int)

    def allow(self, post: RawPost) -> bool:
        key = post.dedupe_key()
        if key in self._seen:
            return False
        self._seen.append(key)
        h = simhash16(clean_text(post.text))
        self._hashes[h] += 1
        self._authors[post.author_id] += 1
        if self._hashes[h] > self.max_dup_hash:
            return False
        if self._authors[post.author_id] > self.max_per_author:
            return False
        return True


class Scorer:
    name = "base"

    def __init__(self, bus: EventBus) -> None:
        self.bus = bus

    def score(self, post: RawPost) -> ScoredPost:
        raise NotImplementedError

    def score_batch(self, posts: Iterable[RawPost]) -> list:
        return [self.score(p) for p in posts]
