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


@app.post("/api/agent/orchestrate")
def agent_orchestrate_trade(request: AnalyzeRequest):
    from app.orchestrator.graph import get_orchestrator
    from app.agents.agent_execution import propose_and_execute_trade
    from app.agents.tools import get_indicators
    from app.agents.risk import RiskAgent
    from app.core import config
    
    symbol = request.ticker.upper()
    
    # 1. Run core orchestrator (Macro -> News -> Technical -> Thesis)
    orchestrator = get_orchestrator()
    state = orchestrator.orchestrate(symbol, proposed_trade=None)
    
    if state.get("status") == "error":
        return JSONResponse(state, status_code=500)
        
    thesis_result = state.get("thesis", {})
    verdict = thesis_result.get("verdict", "neutral").lower()
    
    trade_execution = {"status": "skipped", "message": "Thesis was neutral/skipped. No trade proposed."}
    
    # 2. If thesis recommends trade (buy or sell), construct proposal and audit with RiskAgent
    if verdict in ("buy", "sell"):
        inds_data = get_indicators(symbol)
        if "error" not in inds_data:
            latest_price = inds_data["latest_price"]
            atr = inds_data["indicators"]["atr14"]
            if atr is None or atr <= 0.0:
                atr = latest_price * 0.02
            
            per_share_risk = 2.0 * atr
            qty = round((config.ACCOUNT_SIZE * config.RISK_PCT_PER_TRADE) / per_share_risk, 2)
            
            proposed_trade = {
                "entry": latest_price,
                "stop": latest_price - per_share_risk if verdict == "buy" else latest_price + per_share_risk,
                "qty": qty,
                "side": "long" if verdict == "buy" else "short"
            }
            
            # Audit trade via RiskAgent
            risk_agent = RiskAgent()
            risk_result = risk_agent.run({"symbol": symbol, "proposed_trade": proposed_trade})
            state["risk_analysis"] = risk_result
            
            # Execute trade if approved
            trade_execution = propose_and_execute_trade(symbol, thesis_result, risk_result)
        else:
            trade_execution = {"status": "error", "message": f"Failed to fetch prices for proposal: {inds_data['error']}"}
    else:
        state["risk_analysis"] = {"veto": False, "reason": "No trade proposed."}
        
    state["trade_execution"] = trade_execution
    return JSONResponse(state)


@app.get("/api/agent/positions")
def get_agent_positions():
    from app.agents.tools import get_indicators
    
    trades = db.all_trades(limit=200)
    open_trades = [t for t in trades if t["status"] == "open" and t["strategy"] == "agent_copilot"]
    
    results = []
    for pos in open_trades:
        symbol = pos["symbol"]
        inds_data = get_indicators(symbol)
        
        latest_price = pos["entry_price"]
        pnl_pct = 0.0
        
        if "error" not in inds_data:
            latest_price = inds_data["latest_price"]
            entry = pos["entry_price"]
            if pos["side"] == "long":
                pnl_pct = ((latest_price - entry) / entry) * 100
            else:
                pnl_pct = ((entry - latest_price) / entry) * 100
                
        results.append({
            "id": pos["id"],
            "strategy": pos["strategy"],
            "symbol": symbol,
            "side": pos["side"],
            "qty": pos["qty"],
            "entry_price": pos["entry_price"],
            "latest_price": round(latest_price, 2),
            "pnl_pct": round(pnl_pct, 2),
            "stop_price": pos["stop_price"],
            "target_price": pos["target_price"],
            "entry_time": pos["entry_time"]
        })
        
    return JSONResponse(results)


@app.post("/api/agent/positions/{id}/close")
def close_agent_position(id: int):
    from app.agents.tools import get_indicators
    
    trades = db.all_trades(limit=200)
    pos = None
    for t in trades:
        if t["id"] == id and t["status"] == "open":
            pos = t
            break
            
    if not pos:
        return JSONResponse({"ok": False, "error": f"Open position with ID {id} not found"}, status_code=400)
        
    symbol = pos["symbol"]
    inds_data = get_indicators(symbol)
    if "error" in inds_data:
        return JSONResponse({"ok": False, "error": f"Failed to get current price for closing: {inds_data['error']}"}, status_code=500)
        
    exit_px = inds_data["latest_price"]
    exit_time = inds_data["time"]
    
    # Calculate P&L
    entry = pos["entry_price"]
    qty = pos["qty"]
    
    if pos["side"] == "long":
        pnl = (exit_px - entry) * qty
    else:
        pnl = (entry - exit_px) * qty
        
    # Calculate R-multiple
    risk_per_share = abs(entry - pos["stop_price"])
    pnl_r = pnl / (risk_per_share * qty) if risk_per_share > 0 else 0.0
    
    db.close_trade(id, exit_time, round(exit_px, 2), round(pnl, 2), round(pnl_r, 3), "manual_exit")
    
    return JSONResponse({"ok": True, "message": f"Closed position {symbol} at ${round(exit_px, 2)} with P&L of ${round(pnl, 2)}"})


@app.get("/")
def dashboard():


    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
