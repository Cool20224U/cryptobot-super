"""Append-only event store: audit trail + backtest dataset in one. Point-in-time
timestamped at receipt; every stage is replayable offline."""
from __future__ import annotations

import json
import os
from dataclasses import asdict

ENCODERS = set()


def _default(o):
    try:
        return asdict(o)
    except TypeError:
        return str(o)


class EventStore:
    def __init__(self, path: str = "data/events.jsonl") -> None:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self.path = path

    def append(self, topic: str, event) -> None:
        rec = {"topic": topic, "received_at": __import__("time").time(), "event": _default(event)}
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, default=str) + "\n")

    def replay(self, topic: str):
        if not os.path.exists(self.path):
            return
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                if rec["topic"] == topic:
                    yield rec["event"]
