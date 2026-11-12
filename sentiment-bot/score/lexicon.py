"""FALLBACK A (and always-on cross-check): crypto-tuned lexicon scorer.

Instant, free, deterministic. Runs on every post even when the LLM is primary,
so disagreement between the two can be detected upstream.
"""
from __future__ import annotations

from core.schema import Direction, RawPost, ScoredPost
from score.base import Scorer, clean_text

BULL = {
    "bullish": 2, "moon": 2, "buy": 1, "long": 2, "gem": 1, "pump": 1,
    "breakout": 2, "accumulate": 2, "ath": 1, "surge": 1, "rally": 2,
    "adoption": 1, "approval": 2, "upgrade": 1, "partnership": 1,
}
BEAR = {
    "bearish": -2, "sell": -1, "dump": -2, "scam": -3, "rug": -3, "hack": -3,
    "exploit": -3, "ban": -2, "crash": -2, "liquidation": -2, "fud": -1,
    "outflow": -1, "delay": -1, "lawsuit": -2, "halt": -2,
}
NEGATE = {"not", "no", "never", "isnt", "wont", "cant"}


def lexicon_score(text: str) -> float:
    words = clean_text(text).split()
    score = 0
    for i, w in enumerate(words):
        negated = i > 0 and words[i - 1] in NEGATE
        s = BULL.get(w, 0) + BEAR.get(w, 0)
        score += -s if negated else s
    return max(-1.0, min(1.0, score / 6.0))


class LexiconScorer(Scorer):
    name = "lexicon"

    def score(self, post: RawPost) -> ScoredPost:
        s = lexicon_score(post.text)
        if abs(s) < 0.15:
            direction, uncertain = Direction.NEUTRAL, True
        else:
            direction, uncertain = (Direction.LONG, False) if s > 0 else (Direction.SHORT, False)
        return ScoredPost(post=post, direction=direction, confidence=abs(s), is_uncertain=uncertain, scorer=self.name)
