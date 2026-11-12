from v2.data.entity_resolution import resolve
from v2.data.quality import DataQualitySLA, MarketDataValidator
from v2.risk.pretrade import PreTradeRisk, PortfolioLimits
from v2.risk.var_stress import var_report
from v2.research.edge_decay import DecayMonitor
from v2.research.experiment_registry import Experiment, ExperimentRegistry
from v2.ops.blotter import Blotter, BlotterEntry
from core.schema import Direction, MarketSnapshot, OrderIntent


def test_entity_resolution_unmatched_never_signals():
    assert resolve("PEPE") is not None
    assert resolve("BITCOIN").pair == "BTC/USDT"
    assert resolve("TOTALLYUNKNOWN") is None


def test_data_quality_rejects_stale():
    v = MarketDataValidator(DataQualitySLA(max_quote_age_s=30))
    import time
    from datetime import datetime, timezone
    old = MarketSnapshot(pair="BTC/USDT", price=100, ema50=100, rsi=50, volume_ratio=1,
                         ts=datetime(2020, 1, 1, tzinfo=timezone.utc))
    assert not v.validate(old)


def test_pretrade_cluster_limit():
    ptr = PreTradeRisk(equity=1000, limits=PortfolioLimits(per_asset_pct=0.30, correlated_cluster_pct=0.20))
    i = OrderIntent(pair="SOL/USDT", direction=Direction.LONG, size_quote=150, signal_id="s")
    assert ptr.check(i)
    ptr.on_fill(i)
    j = OrderIntent(pair="DOGE/USDT", direction=Direction.LONG, size_quote=100, signal_id="s")
    assert not ptr.check(j)  # correlated cluster cap


def test_var_and_stress():
    rep = var_report({"BTC/USDT": 500}, {"BTC/USDT": 0.04})
    assert rep["var_99_1d"] > 0
    assert rep["stress"]["flash_crash"] < 0


def test_edge_decay_demotes():
    dm = DecayMonitor(backtest_sharpe=2.0, band=0.5, window=50)
    for _ in range(50):
        dm.record(-0.01)
    assert dm.should_demote()


def test_experiment_signoff_gate(tmp_path):
    reg = ExperimentRegistry(path=str(tmp_path / "exp.json"))
    reg.register(Experiment(id="exp-001", hypothesis="sentiment contrarian"))
    assert not reg.sign_off("exp-001")
    reg.get("exp-001").backtest_sharpe = 1.6
    reg.get("exp-001").oos_sharpe = 1.7
    assert reg.sign_off("exp-001")


def test_blotter_attribution(tmp_path):
    b = Blotter(path=str(tmp_path / "blotter.jsonl"))
    b.record(BlotterEntry(ts=1, client_order_id="c1", pair="BTC/USDT", direction="long",
                          size_quote=100, signal_mode="contrarian", experiment_id="exp-001",
                          scorer="llm", ingest_source="x_stream"))
    rows = b.load()
    assert rows[0]["experiment_id"] == "exp-001"
