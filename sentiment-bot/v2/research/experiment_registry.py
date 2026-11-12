"""V2 Quant Research: hypothesis registry. No signal goes live without a
documented experiment id; live signals carry their experiment id for attribution."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field, asdict

REGISTRY_PATH = os.environ.get("EXPERIMENT_REGISTRY", "data/experiments.json")


@dataclass
class Experiment:
    id: str
    hypothesis: str
    created_at: float = field(default_factory=time.time)
    status: str = "proposed"  # proposed | backtested | oos_validated | live | retired
    backtest_sharpe: float = 0.0
    oos_sharpe: float = 0.0
    notes: str = ""


class ExperimentRegistry:
    def __init__(self, path: str = REGISTRY_PATH) -> None:
        self.path = path
        self._experiments: dict = {}
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                self._experiments = {e["id"]: Experiment(**e) for e in json.load(f)}

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump([asdict(e) for e in self._experiments.values()], f, indent=2)

    def register(self, exp: Experiment) -> None:
        self._experiments[exp.id] = exp
        self.save()

    def sign_off(self, exp_id: str) -> bool:
        """Live promotion gate: backtest + OOS Sharpe >= 1.5 after costs."""
        exp = self._experiments.get(exp_id)
        if exp is None:
            return False
        if exp.backtest_sharpe >= 1.5 and exp.oos_sharpe >= 1.5:
            exp.status = "live"
            self.save()
            return True
        return False

    def get(self, exp_id: str):
        return self._experiments.get(exp_id)
