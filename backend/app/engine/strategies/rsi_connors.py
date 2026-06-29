from app.engine.strategy import Strategy, Signal, Bar


def sma(values: list[float], n: int) -> float | None:
    if len(values) < n:
        return None
    return sum(values[-n:]) / n


def compute_rsi(bars: list[Bar], period: int = 2) -> float | None:
    if len(bars) < period + 1:
        return None

    changes = []
    for i in range(1, len(bars)):
        changes.append(bars[i].close - bars[i - 1].close)

    gains = [max(c, 0) for c in changes]
    losses = [max(-c, 0) for c in changes]

    # First average is simple average
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    # Subsequent averages use Wilder's smoothing
    for i in range(period, len(changes)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0

    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


class RsiConnors(Strategy):
    """
    RSI(2) Connors Mean Reversion Strategy.
    Buys short-term oversold dips in an uptrend (above 200 SMA).
    Exits long positions immediately when price closes above a 5-period SMA.
    """
    name = "rsi_connors"

    def __init__(self, trend_period=200, rsi_period=2, rsi_oversold=10.0, exit_ma=5, swing_lookback=10):
        self.trend_period = trend_period
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.exit_ma = exit_ma
        self.swing_lookback = swing_lookback

    def on_bar(self, bars: list[Bar]) -> Signal | None:
        needed = max(self.trend_period, self.rsi_period) + 2
        if len(bars) < needed:
            return None

        closes = [b.close for b in bars]
        sma_trend = sma(closes, self.trend_period)
        if sma_trend is None or closes[-1] <= sma_trend:
            return None

        rsi_val = compute_rsi(bars, self.rsi_period)
        if rsi_val is None or rsi_val >= self.rsi_oversold:
            return None

        # Reclaimed oversold logic: entry on this dip
        entry = curr_close = closes[-1]
        swing_low = min(b.low for b in bars[-self.swing_lookback:])
        stop = swing_low

        risk = entry - stop
        if risk <= 0:
            return None

        # Hard protective target (exit MA typically hit first)
        target = entry + 2.0 * risk

        return Signal(
            side="long",
            entry=entry,
            stop=stop,
            target=target,
            reason=f"Uptrend (close > SMA {self.trend_period}), RSI({self.rsi_period}) oversold ({round(rsi_val, 1)} < {self.rsi_oversold})",
        )

    def should_exit(self, bars: list[Bar], position: dict) -> bool:
        if position["side"] == "long":
            closes = [b.close for b in bars]
            sma_exit = sma(closes, self.exit_ma)
            if sma_exit is not None and closes[-1] > sma_exit:
                return True
        return False
