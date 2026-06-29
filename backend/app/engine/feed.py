"""
The feed adapter. Everything upstream of your strategies hides behind one
interface: `bars(symbol) -> iterator of Bar`. Today that's a synthetic
generator so the whole system runs with NO account and NO network. Tomorrow you
write a TradierFeed / AlpacaFeed with the same method, and the engine doesn't
notice the difference.
"""
import random
import datetime as dt
from .strategy import Bar


class Feed:
    def bars(self, symbol: str):
        raise NotImplementedError


class MockFeed(Feed):
    """
    Synthetic but realistic-ish daily bars: a random walk with a gentle,
    slowly-flipping trend, so trend-following strategies actually find setups.
    Deterministic when you pass a seed, so your sim is reproducible.
    """
    def __init__(self, n_bars=400, start_price=20.0, seed=42):
        self.n_bars = n_bars
        self.start_price = start_price
        self.seed = seed

    def bars(self, symbol: str):
        rng = random.Random(f"{self.seed}-{symbol}")
        price = self.start_price
        drift = rng.uniform(-0.001, 0.002)
        start = dt.date(2024, 1, 1)
        for i in range(self.n_bars):
            # Flip the trend occasionally so we get both up and down regimes
            if i % 60 == 0:
                drift = rng.uniform(-0.0015, 0.0025)
            shock = rng.gauss(drift, 0.02)
            open_ = price
            close = max(0.5, price * (1 + shock))
            high = max(open_, close) * (1 + abs(rng.gauss(0, 0.006)))
            low = min(open_, close) * (1 - abs(rng.gauss(0, 0.006)))
            vol = rng.randint(200_000, 2_000_000)
            day = start + dt.timedelta(days=i)
            yield Bar(time=day.isoformat(), open=round(open_, 3),
                      high=round(high, 3), low=round(low, 3),
                      close=round(close, 3), volume=vol)
            price = close
