"""
Execution layer. PaperExecutor simulates fills using real prices so you can
run the whole system safely. LiveExecutor sends real orders via ccxt --
read every line of this class before ever instantiating it.
"""
import time
import config
from data_fetcher import get_exchange


class PaperExecutor:
    def __init__(self, starting_equity=config.PAPER_STARTING_EQUITY):
        self.cash = starting_equity
        self.position = None  # dict: {quantity, entry_price, stop_loss, take_profit}
        self.trade_log = []

    @property
    def equity(self):
        if self.position is None:
            return self.cash
        # mark-to-market not tracked live here; realized on close for simplicity
        return self.cash

    def place_order(self, order: dict):
        cost = order["quantity"] * order["entry_price"]
        if cost > self.cash:
            print("[PAPER] Insufficient simulated cash, skipping order.")
            return
        self.cash -= cost
        self.position = order
        self.trade_log.append({"action": "open", **order, "time": time.time()})
        print(f"[PAPER] Opened long {order['quantity']:.6f} @ {order['entry_price']:.2f} "
              f"(SL {order['stop_loss']:.2f} / TP {order['take_profit']:.2f})")

    def check_exit(self, current_price: float):
        if self.position is None:
            return
        pos = self.position
        hit_sl = current_price <= pos["stop_loss"]
        hit_tp = current_price >= pos["take_profit"]
        if hit_sl or hit_tp:
            proceeds = pos["quantity"] * current_price
            self.cash += proceeds
            pnl = proceeds - (pos["quantity"] * pos["entry_price"])
            reason = "stop_loss" if hit_sl else "take_profit"
            self.trade_log.append({"action": "close", "reason": reason, "pnl": pnl, "time": time.time()})
            print(f"[PAPER] Closed via {reason} @ {current_price:.2f}, PnL: {pnl:+.2f}")
            self.position = None


class LiveExecutor:
    """
    Sends real orders to the exchange. Requires API_KEY/API_SECRET with
    TRADING permission only (no withdrawal). Test on the exchange's testnet
    first if available.
    """
    def __init__(self):
        self.exchange = get_exchange()
        self.position = None

    def place_order(self, order: dict, symbol=config.SYMBOL):
        print(f"[LIVE] Placing REAL market buy: {order['quantity']} {symbol}")
        result = self.exchange.create_market_buy_order(symbol, order["quantity"])
        self.position = order
        # In production: also place actual stop-loss/take-profit orders on
        # the exchange (e.g. OCO orders) rather than relying on a local
        # loop to detect and act on price -- a dropped connection would
        # otherwise leave you unprotected.
        return result

    def check_exit(self, current_price: float, symbol=config.SYMBOL):
        if self.position is None:
            return
        pos = self.position
        if current_price <= pos["stop_loss"] or current_price >= pos["take_profit"]:
            print(f"[LIVE] Exit condition met, placing REAL market sell.")
            self.exchange.create_market_sell_order(symbol, pos["quantity"])
            self.position = None


def get_executor():
    if config.TRADING_MODE == "live":
        print(
            "\n*** TRADING_MODE=live: this will place REAL orders with REAL "
            "money. Ctrl+C now if that's not intended. ***\n"
        )
        return LiveExecutor()
    return PaperExecutor()
