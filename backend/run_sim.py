"""
Run a simulation end-to-end and populate your ledger.

    python run_sim.py

Resets the table, runs the registered strategies over a few synthetic symbols,
and prints a summary. Then start the web app to see it in the dashboard.
"""
from app.engine import db, engine
from app.engine.feed import MockFeed
from app.engine.execution import SimExecution
from app.engine.strategy import RaynerTeoPullback

SYMBOLS = ["AMC", "BBAI", "SOFI", "PLTR", "RIOT", "MARA"]  # just labels for the sim


def main():
    db.init_db()
    db.reset()

    engine.REGISTERED_STRATEGIES.clear()
    engine.register(RaynerTeoPullback())

    feed = MockFeed(n_bars=400, seed=7)
    execution = SimExecution(account_size=1000.0, risk_pct=0.01, slippage_bps=5.0)

    engine.run(SYMBOLS, feed, execution)

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
