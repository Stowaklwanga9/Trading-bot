"""
Risk layer: this is the one component nothing else is allowed to bypass.
It decides position size, attaches stop-loss/take-profit, and can veto a
trade outright (return None) regardless of how confident the model is.
"""
import config


class RiskManager:
    def __init__(self, equity: float):
        self.equity = equity
        self.starting_equity_today = equity
        self.open_positions = 0
        self.halted = False

    def reset_daily(self, equity: float):
        """Call once per day (or on startup) to reset the daily-loss tracker."""
        self.starting_equity_today = equity
        self.halted = False

    def update_equity(self, new_equity: float):
        self.equity = new_equity
        daily_loss_pct = (self.starting_equity_today - new_equity) / self.starting_equity_today
        if daily_loss_pct >= config.MAX_DAILY_LOSS_PCT:
            self.halted = True
            print(
                f"[RISK] Daily loss limit hit ({daily_loss_pct:.2%}). "
                f"Halting new trades until reset."
            )

    def size_position(self, entry_price: float) -> float:
        """
        Fixed-fractional sizing: risk MAX_RISK_PER_TRADE_PCT of equity,
        sized so that hitting the stop-loss loses exactly that fraction.
        Returns quantity of the asset to buy.
        """
        risk_amount = self.equity * config.MAX_RISK_PER_TRADE_PCT
        stop_distance = entry_price * config.STOP_LOSS_PCT
        if stop_distance <= 0:
            return 0.0
        quantity = risk_amount / stop_distance
        return quantity

    def evaluate(self, direction: int, confidence: float, entry_price: float):
        """
        Final gate. Returns an order dict or None (veto).
        Nothing downstream should place an order that didn't come from here.
        """
        if self.halted:
            return None
        if self.open_positions >= config.MAX_OPEN_POSITIONS:
            return None
        if confidence < config.MIN_MODEL_CONFIDENCE:
            return None
        if direction != 1:
            # This skeleton only takes long positions for simplicity/safety.
            return None

        quantity = self.size_position(entry_price)
        if quantity <= 0:
            return None

        return {
            "side": "buy",
            "quantity": quantity,
            "entry_price": entry_price,
            "stop_loss": entry_price * (1 - config.STOP_LOSS_PCT),
            "take_profit": entry_price * (1 + config.TAKE_PROFIT_PCT),
        }
