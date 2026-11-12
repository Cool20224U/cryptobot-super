# sentiment-bot — X/Twitter sentiment crypto day-trading bot (V1 + V2)

Self-contained, modular, security-audited design as discussed. **Logger-first:
the default runner uses a paper executor and touches no money.**

## Pipeline

```
Ingest (x_stream > aggregator > coarse)      primary + 2 fallbacks per stage
  -> BotFilter (spam/pump-flood/injection)   security control, non-bypassable
  -> Scorer (llm > lexicon > velocity)       strict-JSON LLM, quota-capped
  -> ModeStack (contrarian > momentum > ta_only)
  -> SignalGate                              two-key: sentiment AND TA must agree
  -> RiskManager                             hard limits: 2%/trade, -3% daily, 5 trades/day
  -> Executor (paper > ccxt venue > flat)
```

Everything flows through a typed event bus (`core/bus.py`); malformed events are
dropped, never propagated toward an order. All events land in an append-only
store (`ops/store.py`) = audit trail + backtest dataset.

## Security posture

- Prompt-injection rejected at ingest; tweet text is data, never instructions.
- LLM output is strict JSON; parse failure -> uncertain -> veto (fail-closed).
- Bot-farm filter: near-dup + author-flood caps (pump groups can't trigger it).
- Two-key trade authorization: no single stage can move money alone.
- Trade-only exchange keys (withdrawals disabled, IP-locked), idempotent client
  order IDs, independent watchdog with cancel/close-only credentials.
- Secrets via env only; `config/` holds wiring, never credentials.

## Quick start

```bash
cd sentiment-bot
pip install -r requirements.txt pytest
python -m pytest tests -q          # 17 tests: gate, risk, filters, V2 modules
python main.py                     # logger-only run (paper executor)
python -m risk.golden_set          # scorer regression gate (blocks deploy)
python -m risk.watchdog data/heartbeat 120   # independent watchdog
```

## V1 vs V2

V1 (`core/ ingest/ score/ signals/ exec/ risk/ ops/`): full pipeline with the
primary + 2-fallback degradation ladder, gate, hard risk limits, watchdog.

V2 (fund-grade, `v2/`):
- `research/` — experiment registry (no signal live without a signed-off
  experiment; Sharpe >= 1.5 after costs), edge-decay monitor (auto-demote when
  live Sharpe exits the backtest band).
- `data/` — entity resolution (unmatched mentions never signal), data-quality
  SLA (stale/insane quotes rejected).
- `risk/` — pre-trade risk service (three-key authorization, correlation
  cluster caps), VaR + stress suite (flash crash, depeg, feed poisoning).
- `ops/` — trade blotter with full decision attribution for auditors.

## Deployment rules

1. Logger-only for 2+ weeks: build your own sentiment/price dataset.
2. Backtest with fees/slippage; walk-forward; Sharpe < 1.5 after costs -> stop.
3. Dry-run (paper signals vs live prices) 4–6 weeks.
4. Live at 10% intended size; weekly fallback drill (kill a source on purpose).
5. Not financial advice. No configuration guarantees daily profits — the
   design goal is surviving the days the edge doesn't show up.
