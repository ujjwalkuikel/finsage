"""
TradierFeed — live consolidated stream for paper/live trading. (Phase 3)

Implements the engine's Feed interface. See docs/03 for the streaming gotchas:
  - real-time consolidated data is free for brokerage account holders
  - websocket session IDs are short-lived: fetch fresh at startup/reconnect
  - paper environment can't stream; use live stream + our own SimExecution

TODO:
  - create streaming session, connect wss://ws.tradier.com/v1/
  - subscribe filters: timesale, quote
  - aggregate ticks -> 1-min engine.strategy.Bar
"""
from app.engine.feed import Feed


class TradierFeed(Feed):
    def __init__(self, token: str):
        self.token = token

    def bars(self, symbol: str):
        raise NotImplementedError("Phase 3: implement Tradier websocket stream")
