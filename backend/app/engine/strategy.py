"""
Strategies. The contract is dead simple and broker-agnostic:

    strategy.on_bar(bars) -> Signal | None

`bars` is the rolling history (oldest -> newest) for ONE symbol.
A strategy looks only at bars and returns a Signal (or None to do nothing).
It never talks to a broker, a database, or the network. That isolation is what
lets you run ten strategies side by side and compare them fairly.

To add a strategy: subclass Strategy, implement on_bar, register it in engine.py.
"""
from dataclasses import dataclass


@dataclass
class Bar:
    time: str
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class Signal:
    side: str          # 'long' or 'short'
    entry: float       # intended entry price
    stop: float        # protective stop
    target: float      # profit target
    reason: str = ""   # human-readable why, shown in the UI later


def sma(values, n):
    if len(values) < n:
        return None
    return sum(values[-n:]) / n


class Strategy:
    name = "base"

    def on_bar(self, bars: list[Bar]) -> Signal | None:
        raise NotImplementedError

    def should_exit(self, bars: list[Bar], position: dict) -> bool:
        """
        Check if an open position should be closed based on custom strategy exit rules.
        """
        return False


class RaynerTeoPullback(Strategy):
    """
    Trade with the higher-timeframe trend, buy the pullback. (Rayner Teo's
    bread and butter, and a clean fit for free/delayed data because it holds
    longer than a few minutes.)

    Rules, fully mechanical:
      - Trend filter: 50-SMA > 200-SMA  (uptrend) -> only longs
      - Pullback: prior close dipped to/below the 20-SMA
      - Trigger: current close turns back UP above the 20-SMA
      - Stop: most recent swing low over lookback window
      - Target: 2x risk (your 2:1 worksheet rule)
    """
    name = "rayner_teo_pullback"

    def __init__(self, fast=20, mid=50, slow=200, swing_lookback=10, rr=2.0):
        self.fast, self.mid, self.slow = fast, mid, slow
        self.swing_lookback = swing_lookback
        self.rr = rr

    def on_bar(self, bars: list[Bar]) -> Signal | None:
        if len(bars) < self.slow + 2:
            return None

        closes = [b.close for b in bars]
        f, m, s = sma(closes, self.fast), sma(closes, self.mid), sma(closes, self.slow)
        if None in (f, m, s):
            return None

        uptrend = m > s
        if not uptrend:
            return None  # long-only for now; short side is a later module

        prev_close = closes[-2]
        curr_close = closes[-1]
        # Pullback then reclaim: dipped to the fast MA, now closing back above it
        pulled_back = prev_close <= sma(closes[:-1], self.fast)
        reclaiming = curr_close > f
        if not (pulled_back and reclaiming):
            return None

        swing_low = min(b.low for b in bars[-self.swing_lookback:])
        entry = curr_close
        stop = swing_low
        risk = entry - stop
        if risk <= 0:
            return None
        target = entry + self.rr * risk

        return Signal(
            side="long", entry=entry, stop=stop, target=target,
            reason=f"Uptrend (50>200), pullback to {self.fast}MA then reclaim",
        )
