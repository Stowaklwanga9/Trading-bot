# Trading Bot Skeleton (Paper-Trading by Default)

This is a **learning framework**, not a profit machine. It fetches historical
and live market data, engineers features, trains an ML model to produce a
directional signal, gates every signal through a hard risk-management layer,
and executes trades — in **paper mode by default**.

## What this is / isn't

- ✅ A realistic architecture: data → features → model → risk gate → execution
- ✅ Backtestable, loggable, and safe to run against Binance/Coinbase test data
- ❌ Not a "highly accurate" predictor — no such thing exists reliably in markets
- ❌ Not financial advice, and not guaranteed to be profitable
- ❌ Not safe to point at real funds until YOU read `execution.py` and
  understand exactly what it does

## Setup

```bash
pip install ccxt pandas numpy scikit-learn ta python-dotenv
```

Create a `.env` file (never commit this):

```
EXCHANGE=binance
API_KEY=your_key_here
API_SECRET=your_secret_here
TRADING_MODE=paper   # paper | live  -- DO NOT set to "live" until you've read execution.py
```

**API key permissions:** when you create the key on Binance/Coinbase, enable
**trading only**. Disable withdrawal permissions. If the key ever leaks, the
attacker still can't move your funds out.

## Run order

1. `python backtest.py` — trains the model on historical data and reports
   performance metrics (win rate, max drawdown, Sharpe-ish ratio) on data the
   model did NOT train on (out-of-sample). If this looks too good (>65-70%
   win rate), be suspicious of overfitting before trusting it.
2. `python main.py` — runs the live loop in **paper mode**: real market data,
   simulated fills, real logs. Watch this for days/weeks before considering
   live mode.
3. Only after (1) and (2) look sane for an extended period, and only with
   money you can fully afford to lose, consider flipping `TRADING_MODE=live`.

## File map

- `config.py` — central settings, risk limits, reads `.env`
- `data_fetcher.py` — historical OHLCV + live data via ccxt
- `feature_engineering.py` — technical indicators used as model inputs
- `ml_model.py` — trains/loads a classifier predicting next-period direction
- `risk_manager.py` — position sizing, stop-loss, daily loss limit, veto power
- `strategy.py` — combines model output + risk manager into a final order (or none)
- `execution.py` — paper executor (simulated) and live executor (ccxt orders)
- `backtest.py` — historical evaluation harness with out-of-sample split
- `main.py` — orchestrates the live loop, logging, and kill-switch

## The kill switch

`risk_manager.py` tracks daily P&L. If losses exceed `MAX_DAILY_LOSS_PCT`,
`RiskManager.halted` becomes `True` and `strategy.py` will refuse to emit any
new orders for the rest of that day, regardless of what the model says. This
check cannot be bypassed by the strategy layer — that's intentional.
