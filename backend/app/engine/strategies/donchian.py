from app.engine.strategy import Strategy, Signal, Bar


def compute_tr(bar: Bar, prev_bar: Bar | None) -> float:
    if prev_bar is None:
        return bar.high - bar.low
    return max(
        bar.high - bar.low,
        abs(bar.high - prev_bar.close),
        abs(bar.low - prev_bar.close),
    )


def compute_atr(bars: list[Bar], period: int = 14) -> float | None:
    if len(bars) < period + 1:
        return None
    tr_values = []
    for i in range(1, len(bars)):
        tr_values.append(compute_tr(bars[i], bars[i - 1]))
    return sum(tr_values[-period:]) / period


class DonchianTurtle(Strategy):
    """
    Donchian Channel / Turtle Breakout Strategy.
    Enters long on N-bar breakout high, short on N-bar breakout low.
    Uses ATR-based stop loss sizing (stop = 2 * ATR).
    """
    name = "donchian_turtle"

    def __init__(self, period=20, exit_period=10, rr=2.0, atr_period=14):
        self.period = period
        self.exit_period = exit_period
        self.rr = rr
        self.atr_period = atr_period

    def on_bar(self, bars: list[Bar]) -> Signal | None:
        # We need enough bars for Donchian channel, ATR lookback, and previous close comparisons
        needed_bars = max(self.period, self.atr_period) + 2
        if len(bars) < needed_bars:
            return None

        atr = compute_atr(bars, self.atr_period)
        if atr is None or atr <= 0:
            return None

        curr_bar = bars[-1]
        
        # Donchian highs and lows of the previous N bars (excluding current bar)
        channel_bars = bars[-self.period - 1 : -1]
        highest_high = max(b.high for b in channel_bars)
        lowest_low = min(b.low for b in channel_bars)

        # Bullish Breakout
        if curr_bar.close > highest_high:
            entry = curr_bar.close
            stop = entry - 2.0 * atr
            risk = entry - stop
            return Signal(
                side="long",
                entry=entry,
                stop=stop,
                target=entry + self.rr * risk,
                reason=f"Bullish Donchian {self.period}-bar breakout",
            )

        # Bearish Breakout
        elif curr_bar.close < lowest_low:
            entry = curr_bar.close
            stop = entry + 2.0 * atr
            risk = stop - entry
            return Signal(
                side="short",
                entry=entry,
                stop=stop,
                target=entry - self.rr * risk,
                reason=f"Bearish Donchian {self.period}-bar breakout",
            )

        return None
