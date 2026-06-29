import datetime as dt
from app.engine.strategy import Strategy, Signal, Bar


class OpeningRangeBreakout(Strategy):
    """
    Opening Range Breakout (ORB) Strategy.
    Identifies the high/low range of the first N minutes of the session (9:30 AM EST start),
    then enters a long trade on a breakout above the high, or a short trade
    on a breakout below the low.
    Only one trade is allowed per calendar day.
    """
    name = "opening_range_breakout"

    def __init__(self, range_minutes=15, rr=2.0):
        self.range_minutes = range_minutes
        self.rr = rr

        # State tracking
        self.current_day = None
        self.range_high = None
        self.range_low = None
        self.traded_today = False

    def on_bar(self, bars: list[Bar]) -> Signal | None:
        if not bars:
            return None

        bar = bars[-1]
        try:
            bar_time = dt.datetime.fromisoformat(bar.time)
        except ValueError:
            # Fall back to returning None if timestamp is not intraday format
            return None

        bar_date = bar_time.date()
        session_start = dt.datetime.combine(bar_date, dt.time(9, 30))

        # Reset states on a new calendar day
        if bar_date != self.current_day:
            self.current_day = bar_date
            self.range_high = -999999.0
            self.range_low = 999999.0
            self.traded_today = False

        if bar_time < session_start:
            return None

        # Calculate minutes elapsed since the session open
        elapsed_minutes = (bar_time - session_start).total_seconds() / 60

        # 1) Inside the opening range window: record the session boundaries
        if elapsed_minutes < self.range_minutes:
            self.range_high = max(self.range_high, bar.high)
            self.range_low = min(self.range_low, bar.low)
            return None

        # 2) Outside the opening range: trigger once per day if range is set
        if self.traded_today or self.range_high == -999999.0:
            return None

        # Bullish Breakout
        if bar.close > self.range_high:
            self.traded_today = True
            entry = bar.close
            stop = self.range_low
            risk = entry - stop
            if risk <= 0:
                return None
            target = entry + self.rr * risk
            return Signal(
                side="long",
                entry=entry,
                stop=stop,
                target=target,
                reason=f"Bullish ORB breakout above {round(self.range_high, 3)}",
            )

        # Bearish Breakout
        elif bar.close < self.range_low:
            self.traded_today = True
            entry = bar.close
            stop = self.range_high
            risk = stop - entry
            if risk <= 0:
                return None
            target = entry - self.rr * risk
            return Signal(
                side="short",
                entry=entry,
                stop=stop,
                target=target,
                reason=f"Bearish ORB breakout below {round(self.range_low, 3)}",
            )

        return None
