"""
Data layer: pulls OHLCV candles from the exchange via ccxt.
Same function serves both backtesting (large historical pull) and the live
loop (small recent pull) so strategy code never has to know the difference.
"""
import ccxt
import pandas as pd
import config


def get_exchange():
    exchange_class = getattr(ccxt, config.EXCHANGE_NAME)
    exchange = exchange_class({
        "apiKey": config.API_KEY,
        "secret": config.API_SECRET,
        "enableRateLimit": True,
    })
    return exchange


def fetch_ohlcv(symbol=config.SYMBOL, timeframe=config.TIMEFRAME,
                 limit=500, since=None):
    """
    Returns a DataFrame with columns: timestamp, open, high, low, close, volume.
    `limit` is capped by the exchange (usually 500-1000 per call) -- for large
    historical pulls, page through using `since`.
    """
    exchange = get_exchange()
    raw = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit, since=since)
    df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df


def fetch_historical(symbol=config.SYMBOL, timeframe=config.TIMEFRAME,
                      days_back=365):
    """
    Pages through the exchange's API to build a longer historical dataset
    than a single call allows. Used by backtest.py.
    """
    exchange = get_exchange()
    ms_per_candle = exchange.parse_timeframe(timeframe) * 1000
    since = exchange.milliseconds() - days_back * 24 * 60 * 60 * 1000

    all_rows = []
    while True:
        batch = exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=500)
        if not batch:
            break
        all_rows.extend(batch)
        last_ts = batch[-1][0]
        if last_ts == since:
            break
        since = last_ts + ms_per_candle
        if last_ts >= exchange.milliseconds() - ms_per_candle:
            break

    df = pd.DataFrame(all_rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df = df.drop_duplicates(subset="timestamp").reset_index(drop=True)
    return df
