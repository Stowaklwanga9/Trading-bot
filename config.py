"""
Central configuration. Reads secrets from environment (.env) so keys never
end up hardcoded or committed to source control.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# --- Exchange / auth ---
EXCHANGE_NAME = os.getenv("EXCHANGE", "binance")
API_KEY = os.getenv("API_KEY", "")
API_SECRET = os.getenv("API_SECRET", "")

# "paper" simulates fills locally using real market data.
# "live" sends real orders. Never default this to "live".
TRADING_MODE = os.getenv("TRADING_MODE", "paper")

# --- Market / instrument ---
SYMBOL = os.getenv("SYMBOL", "BTC/USDT")
TIMEFRAME = os.getenv("TIMEFRAME", "15m")  # candle interval

# --- Risk management (hard limits, enforced in risk_manager.py) ---
MAX_RISK_PER_TRADE_PCT = 0.01      # never risk more than 1% of equity per trade
MAX_DAILY_LOSS_PCT = 0.03          # halt trading for the day past 3% drawdown
MAX_OPEN_POSITIONS = 1             # keep it simple: one position at a time
STOP_LOSS_PCT = 0.02               # 2% stop-loss from entry
TAKE_PROFIT_PCT = 0.04             # 4% take-profit from entry (2:1 reward:risk)

# --- Model ---
MODEL_PATH = "model.joblib"
MIN_MODEL_CONFIDENCE = 0.55        # ignore signals the model isn't reasonably sure about

# --- Starting paper equity (irrelevant once live, but needed for sizing sim) ---
PAPER_STARTING_EQUITY = 10_000.0
