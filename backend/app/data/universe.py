"""
Universe module. (Phase 3)
Handles watchlist and universe building filters.
"""

# A fixed, diverse watchlist of 20 liquid tickers across multiple sectors
WATCHLIST = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",  # Tech / Megacaps
    "JPM", "BAC", "V",                        # Financials
    "JNJ", "PFE", "UNH",                      # Healthcare
    "TSLA", "HD", "XOM",                      # Cons Cyclical / Energy
    "PG", "KO", "PEP",                        # Cons Defensive
    "PLTR", "SOFI", "RIOT"                    # Mid/Small Cap momentum names
]


def build_daily_universe() -> list[str]:
    """
    Stub to dynamically build the daily candidate list based on EOD queries
    (e.g., Average Volume > 1M, Price between $5 and $500).
    Currently returns the fixed WATCHLIST universe.
    """
    # In future phases, this can fetch EOD bars and screen candidates
    return WATCHLIST
