"""
The web layer. FastAPI serves the dashboard and exposes your ledger as JSON.
Endpoints:
    GET /                -> the dashboard
    GET /api/stats       -> summary metrics
    GET /api/trades      -> the trades ledger
    POST /api/run-sim    -> re-run the simulation (handy for the demo)

This is where you'd later add WebSocket push for live updates, auth, and
agentic endpoints (e.g. POST /api/strategies to spin up a new strategy module).
"""
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.engine import db

app = FastAPI(title="AII Platform")

STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "static"


@app.on_event("startup")
def _startup():
    db.init_db()


@app.get("/api/stats")
def get_stats():
    return JSONResponse(db.stats())


@app.get("/api/trades")
def get_trades(limit: int = 200):
    return JSONResponse(db.all_trades(limit))


@app.post("/api/run-sim")
def run_sim():
    # imported lazily so the web app starts even before deps for sim are loaded
    from app.engine import engine
    from app.engine.feed import MockIntradayFeed
    from app.engine.execution import SimExecution
    
    from app.engine.strategy import RaynerTeoPullback
    from app.engine.strategies.orb import OpeningRangeBreakout
    from app.engine.strategies.pdh_pdl import PdhPdlStrategy
    from app.engine.strategies.donchian import DonchianTurtle
    from app.engine.strategies.rsi_connors import RsiConnors
    from app.engine.strategies.vwap import VwapReversion
    from app.engine.strategies.gap_fade import GapFade

    db.reset()
    engine.REGISTERED_STRATEGIES.clear()
    engine.register(RaynerTeoPullback())
    engine.register(OpeningRangeBreakout(range_minutes=15, rr=2.0))
    engine.register(PdhPdlStrategy(mode="breakout", rr=2.0))
    engine.register(PdhPdlStrategy(mode="reversal", rr=2.0))
    engine.register(DonchianTurtle(period=20, exit_period=10, rr=2.0))
    engine.register(RsiConnors(trend_period=50, rsi_period=2, rsi_oversold=10.0, exit_ma=5))
    engine.register(VwapReversion(dev_multiplier=2.0, atr_period=14))
    engine.register(GapFade(gap_pct=0.005, catalyst_filter=True))

    ex = SimExecution(account_size=1000.0, risk_pct=0.01)
    engine.run(["AMC", "BBAI", "SOFI", "PLTR", "RIOT", "MARA"], MockIntradayFeed(n_days=15, seed=7), ex, warmup=55)
    return JSONResponse({"ok": True, "stats": db.stats()})


@app.get("/")
def dashboard():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
