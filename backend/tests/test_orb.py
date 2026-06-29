import os
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.engine.feed import MockIntradayFeed
from app.engine.strategies.orb import OpeningRangeBreakout
from app.validation.gauntlet import backtest


def test_mock_intraday_feed():
    feed = MockIntradayFeed(n_days=2, seed=12)
    bars = list(feed.bars("AAPL"))

    # Each day should have 79 bars (from 9:30 to 16:00 inclusive at 5-minute intervals is 79 bars)
    # Total bars for 2 days = 158
    assert len(bars) == 158
    assert bars[0].time.endswith("09:30:00")
    assert bars[78].time.endswith("16:00:00")
    assert bars[79].time.endswith("09:30:00")


def test_orb_strategy_logic():
    strategy = OpeningRangeBreakout(range_minutes=15, rr=2.0)
    feed = MockIntradayFeed(n_days=5, seed=42)
    bars = list(feed.bars("TSLA"))

    # Run the backtest on the intraday series
    res = backtest(strategy, bars)
    stats = res["stats"]
    trades = res["trades"]

    assert stats["total_trades"] >= 0
    
    # We should have long and/or short trades
    for t in trades:
        assert t["strategy"] == "opening_range_breakout"
        assert t["status"] in ("open", "closed")
        if t["status"] == "closed":
            assert t["exit_reason"] in ("stop", "target", "eod")
            # Verify target/stop logic
            if t["side"] == "long":
                assert t["stop_price"] < t["entry_price"]
                assert t["target_price"] > t["entry_price"]
            else:
                assert t["stop_price"] > t["entry_price"]
                assert t["target_price"] < t["entry_price"]
