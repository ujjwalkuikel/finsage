import datetime as dt
from app.core import config
from app.engine import db
from app.agents.tools import get_indicators

def propose_and_execute_trade(symbol: str, thesis_result: dict, risk_result: dict) -> dict:
    """
    Evaluates agent thesis and risk officer veto.
    If approved, calculates ATR-based stop/target and sizing, and inserts the trade in the ledger.
    """
    symbol = symbol.upper()
    verdict = thesis_result.get("verdict", "neutral").lower()
    veto = risk_result.get("veto", False)
    
    if verdict not in ("buy", "sell"):
        return {"status": "skipped", "message": f"Thesis verdict was '{verdict}'. Skipping trade execution."}
        
    if veto:
        return {"status": "vetoed", "message": f"Risk officer vetoed trade: {risk_result.get('reason')}"}
        
    # Check if we already have an open position in this symbol
    trades = db.all_trades(limit=100)
    open_trades = [t for t in trades if t["symbol"] == symbol and t["status"] == "open"]
    if open_trades:
        return {"status": "skipped", "message": f"A position in {symbol} is already open. Skipping execution."}
        
    # Fetch indicators to get latest price and ATR(14)
    inds_data = get_indicators(symbol)
    if "error" in inds_data:
        return {"status": "error", "message": f"Failed to fetch indicators for execution: {inds_data['error']}"}
        
    latest_price = inds_data["latest_price"]
    atr = inds_data["indicators"]["atr14"]
    
    # Safety default for ATR if not calculated (e.g. 2% of price)
    if atr is None or atr <= 0.0:
        atr = latest_price * 0.02
        
    # Sizing and Risk offsets
    entry = latest_price
    side = "long" if verdict == "buy" else "short"
    
    # 2 * ATR risk
    per_share_risk = 2.0 * atr
    
    if side == "long":
        stop = entry - per_share_risk
        target = entry + 2.0 * per_share_risk
    else:
        stop = entry + per_share_risk
        target = entry - 2.0 * per_share_risk
        
    # Determine Qty: use risk officer suggested size or compute standard 1% sizing
    adjusted_qty = risk_result.get("adjusted_qty")
    if adjusted_qty is not None:
        qty = float(adjusted_qty)
    else:
        account_size = config.ACCOUNT_SIZE
        risk_pct_limit = config.RISK_PCT_PER_TRADE
        max_allowed_risk = account_size * risk_pct_limit
        qty = round(max_allowed_risk / per_share_risk, 2)
        
    if qty <= 0.0:
        return {"status": "skipped", "message": "Position sizing resulted in 0 shares. Skipping execution."}
        
    # Insert trade into SQLite ledger
    trade_data = {
        "strategy": "agent_copilot",
        "symbol": symbol,
        "side": side,
        "qty": qty,
        "entry_time": inds_data["time"],
        "entry_price": round(entry, 2),
        "stop_price": round(stop, 2),
        "target_price": round(target, 2)
    }
    
    try:
        trade_id = db.insert_open_trade(trade_data)
        trade_data["id"] = trade_id
        trade_data["status"] = "open"
        return {
            "status": "executed",
            "message": f"SUCCESS: Placed {side.upper()} order for {qty} shares of {symbol} at ${round(entry, 2)}.",
            "trade": trade_data
        }
    except Exception as e:
        return {"status": "error", "message": f"Ledger write failed: {str(e)}"}
