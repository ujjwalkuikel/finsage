import datetime as dt
from app.engine.strategy import Strategy, Signal, Bar


class PdhPdlStrategy(Strategy):
    """
    Prior Day High / Prior Day Low (PDH/PDL) Strategy.
    Identifies prior day extremes and trades breakouts or reversals when they are breached.
    """
    name = "pdh_pdl"

    def __init__(self, mode="breakout", rr=2.0):
        self.mode = mode  # "breakout" or "reversal"
        self.rr = rr

        # State tracking
        self.current_day = None
        self.pdh = None
        self.pdl = None
        self.today_high = -999999.0
        self.today_low = 999999.0
        self.traded_today = False

        self.name = f"pdh_pdl_{mode}"

    def on_bar(self, bars: list[Bar]) -> Signal | None:
        if not bars:
            return None

        bar = bars[-1]
        try:
            bar_time = dt.datetime.fromisoformat(bar.time)
        except ValueError:
            return None

        bar_date = bar_time.date()

        # Day rollover check
        if bar_date != self.current_day:
            self.current_day = bar_date
            if self.today_high != -999999.0 and self.today_low != 999999.0:
                self.pdh = self.today_high
                self.pdl = self.today_low
            self.today_high = bar.high
            self.today_low = bar.low
            self.traded_today = False
            return None

        # Update current day's extremes
        self.today_high = max(self.today_high, bar.high)
        self.today_low = min(self.today_low, bar.low)

        # Do not trade if we already traded today or prior day levels are not set yet
        if self.traded_today or self.pdh is None or self.pdl is None:
            return None

        # Ignore trades in first 10 minutes to avoid market open whip
        session_start = dt.datetime.combine(bar_date, dt.time(9, 30))
        if bar_time <= session_start + dt.timedelta(minutes=10):
            return None

        if self.mode == "breakout":
            # Bullish Breakout above PDH
            if bar.close > self.pdh:
                self.traded_today = True
                entry = bar.close
                stop = self.pdl
                risk = entry - stop
                if risk <= 0:
                    return None
                return Signal(
                    side="long",
                    entry=entry,
                    stop=stop,
                    target=entry + self.rr * risk,
                    reason=f"Bullish breakout above PDH ({round(self.pdh, 3)})",
                )
            # Bearish Breakout below PDL
            elif bar.close < self.pdl:
                self.traded_today = True
                entry = bar.close
                stop = self.pdh
                risk = stop - entry
                if risk <= 0:
                    return None
                return Signal(
                    side="short",
                    entry=entry,
                    stop=stop,
                    target=entry - self.rr * risk,
                    reason=f"Bearish breakout below PDL ({round(self.pdl, 3)})",
                )

        elif self.mode == "reversal":
            # Bearish Reversal (Failed breakout of PDH)
            # High breached PDH, but close fell back below PDH
            if bar.high > self.pdh and bar.close < self.pdh:
                self.traded_today = True
                entry = bar.close
                stop = max(bar.high, self.pdh * 1.002)  # Stop is high of breakout bar or slightly above PDH
                risk = stop - entry
                if risk <= 0:
                    return None
                return Signal(
                    side="short",
                    entry=entry,
                    stop=stop,
                    target=entry - self.rr * risk,
                    reason=f"Bearish reversal: failed breach of PDH ({round(self.pdh, 3)})",
                )
            # Bullish Reversal (Failed breakdown of PDL)
            # Low breached PDL, but close reclaimed PDL
            elif bar.low < self.pdl and bar.close > self.pdl:
                self.traded_today = True
                entry = bar.close
                stop = min(bar.low, self.pdl * 0.998)
                risk = entry - stop
                if risk <= 0:
                    return None
                return Signal(
                    side="long",
                    entry=entry,
                    stop=stop,
                    target=entry + self.rr * risk,
                    reason=f"Bullish reversal: failed breach of PDL ({round(self.pdl, 3)})",
                )

        return None
