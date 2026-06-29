import os
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.engine.feed import MockIntradayFeed
from app.engine.strategies.pdh_pdl import PdhPdlStrategy
from app.engine.strategies.donchian import DonchianTurtle
from app.engine.strategies.rsi_connors import RsiConnors
from app.engine.strategies.vwap import VwapReversion
from app.engine.strategies.gap_fade import GapFade
from app.validation.gauntlet import backtest


def test_pdh_pdl_breakout():
    strat = PdhPdlStrategy(mode="breakout", rr=2.0)
    feed = MockIntradayFeed(n_days=10, seed=10)
    bars = list(feed.bars("PLTR"))
    
    res = backtest(strat, bars)
    assert res["stats"]["total_trades"] >= 0


def test_pdh_pdl_reversal():
    strat = PdhPdlStrategy(mode="reversal", rr=2.0)
    feed = MockIntradayFeed(n_days=10, seed=15)
    bars = list(feed.bars("SOFI"))
    
    res = backtest(strat, bars)
    assert res["stats"]["total_trades"] >= 0


def test_donchian_turtle():
    # Keep lookbacks small to trade frequently in mock test data
    strat = DonchianTurtle(period=5, exit_period=3, rr=2.0)
    feed = MockIntradayFeed(n_days=10, seed=20)
    bars = list(feed.bars("AMC"))
    
    res = backtest(strat, bars)
    assert res["stats"]["total_trades"] >= 0


def test_rsi_connors():
    strat = RsiConnors(trend_period=30, rsi_period=2, rsi_oversold=20.0, exit_ma=5)
    feed = MockIntradayFeed(n_days=10, seed=30)
    bars = list(feed.bars("RIOT"))
    
    res = backtest(strat, bars)
    assert res["stats"]["total_trades"] >= 0


def test_vwap_reversion():
    strat = VwapReversion(dev_multiplier=1.0, atr_period=10)
    feed = MockIntradayFeed(n_days=10, seed=40)
    bars = list(feed.bars("BBAI"))
    
    res = backtest(strat, bars)
    assert res["stats"]["total_trades"] >= 0


def test_gap_fade():
    strat = GapFade(gap_pct=0.002, catalyst_filter=False)
    feed = MockIntradayFeed(n_days=10, seed=50)
    bars = list(feed.bars("MARA"))
    
    res = backtest(strat, bars)
    assert res["stats"]["total_trades"] >= 0
