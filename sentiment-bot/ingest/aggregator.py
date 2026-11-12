"""FALLBACK A: paid sentiment aggregator (LunarCrush / Santiment style).

Consumes a bot-filtered per-coin sentiment time-series so if the raw X feed
dies, scoring quality degrades gracefully instead of collapsing.
"""
from __future__ import annotations

import os
from typing import Iterable

import requests

from ingest.base import IngestSource
from core.schema import Direction, RawPost


class AggregatorSource(IngestSource):
    name = "aggregator"

    def poll(self) -> Iterable[RawPost]:
        url = os.getenv("SENTIMENT_AGGREGATOR_URL")
        key = os.getenv("SENTIMENT_AGGREGATOR_KEY")
        if not url or not key:
            self.bus.publish_health("ingest.aggregator", "critical", "aggregator not configured")
            return
        resp = requests.get(url, headers={"Authorization": f"Bearer {key}"}, timeout=10)
        if resp.status_code != 200:
            self.bus.publish_health("ingest.aggregator", "critical", f"http {resp.status_code}")
            return
        for row in resp.json().get("data", []):
            yield RawPost(
                source="aggregator",
                external_id=f"{row.get('coin')}:{row.get('ts')}",
                text=row.get("summary", row.get("coin", "")),
                author_id="aggregator",
                author_followers=1_000_000,
                engagement=int(row.get("social_volume", 0)),
                mentions=(row.get("coin", "").upper(),),
            )
