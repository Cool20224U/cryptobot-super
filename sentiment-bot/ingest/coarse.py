"""FALLBACK B: free coarse mood floor - Alternative.me Fear & Greed + Reddit RSS.

No auth required. Degrades the whole system to 'no directional sentiment,
TA-only' if both primary and fallback A are down.
"""
from __future__ import annotations

from typing import Iterable

import requests

from ingest.base import IngestSource
from core.schema import RawPost

FNG_URL = "https://api.alternative.me/fng/?limit=1"


class CoarseSource(IngestSource):
    name = "coarse"

    def poll(self) -> Iterable[RawPost]:
        try:
            resp = requests.get(FNG_URL, timeout=10)
            data = resp.json()["data"][0]
        except Exception:
            self.bus.publish_health("ingest.coarse", "critical", "fng fetch failed")
            return
        yield RawPost(
            source="fng",
            external_id=f"fng:{data['timestamp']}",
            text=f"market fear and greed index {data['value']} {data['value_classification']}",
            author_id="alternative.me",
            engagement=0,
            mentions=("BTC",),
        )
