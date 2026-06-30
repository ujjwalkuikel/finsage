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
from pydantic import BaseModel

from app.engine import db

class AnalyzeRequest(BaseModel):
    ticker: str

class OrchestrateRequest(BaseModel):
    ticker: str
    proposed_trade: dict = None

app = FastAPI(title="AII Platform")


STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "static"


@app.on_event("startup")
def _startup():
    db.init_db()
    # Start Telegram bot polling in a background thread automatically
    from app.agents.telegram_bot import run_polling_bot
    import threading
    threading.Thread(target=run_polling_bot, daemon=True).start()



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


@app.get("/api/strategies")
def get_strategies():
    return JSONResponse(db.stats_by_strategy())


@app.post("/api/strategies/{name}/validate")
def validate_strategy(name: str):
    from app.engine.strategies.orb import OpeningRangeBreakout
    from app.engine.strategies.pdh_pdl import PdhPdlStrategy
    from app.engine.strategies.donchian import DonchianTurtle
    from app.engine.strategies.rsi_connors import RsiConnors
    from app.engine.strategies.vwap import VwapReversion
    from app.engine.strategies.gap_fade import GapFade
    from app.engine.strategy import RaynerTeoPullback
    from app.engine.feed import MockIntradayFeed
    from app.validation.gauntlet import validate

    # Resolve strategy class instance
    strat = None
    if name == "opening_range_breakout":
        strat = OpeningRangeBreakout()
    elif name == "pdh_pdl_breakout":
        strat = PdhPdlStrategy(mode="breakout")
    elif name == "pdh_pdl_reversal":
        strat = PdhPdlStrategy(mode="reversal")
    elif name == "donchian_turtle":
        strat = DonchianTurtle()
    elif name == "rsi_connors":
        strat = RsiConnors(trend_period=50)
    elif name == "vwap_reversion":
        strat = VwapReversion()
    elif name == "gap_fade":
        strat = GapFade(gap_pct=0.005)
    elif name == "rayner_teo_pullback":
        strat = RaynerTeoPullback()

    if not strat:
        return JSONResponse({"ok": False, "error": f"Strategy {name} not found"}, status_code=400)

    # Run the validation gauntlet over mock intraday feed
    feed = MockIntradayFeed(n_days=10, seed=42)
    symbols = ["AMC", "BBAI", "SOFI", "PLTR", "RIOT", "MARA"]

    try:
        report = validate(strat, feed, symbols, warmup=55)
        return JSONResponse({"ok": True, "report": report})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


@app.post("/api/analyze")
def analyze_ticker(request: AnalyzeRequest):
    from app.agents.technical import TechnicalAgent
    
    agent = TechnicalAgent()
    result = agent.run({"ticker": request.ticker})
    
    if "error" in result:
        return JSONResponse(result, status_code=400)
    return JSONResponse(result)


@app.post("/api/orchestrate")
def orchestrate_analysis(request: OrchestrateRequest):
    from app.orchestrator.graph import get_orchestrator
    
    orchestrator = get_orchestrator()
    result = orchestrator.orchestrate(request.ticker, request.proposed_trade)
    
    if result.get("status") == "error":
        return JSONResponse(result, status_code=500)
    return JSONResponse(result)


@app.get("/api/memories")
def query_memories(query: str, symbol: str = None):
    from app.core.memory import get_vector_store
    
    store = get_vector_store()
    filter_metadata = {}
    if symbol:
        filter_metadata["symbol"] = symbol.upper()
        
    results = store.query(query, filter_metadata=filter_metadata, limit=10)
    return JSONResponse({"ok": True, "results": results})


@app.get("/")
def dashboard():


    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
