import os
import sys
from pathlib import Path

# Add backend directory to sys.path so 'app' can be imported
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.engine import db, engine
from app.engine.feed import MockFeed
from app.engine.execution import SimExecution
from app.engine.strategy import RaynerTeoPullback


def test_simulation_smoke():
    # Initialize and reset the ledger database
    db.init_db()
    db.reset()

    # Register only the baseline strategy
    engine.REGISTERED_STRATEGIES.clear()
    engine.register(RaynerTeoPullback())

    # Set up synthetic feed and simulated execution
    feed = MockFeed(n_bars=400, seed=7)
    execution = SimExecution(account_size=1000.0, risk_pct=0.01, slippage_bps=5.0)

    # Run the engine
    symbols = ["AMC", "BBAI", "SOFI", "PLTR", "RIOT", "MARA"]
    engine.run(symbols, feed, execution)

    # Fetch results from db
    s = db.stats()

    # Verify that the simulation produced trades and stats are populated
    assert s["total_trades"] >= 1, "Simulation did not produce any trades"
    assert s["win_rate"] >= 0.0
    assert execution.account > 0.0
