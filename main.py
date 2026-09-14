"""
Live loop orchestrator. Defaults to paper mode via config.TRADING_MODE.
Run backtest.py first to produce model.joblib before running this.
"""
import time
import datetime
import data_fetcher
import ml_model
from strategy import Strategy
from risk_manager import RiskManager
from execution import get_executor
import config


def main():
    print(f"Starting bot in {config.TRADING_MODE.upper()} mode on {config.SYMBOL} ({config.TIMEFRAME})")

    model = ml_model.load()
    risk_mgr = RiskManager(equity=config.PAPER_STARTING_EQUITY)
    strategy = Strategy(model, risk_mgr)
    executor = get_executor()

    current_day = datetime.date.today()

    while True:
        try:
            # Daily reset of the loss-limit tracker
            if datetime.date.today() != current_day:
                current_day = datetime.date.today()
                risk_mgr.reset_daily(equity=getattr(executor, "cash", risk_mgr.equity))

            df = data_fetcher.fetch_ohlcv(limit=200)  # enough history for indicators
            current_price = df.iloc[-1]["close"]

            # Manage any open position first
            executor.check_exit(current_price)

            # Look for a new entry only if flat
            if getattr(executor, "position", None) is None:
                order = strategy.decide(df)
                if order:
                    executor.place_order(order)

            risk_mgr.update_equity(getattr(executor, "cash", risk_mgr.equity))

        except Exception as e:
            # Fail safe, not silent: log and back off, never crash-loop
            # straight back into placing orders on bad state.
            print(f"[ERROR] {e}")
            time.sleep(30)
            continue

        time.sleep(60)  # poll interval -- tune to your timeframe


if __name__ == "__main__":
    main()
