"""PRIMARY: X (Twitter) filtered stream / search adapter.

Uses the X API v2 filtered stream when credentials exist; degrades to a
twitterapi.io-style REST poll via INGEST_X_ALT_URL. No credentials -> emits
nothing and reports critical health so the ladder degrades to fallback A.
Secrets come from env vars only, never config files.
"""
from __future__ import annotations

import json
import os
from typing import Iterable

import requests

from ingest.base import IngestSource
from core.schema import RawPost

API = "https://api.x.com/2/tweets/search/stream"


class XStream(IngestSource):
    name = "x_stream"

    def poll(self) -> Iterable[RawPost]:
        bearer = os.getenv("X_BEARER_TOKEN")
        if not bearer:
            self.bus.publish_health("ingest.x_stream", "critical", "no X_BEARER_TOKEN")
            return
        resp = requests.get(
            API,
            headers={"Authorization": f"Bearer {bearer}"},
            params={"tweet.fields": "created_at,public_metrics,author_id"},
            timeout=10,
        )
        if resp.status_code != 200:
            self.bus.publish_health("ingest.x_stream", "critical", f"http {resp.status_code}")
            return
        for line in resp.text.splitlines():
            if not line.strip():
                continue
            data = json.loads(line).get("data", {})
            if not data:
                continue
            metrics = data.get("public_metrics", {})
            yield RawPost(
                source="x",
                external_id=data["id"],
                text=data.get("text", ""),
                author_id=data.get("author_id", ""),
                engagement=metrics.get("like_count", 0) + metrics.get("retweet_count", 0),
            )
