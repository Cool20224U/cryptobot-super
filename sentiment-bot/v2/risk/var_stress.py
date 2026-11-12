"""V2 Risk desk: VaR + stress scenarios. Daily suite: exchange outage
mid-position, flash crash, stablecoin depeg, coordinated sentiment poisoning."""
from __future__ import annotations

from dataclasses import dataclass

import math


def parametric_var(exposures: dict, vol: dict, z: float = 2.33, horizon_days: int = 1) -> float:
    """ exposures: {pair: signed_quote_size}, vol: {pair: daily sigma} """
    variance = sum((exposures.get(p, 0.0) * s) ** 2 for p, s in vol.items())
    return z * math.sqrt(variance) * math.sqrt(horizon_days)


STRESS_SCENARIOS = {
    "flash_crash": -0.30,        # 30% adverse move across book
    "exchange_outage_gap": -0.15,
    "stablecoin_depeg": -0.20,
    "sentiment_feed_poisoned": -0.10,
}


def run_stress(exposures: dict) -> dict:
    net = sum(exposures.values())
    return {name: net * shock for name, shock in STRESS_SCENARIOS.items()}


def var_report(exposures: dict, vol: dict) -> dict:
    return {
        "var_99_1d": round(parametric_var(exposures, vol), 2),
        "stress": {k: round(v, 2) for k, v in run_stress(exposures).items()},
    }
