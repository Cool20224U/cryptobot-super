"""Golden-set regression: a frozen labeled tweet set run on every scorer
change. Accuracy below threshold BLOCKS deploy. Guards against model drift."""
from __future__ import annotations

import json
import os
import sys

from core.schema import Direction, RawPost, ScoredPost
from score.lexicon import LexiconScorer

GOLDEN_PATH = os.path.join(os.path.dirname(__file__), "golden_set.json")
ACCURACY_FLOOR = 0.70

GOLDEN = [
    {"text": "bitcoin breaking out, super bullish", "label": "long"},
    {"text": "exchange hacked, funds drained, panic", "label": "short"},
    {"text": "this coin is a rug, total scam", "label": "short"},
    {"text": "ETF approval incoming, accumulate now", "label": "long"},
    {"text": "not bullish at all, careful out there", "label": "short"},
    {"text": "the weather is nice today", "label": "neutral"},
    {"text": "regulator bans crypto trading in country", "label": "short"},
    {"text": "huge partnership announced, moon soon", "label": "long"},
    {"text": "market looks choppy, staying flat", "label": "neutral"},
    {"text": "massive liquidation cascade incoming", "label": "short"},
]


def run_golden_set(scorer=None) -> float:
    scorer = scorer or LexiconScorer(bus=None)
    correct = 0
    for row in GOLDEN:
        post = RawPost(source="golden", external_id=row["text"], text=row["text"], author_id="g")
        scored: ScoredPost = scorer.score(post)
        if scored.direction == Direction.NEUTRAL and row["label"] == "neutral":
            correct += 1
        elif scored.direction.value == row["label"]:
            correct += 1
    acc = correct / len(GOLDEN)
    return round(acc, 3)


def deploy_gate() -> bool:
    acc = run_golden_set()
    print(f"golden set accuracy: {acc:.2f} (floor {ACCURACY_FLOOR})")
    return acc >= ACCURACY_FLOOR


if __name__ == "__main__":
    sys.exit(0 if deploy_gate() else 1)
