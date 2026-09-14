"""
Backtest harness: trains the model on historical data, then simulates the
full strategy + risk pipeline candle-by-candle on held-out data to see
whether the signal actually translates into a sane equity curve --
not just a good classification accuracy score.
"""
import pandas as pd
import data_fetcher
import feature_engineering as fe
import ml_model
from risk_manager import RiskManager
import config


def run_backtest(days_back=365):
    print("Fetching historical data...")
    raw_df = data_fetcher.fetch_historical(days_back=days_back)
    print(f"Fetched {len(raw_df)} candles.")

    featured_df = fe.add_features(raw_df)
    labeled_df = fe.make_labels(featured_df)

    print("Training model...")
    model = ml_model.train(labeled_df)

    # Simulate the strategy candle-by-candle on the last 20% (out-of-sample)
    sim_start = int(len(labeled_df) * 0.8)
    sim_df = labeled_df.iloc[sim_start:].reset_index(drop=True)

    risk_mgr = RiskManager(equity=config.PAPER_STARTING_EQUITY)
    cash = config.PAPER_STARTING_EQUITY
    position = None
    equity_curve = []
    trades = []

    for i in range(len(sim_df)):
        row = sim_df.iloc[i]
        price = row["close"]

        # Check exits first
        if position is not None:
            if price <= position["stop_loss"] or price >= position["take_profit"]:
                proceeds = position["quantity"] * price
                pnl = proceeds - position["quantity"] * position["entry_price"]
                cash += proceeds
                trades.append(pnl)
                position = None
                risk_mgr.update_equity(cash)

        # Consider new entry
        if position is None and not risk_mgr.halted:
            direction, confidence = ml_model.predict_signal(model, row)
            order = risk_mgr.evaluate(direction, confidence, price)
            if order:
                cost = order["quantity"] * price
                if cost <= cash:
                    cash -= cost
                    position = order

        mark_to_market = cash + (position["quantity"] * price if position else 0)
        equity_curve.append(mark_to_market)

    final_equity = equity_curve[-1] if equity_curve else config.PAPER_STARTING_EQUITY
    total_return = (final_equity - config.PAPER_STARTING_EQUITY) / config.PAPER_STARTING_EQUITY
    wins = [t for t in trades if t > 0]
    losses = [t for t in trades if t <= 0]
    max_dd = _max_drawdown(equity_curve)

    print("\n--- Backtest Results (out-of-sample) ---")
    print(f"Trades taken:      {len(trades)}")
    print(f"Win rate:          {len(wins)/len(trades):.1%}" if trades else "Win rate: N/A (no trades)")
    print(f"Total return:      {total_return:+.2%}")
    print(f"Max drawdown:      {max_dd:.2%}")
    print(
        "\nReminder: this is one historical window on one symbol. A good "
        "result here is a reason to paper-trade next, not a reason to go live."
    )
    return equity_curve, trades


def _max_drawdown(equity_curve):
    peak = equity_curve[0]
    max_dd = 0.0
    for value in equity_curve:
        peak = max(peak, value)
        dd = (peak - value) / peak
        max_dd = max(max_dd, dd)
    return max_dd


if __name__ == "__main__":
    run_backtest()
