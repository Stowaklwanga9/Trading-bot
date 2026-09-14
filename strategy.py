"""
Strategy layer: glues the model's opinion to the risk manager's veto power.
This file should never place an order directly -- it only produces an
order dict (or None) for execution.py to act on.
"""
from feature_engineering import add_features
import ml_model


class Strategy:
    def __init__(self, model, risk_manager):
        self.model = model
        self.risk_manager = risk_manager

    def decide(self, raw_ohlcv_df):
        """
        raw_ohlcv_df: recent OHLCV candles (needs enough history for
        indicators to warm up, e.g. 60+ candles for a 50-period SMA).
        Returns an order dict from risk_manager.evaluate(), or None.
        """
        features_df = add_features(raw_ohlcv_df)
        if features_df.empty:
            return None

        latest = features_df.iloc[-1]
        direction, confidence = ml_model.predict_signal(self.model, latest)
        entry_price = latest["close"]

        order = self.risk_manager.evaluate(direction, confidence, entry_price)
        if order:
            order["confidence"] = confidence
        return order
