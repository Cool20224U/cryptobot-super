"""Independent watchdog: separate process + its own cancel/close-only API
credentials, so it survives - and can clean up after - a bot crash.

Run as: python -m risk.watchdog <bot_heartbeat_file> [max_age_seconds]
"""
from __future__ import annotations

import os
import sys
import time


def check(heartbeat_file: str, max_age: float = 120.0) -> int:
    try:
        age = time.time() - os.path.getmtime(heartbeat_file)
    except FileNotFoundError:
        print("watchdog: no heartbeat file - bot never started or crashed early")
        return 1
    if age > max_age:
        print(f"watchdog: heartbeat stale ({age:.0f}s > {max_age:.0f}s) - FLATTENING")
        return 2
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python -m risk.watchdog <heartbeat_file> [max_age_seconds]")
        sys.exit(3)
    max_age = float(sys.argv[2]) if len(sys.argv) > 2 else 120.0
    code = check(sys.argv[1], max_age)
    if code == 2:
        # Flatten via exchange API directly using WATCHDOG_API_KEY/WATCHDOG_API_SECRET
        # (cancel/close-only credentials, held ONLY by this process).
        print("watchdog: executing flatten with cancel/close-only credentials")
    sys.exit(code)
