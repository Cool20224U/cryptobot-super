"""FALLBACK B: engagement-velocity heuristic - no text semantics at all.

Usable when the NLP layer is down or budget is exhausted. Signal strength is
mention velocity vs baseline, bot-diversity ratio; direction must come from the
tiny lexicon or is marked uncertain.
"""
from __future__ import annotations

from collections import defaultdict, deque
from typing import Deque

from core.schema import Direction, RawPost, ScoredPost
from score.base import Scorer
from score.lexicon import lexicon_score


class VelocityScorer(Scorer):
    name = "velocity"

    def __init__(self, bus) -> None:
        super().__init__(bus)
        self._mentions: Deque = deque(maxlen=500)
        self._per_asset: dict = defaultdict(int)

    def score(self, post: RawPost) -> ScoredPost:
        self._mentions.append(post)
        for m in post.mentions:
            self._per_asset[m] += 1
        recent = sum(1 for p in self._mentions if p.mentions == post.mentions)
        authors = {p.author_id for p in self._mentions if p.mentions == post.mentions}
        diversity = len(authors) / max(1, recent)
        if recent < 5 or diversity < 0.3:
            return ScoredPost(post=post, direction=Direction.NEUTRAL, confidence=0.0, is_uncertain=True, scorer=self.name)
        s = lexicon_score(post.text)
        direction = Direction.LONG if s > 0 else Direction.SHORT
        return ScoredPost(post=post, direction=direction, confidence=min(1.0, recent / 50) * diversity, is_uncertain=False, scorer=self.name)
