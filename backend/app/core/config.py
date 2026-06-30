import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


# --- Data / broker (see docs/03_Data_Sources.md) ---
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", "")
TRADIER_TOKEN = os.getenv("TRADIER_TOKEN", "")
TRADIER_BASE = os.getenv("TRADIER_BASE", "https://api.tradier.com/v1")
ALPACA_KEY = os.getenv("ALPACA_KEY", "")
ALPACA_SECRET = os.getenv("ALPACA_SECRET", "")
FINNHUB_KEY = os.getenv("FINNHUB_KEY", "")

# --- LLM inference for agents (Phase 4+) ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")


# --- Risk limits (deterministic; an LLM never changes these) ---
ACCOUNT_SIZE = float(os.getenv("ACCOUNT_SIZE", "1000"))
RISK_PCT_PER_TRADE = float(os.getenv("RISK_PCT_PER_TRADE", "0.01"))
DAILY_MAX_LOSS_PCT = float(os.getenv("DAILY_MAX_LOSS_PCT", "0.06"))
