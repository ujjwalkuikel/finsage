"""
PolygonFeed — historical bars for backtesting/validation. (Phase 3)

Implements the engine's Feed interface so it drops straight into engine.run().
See docs/03_Data_Sources.md for tier/limits (free: ~5 calls/min, 2yr, delayed).

TODO:
  - fetch /v2/aggs/ticker/{symbol}/range/{mult}/{span}/{from}/{to}
  - follow next_url pagination for minute data
  - cache pulls to CSV so we never re-request the same bars
  - map Polygon bars -> engine.strategy.Bar
"""
from app.engine.feed import Feed


class PolygonFeed(Feed):
    def __init__(self, api_key: str, timespan: str = "day"):
        self.api_key = api_key
        self.timespan = timespan

    def bars(self, symbol: str):
        raise NotImplementedError("Phase 3: implement Polygon historical fetch")
