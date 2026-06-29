"""
Run a simulation end-to-end and populate your ledger.

    python run_sim.py

Resets the table, runs all registered strategies over a few synthetic symbols,
and prints a summary. Then start the web app to see it in the dashboard.
"""
from app.engine import db, engine
from app.engine.feed import MockIntradayFeed
from app.engine.execution import SimExecution

# Import all strategies
from app.engine.strategy import RaynerTeoPullback
from app.engine.strategies.orb import OpeningRangeBreakout
from app.engine.strategies.pdh_pdl import PdhPdlStrategy
from app.engine.strategies.donchian import DonchianTurtle
from app.engine.strategies.rsi_connors import RsiConnors
from app.engine.strategies.vwap import VwapReversion
from app.engine.strategies.gap_fade import GapFade

SYMBOLS = ["AMC", "BBAI", "SOFI", "PLTR", "RIOT", "MARA"]


def main():
    db.init_db()
    db.reset()

    # Register all strategies
    engine.REGISTERED_STRATEGIES.clear()
    engine.register(RaynerTeoPullback())
    engine.register(OpeningRangeBreakout(range_minutes=15, rr=2.0))
    engine.register(PdhPdlStrategy(mode="breakout", rr=2.0))
    engine.register(PdhPdlStrategy(mode="reversal", rr=2.0))
    engine.register(DonchianTurtle(period=20, exit_period=10, rr=2.0))
    engine.register(RsiConnors(trend_period=50, rsi_period=2, rsi_oversold=10.0, exit_ma=5))  # Adjusted trend_period to 50 for shorter intraday warmup
    engine.register(VwapReversion(dev_multiplier=2.0, atr_period=14))
    engine.register(GapFade(gap_pct=0.005, catalyst_filter=True))  # Adjusted gap to 0.5% for more triggers in mock data

    feed = MockIntradayFeed(n_days=15, seed=7)
    execution = SimExecution(account_size=1000.0, risk_pct=0.01, slippage_bps=5.0)

    # Use a warmup period appropriate for the 50-SMA/200-SMA or 50-SMA trend filter
    engine.run(SYMBOLS, feed, execution, warmup=55)

    s = db.stats()
    print("\n=== Simulation complete ===")
    print(f"Closed trades : {s['total_trades']}")
    print(f"Win rate      : {s['win_rate']}%  ({s['wins']}W / {s['losses']}L)")
    print(f"Total P&L     : ${s['total_pnl']}")
    print(f"Expectancy    : {s['expectancy_r']} R per trade")
    print(f"Profit factor : {s['profit_factor']}")
    print(f"Final account : ${round(execution.account, 2)}")
    print("\nStart the dashboard with:  uvicorn app.api.main:app --reload")


if __name__ == "__main__":
    main()
