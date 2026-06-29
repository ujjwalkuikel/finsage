import os
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.engine.strategy import RaynerTeoPullback
from app.engine.feed import MockFeed
from app.validation.gauntlet import backtest, MemoryLedger


def test_memory_ledger():
    ledger = MemoryLedger()
    assert ledger.stats()["total_trades"] == 0

    trade_id = ledger.insert_open_trade({
        "strategy": "test_strat",
        "symbol": "TEST",
        "side": "long",
        "qty": 10.0,
        "entry_time": "2024-01-01",
        "entry_price": 100.0,
        "stop_price": 90.0,
        "target_price": 120.0
    })
    assert trade_id == 1
    assert ledger.stats()["total_trades"] == 0  # 0 closed trades

    ledger.close_trade(trade_id, "2024-01-02", 110.0, 100.0, 1.0, "target")
    stats = ledger.stats()
    assert stats["total_trades"] == 1
    assert stats["wins"] == 1
    assert stats["total_pnl"] == 100.0
    assert stats["expectancy_r"] == 1.0


def test_backtest_runner():
    strategy = RaynerTeoPullback()
    feed = MockFeed(n_bars=400, seed=7)
    bars = list(feed.bars("PLTR"))

    res = backtest(strategy, bars)
    stats = res["stats"]
    trades = res["trades"]

    assert stats["total_trades"] >= 0
    assert "max_dd" in stats
    assert isinstance(stats["max_dd"], float)
    if stats["total_trades"] > 0:
        assert len(trades) == stats["total_trades"]


def test_in_sample_report():
    from app.engine.strategy import Strategy
    from app.validation.gauntlet import in_sample_report

    class HighlyOverfitStrategy(Strategy):
        name = "overfit_strat"
        def __init__(self):
            # 6 parameters
            self.p1 = 1
            self.p2 = 2
            self.p3 = 3
            self.p4 = 4
            self.p5 = 5
            self.p6 = 6

        def on_bar(self, bars):
            return None

    strategy = HighlyOverfitStrategy()
    feed = MockFeed(n_bars=100, seed=42)
    bars = list(feed.bars("AAPL"))

    report = in_sample_report(strategy, bars)
    stats = report["stats"]

    assert stats["num_parameters"] == 6
    # Should flag warning for too many parameters and low trade count (0 trades)
    assert len(stats["warnings"]) >= 2
    assert stats["overfit_risk"] == "high"


def test_permute_bars():
    import math
    from app.validation.gauntlet import permute_bars

    feed = MockFeed(n_bars=200, seed=12)
    bars = list(feed.bars("NVDA"))

    permuted = permute_bars(bars, block_size=10, seed=99)

    assert len(bars) == len(permuted)

    # Compute original returns standard deviation
    orig_rets = []
    for i in range(1, len(bars)):
        orig_rets.append((bars[i].close - bars[i-1].close) / bars[i-1].close)

    perm_rets = []
    for i in range(1, len(permuted)):
        perm_rets.append((permuted[i].close - permuted[i-1].close) / permuted[i-1].close)

    def std_dev(lst):
        mean = sum(lst) / len(lst)
        variance = sum((x - mean) ** 2 for x in lst) / (len(lst) - 1)
        return math.sqrt(variance)

    orig_std = std_dev(orig_rets)
    perm_std = std_dev(perm_rets)

    # Volatility should be identical or extremely close (tiny differences from price rounding are expected)
    assert abs(orig_std - perm_std) < 1e-5
    # Make sure they are not the exact same order of bars
    assert [b.close for b in bars] != [b.close for b in permuted]


def test_monte_carlo_permutation():
    from app.validation.gauntlet import monte_carlo_permutation

    strategy = RaynerTeoPullback()
    feed = MockFeed(n_bars=200, seed=7)
    bars = list(feed.bars("SOFI"))

    # Run with small n for speed in tests
    res = monte_carlo_permutation(strategy, bars, n=20)

    assert "real_expectancy" in res
    assert "p_value" in res
    assert res["n_simulations"] == 20
    assert 0.0 <= res["p_value"] <= 1.0


def test_walk_forward():
    from app.validation.gauntlet import walk_forward

    feed = MockFeed(n_bars=350, seed=7)
    bars = list(feed.bars("PLTR"))

    # Walk forward with 200 train size and 50 test size
    res = walk_forward(RaynerTeoPullback, bars, train_size=250, test_size=50)

    assert "trades" in res
    assert "stats" in res
    stats = res["stats"]
    assert "total_trades" in stats
    assert "expectancy_r" in stats
    assert "max_dd" in stats


def test_walk_forward_permutation():
    from app.validation.gauntlet import walk_forward_permutation

    feed = MockFeed(n_bars=300, seed=10)
    bars = list(feed.bars("BBAI"))

    # Walk forward permutation test with a small number of simulations for speed
    res = walk_forward_permutation(RaynerTeoPullback, bars, train_size=200, test_size=50, n=5)

    assert "real_expectancy" in res
    assert "p_value" in res
    assert res["n_simulations"] == 5
    assert 0.0 <= res["p_value"] <= 1.0


def test_cross_sectional():
    from app.validation.gauntlet import cross_sectional

    strategy = RaynerTeoPullback()
    feed = MockFeed(n_bars=200, seed=1)
    bars_dict = {
        "AMC": list(feed.bars("AMC")),
        "BBAI": list(feed.bars("BBAI")),
    }

    res = cross_sectional(strategy, bars_dict)

    assert "AMC" in res
    assert "BBAI" in res
    assert "total_trades" in res["AMC"]
    assert "expectancy_r" in res["BBAI"]


def test_validate_harness():
    from app.validation.gauntlet import validate

    feed = MockFeed(n_bars=300, seed=42)
    bars = list(feed.bars("AAPL"))

    # Run complete gauntlet with small simulations for speed
    res = validate(RaynerTeoPullback, bars, train_size=200, test_size=50, n_sims=5)

    assert "strategy" in res
    assert "verdict" in res
    assert "failures" in res
    assert "in_sample" in res
    assert "monte_carlo" in res
    assert "walk_forward" in res
    assert "walk_forward_permutation" in res
    assert res["verdict"] in ("PASS", "FAIL")

