"""V2 Compliance desk: trade blotter with decision attribution. Every order
reconstructable for auditors: which signal, which experiment, which data."""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass

BLOTTER_PATH = os.environ.get("BLOTTER_PATH", "data/blotter.jsonl")


@dataclass
class BlotterEntry:
    ts: float
    client_order_id: str
    pair: str
    direction: str
    size_quote: float
    signal_mode: str
    experiment_id: str
    scorer: str = ""
    ingest_source: str = ""


class Blotter:
    def __init__(self, path: str = BLOTTER_PATH) -> None:
        self.path = path

    def record(self, entry: BlotterEntry) -> None:
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(entry)) + "\n")

    def load(self) -> list:
        if not os.path.exists(self.path):
            return []
        with open(self.path, encoding="utf-8") as f:
            return [json.loads(line) for line in f]
