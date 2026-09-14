"""
Turns raw OHLCV into model-ready features. Pure functions: same input df
always produces the same output df, which keeps this testable and keeps
backtest/live behavior identical.
"""
import pandas as pd
import ta


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Trend
    df["sma_20"] = ta.trend.sma_indicator(df["close"], window=20)
    df["sma_50"] = ta.trend.sma_indicator(df["close"], window=50)
    df["ema_12"] = ta.trend.ema_indicator(df["close"], window=12)
    df["ema_26"] = ta.trend.ema_indicator(df["close"], window=26)
    df["macd"] = ta.trend.macd_diff(df["close"])

    # Momentum
    df["rsi_14"] = ta.momentum.rsi(df["close"], window=14)
    df["stoch_k"] = ta.momentum.stoch(df["high"], df["low"], df["close"])

    # Volatility
    bb = ta.volatility.BollingerBands(df["close"], window=20)
    df["bb_width"] = bb.bollinger_wband()
    df["atr_14"] = ta.volatility.average_true_range(df["high"], df["low"], df["close"], window=14)

    # Volume
    df["volume_change"] = df["volume"].pct_change()

    # Price-derived
    df["return_1"] = df["close"].pct_change(1)
    df["return_5"] = df["close"].pct_change(5)
    df["sma_ratio"] = df["sma_20"] / df["sma_50"]

    df = df.dropna().reset_index(drop=True)
    return df


def make_labels(df: pd.DataFrame, horizon: int = 1, threshold: float = 0.0015) -> pd.DataFrame:
    """
    Label = 1 if price rises more than `threshold` over the next `horizon`
    candles, 0 otherwise. A dead-zone (no label 'down' class needed here since
    this is binary; threshold filters out noise-level moves).
    """
    df = df.copy()
    future_return = df["close"].shift(-horizon) / df["close"] - 1
    df["label"] = (future_return > threshold).astype(int)
    df = df.iloc[:-horizon]  # drop rows with no future data
    return df


FEATURE_COLUMNS = [
    "sma_20", "sma_50", "ema_12", "ema_26", "macd",
    "rsi_14", "stoch_k", "bb_width", "atr_14",
    "volume_change", "return_1", "return_5", "sma_ratio",
]
