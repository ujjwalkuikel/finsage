import datetime as dt
from app.engine.strategy import Strategy, Signal, Bar
from app.engine.strategies.donchian import compute_atr


class VwapReversion(Strategy):
    """
    VWAP Reversion Strategy.
    Resets VWAP calculations daily.
    Enters long on price deviations below VWAP - (dev_multiplier * ATR).
    Enters short on price deviations above VWAP + (dev_multiplier * ATR).
    Exits dynamically when price reclaims the VWAP level.
    """
    name = "vwap_reversion"

    def __init__(self, dev_multiplier=2.0, atr_period=14, rr=2.0):
        self.dev_multiplier = dev_multiplier
        self.atr_period = atr_period
        self.rr = rr

        # State tracking
        self.current_day = None
        self.cum_pv = 0.0
        self.cum_vol = 0.0
        self.vwap = None
        self.traded_today = False

    def on_bar(self, bars: list[Bar]) -> Signal | None:
        if len(bars) < self.atr_period + 2:
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
            self.cum_pv = 0.0
            self.cum_vol = 0.0
            self.traded_today = False

        # Accumulate VWAP PV and Volume
        typical_price = (bar.high + bar.low + bar.close) / 3.0
        self.cum_pv += typical_price * bar.volume
        self.cum_vol += bar.volume
        self.vwap = self.cum_pv / self.cum_vol if self.cum_vol > 0 else bar.close

        # Do not enter a trade if we traded today
        if self.traded_today:
            return None

        # Ignore first 15 mins to let range / VWAP stabilize
        session_start = dt.datetime.combine(bar_date, dt.time(9, 30))
        if bar_time <= session_start + dt.timedelta(minutes=15):
            return None

        atr = compute_atr(bars, self.atr_period)
        if atr is None or atr <= 0:
            return None

        entry = bar.close
        offset = self.dev_multiplier * atr

        # Bullish Reversion entry: price deviates far below VWAP
        if entry < self.vwap - offset:
            self.traded_today = True
            stop = entry - offset
            # Target is the current VWAP (can also exit dynamically in should_exit)
            target = self.vwap
            return Signal(
                side="long",
                entry=entry,
                stop=stop,
                target=target,
                reason=f"Bullish VWAP reversion below {round(self.vwap - offset, 3)}",
            )

        # Bearish Reversion entry: price deviates far above VWAP
        elif entry > self.vwap + offset:
            self.traded_today = True
            stop = entry + offset
            target = self.vwap
            return Signal(
                side="short",
                entry=entry,
                stop=stop,
                target=target,
                reason=f"Bearish VWAP reversion above {round(self.vwap + offset, 3)}",
            )

        return None

    def should_exit(self, bars: list[Bar], position: dict) -> bool:
        if not bars:
            return False

        bar = bars[-1]
        try:
            bar_time = dt.datetime.fromisoformat(bar.time)
        except ValueError:
            return False

        # Recalculate daily VWAP for the exit check
        bar_date = bar_time.date()
        
        # Reset and recalculate for current day's bars
        today_bars = []
        for b in bars:
            try:
                bt = dt.datetime.fromisoformat(b.time)
                if bt.date() == bar_date:
                    today_bars.append(b)
            except ValueError:
                continue

        if not today_bars:
            return False

        cum_pv = 0.0
        cum_vol = 0.0
        for b in today_bars:
            tp = (b.high + b.low + b.close) / 3.0
            cum_pv += tp * b.volume
            cum_vol += b.volume

        vwap_val = cum_pv / cum_vol if cum_vol > 0 else bar.close

        # Long positions exit when closing above VWAP
        if position["side"] == "long" and bar.close >= vwap_val:
            return True
        # Short positions exit when closing below VWAP
        elif position["side"] == "short" and bar.close <= vwap_val:
            return True

        return False
