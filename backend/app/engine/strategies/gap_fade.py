import datetime as dt
from app.engine.strategy import Strategy, Signal, Bar


class GapFade(Strategy):
    """
    Gap Fade Strategy.
    Identifies morning gaps (> gap_pct) relative to the prior day's close.
    If catalyst_filter is active, fades are skipped on volume shocks (first bar volume > 4x avg).
    Enters a fade trade when the opening bar's high/low is breached.
    Targets a complete gap fill (prior day's close price).
    """
    name = "gap_fade"

    def __init__(self, gap_pct=0.01, catalyst_filter=True, rr=2.0, catalyst_present_override=False):
        self.gap_pct = gap_pct
        self.catalyst_filter = catalyst_filter
        self.rr = rr
        self.catalyst_present_override = catalyst_present_override

        # State tracking
        self.current_day = None
        self.prior_close = None
        self.prev_bar_close = None
        
        self.first_bar_open = None
        self.first_bar_high = None
        self.first_bar_low = None
        self.first_bar_vol = None
        
        self.traded_today = False
        self.gap_direction = None  # "up", "down", or None
        
        # Keep track of daily volumes to calculate average
        self.daily_volumes = []
        self.current_day_volume = 0

    def on_bar(self, bars: list[Bar]) -> Signal | None:
        if not bars:
            return None

        bar = bars[-1]
        try:
            bar_time = dt.datetime.fromisoformat(bar.time)
        except ValueError:
            return None

        bar_date = bar_time.date()

        # Rollover check
        if bar_date != self.current_day:
            if self.current_day is not None:
                self.prior_close = self.prev_bar_close
                if self.current_day_volume > 0:
                    self.daily_volumes.append(self.current_day_volume)
                    if len(self.daily_volumes) > 5:
                        self.daily_volumes.pop(0)

            self.current_day = bar_date
            self.current_day_volume = 0
            
            # Setup first bar of the day
            self.first_bar_open = bar.open
            self.first_bar_high = bar.high
            self.first_bar_low = bar.low
            self.first_bar_vol = bar.volume
            
            self.traded_today = False
            self.gap_direction = None

            # Calculate gap direction relative to prior close
            if self.prior_close is not None and self.prior_close > 0:
                gap = (self.first_bar_open - self.prior_close) / self.prior_close
                if gap >= self.gap_pct:
                    self.gap_direction = "up"
                elif gap <= -self.gap_pct:
                    self.gap_direction = "down"

            self.prev_bar_close = bar.close
            self.current_day_volume += bar.volume
            return None

        self.prev_bar_close = bar.close
        self.current_day_volume += bar.volume

        # Skip if we already traded, did not detect a gap, or do not have prior close
        if self.traded_today or self.gap_direction is None or self.prior_close is None:
            return None

        # Check catalyst filter
        catalyst_present = self.catalyst_present_override
        if self.catalyst_filter and len(self.daily_volumes) >= 2:
            avg_daily_vol = sum(self.daily_volumes) / len(self.daily_volumes)
            # 78 bars per session on 5-minute intervals. 
            # If the first bar volume is > 5% of average daily volume (~4x normal), we flag volume shock.
            if self.first_bar_vol > 0.05 * avg_daily_vol:
                catalyst_present = True

        if catalyst_present:
            return None

        session_start = dt.datetime.combine(bar_date, dt.time(9, 30))
        # Wait 10 minutes (allow range to establish)
        if bar_time <= session_start + dt.timedelta(minutes=10):
            return None

        # Bearish Fade (Gap Up): short breakout below opening low
        if self.gap_direction == "up" and bar.close < self.first_bar_low:
            self.traded_today = True
            entry = bar.close
            stop = self.first_bar_high
            target = self.prior_close
            
            # Sanity checks
            if stop <= entry:
                return None
            return Signal(
                side="short",
                entry=entry,
                stop=stop,
                target=target,
                reason=f"Fading Gap Up from {round(self.prior_close, 3)}: price fell below {round(self.first_bar_low, 3)}",
            )

        # Bullish Fade (Gap Down): long breakout above opening high
        elif self.gap_direction == "down" and bar.close > self.first_bar_high:
            self.traded_today = True
            entry = bar.close
            stop = self.first_bar_low
            target = self.prior_close
            
            if stop >= entry:
                return None
            return Signal(
                side="long",
                entry=entry,
                stop=stop,
                target=target,
                reason=f"Fading Gap Down from {round(self.prior_close, 3)}: price rose above {round(self.first_bar_high, 3)}",
            )

        return None
