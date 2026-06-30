import datetime as dt
from app.core import config
from app.data.polygon_feed import PolygonFeed
from app.engine.strategy import sma
from app.engine.strategies.rsi_connors import compute_rsi
from app.engine.strategies.donchian import compute_atr

def get_indicators(symbol: str) -> dict:
    """
    Exposes deterministic technical indicators for a given symbol.
    Fetches daily bars for the past year to compute SMA, RSI, ATR, and performance.
    """
    if not config.POLYGON_API_KEY:
        return {"error": "POLYGON_API_KEY is not configured in .env"}

    # To calculate 200 SMA, we need at least 200 trading days (~300 calendar days)
    today = dt.date.today()
    from_date = (today - dt.timedelta(days=365)).isoformat()
    
    feed = PolygonFeed(
        api_key=config.POLYGON_API_KEY,
        timespan="day",
        multiplier=1,
        from_date=from_date,
        to_date=today.isoformat()
    )
    
    try:
        bars = list(feed.bars(symbol))
    except Exception as e:
        return {"error": f"Failed to fetch data for symbol {symbol}: {str(e)}"}
        
    if not bars:
        return {"error": f"No data found for symbol {symbol}"}
        
    # Compute indicators
    closes = [b.close for b in bars]
    volumes = [b.volume for b in bars]
    
    sma20 = sma(closes, 20)
    sma50 = sma(closes, 50)
    sma200 = sma(closes, 200)
    
    rsi2 = compute_rsi(bars, 2)
    rsi14 = compute_rsi(bars, 14)
    atr14 = compute_atr(bars, 14)
    avg_volume = sma(volumes, 20)
    
    latest_close = closes[-1]
    prev_close = closes[-2] if len(closes) > 1 else latest_close
    perf_1d = (latest_close - prev_close) / prev_close if prev_close > 0 else 0.0
    
    close_5d = closes[-5] if len(closes) > 4 else closes[0]
    perf_5d = (latest_close - close_5d) / close_5d if close_5d > 0 else 0.0
    
    close_20d = closes[-20] if len(closes) > 19 else closes[0]
    perf_20d = (latest_close - close_20d) / close_20d if close_20d > 0 else 0.0
    
    return {
        "symbol": symbol,
        "latest_price": round(latest_close, 3),
        "time": bars[-1].time,
        "indicators": {
            "sma20": round(sma20, 3) if sma20 is not None else None,
            "sma50": round(sma50, 3) if sma50 is not None else None,
            "sma200": round(sma200, 3) if sma200 is not None else None,
            "rsi2": round(rsi2, 3) if rsi2 is not None else None,
            "rsi14": round(rsi14, 3) if rsi14 is not None else None,
            "atr14": round(atr14, 3) if atr14 is not None else None,
            "avg_volume_20d": round(avg_volume, 0) if avg_volume is not None else None,
        },
        "performance": {
            "perf_1d_pct": round(perf_1d * 100, 2),
            "perf_5d_pct": round(perf_5d * 100, 2),
            "perf_20d_pct": round(perf_20d * 100, 2),
        }
    }

def run_backtest(strategy_name: str, symbol: str) -> dict:
    """
    Runs a deterministic strategy backtest for a symbol over daily history.
    """
    if not config.POLYGON_API_KEY:
        return {"error": "POLYGON_API_KEY is not configured in .env"}

    # Resolve strategy instance
    from app.engine.strategies.orb import OpeningRangeBreakout
    from app.engine.strategies.pdh_pdl import PdhPdlStrategy
    from app.engine.strategies.donchian import DonchianTurtle
    from app.engine.strategies.rsi_connors import RsiConnors
    from app.engine.strategies.vwap import VwapReversion
    from app.engine.strategies.gap_fade import GapFade
    from app.engine.strategy import RaynerTeoPullback
    from app.validation.gauntlet import backtest
    
    today = dt.date.today()
    from_date = (today - dt.timedelta(days=365)).isoformat()
    
    feed = PolygonFeed(
        api_key=config.POLYGON_API_KEY,
        timespan="day",
        multiplier=1,
        from_date=from_date,
        to_date=today.isoformat()
    )
    
    try:
        bars = list(feed.bars(symbol))
    except Exception as e:
        return {"error": f"Failed to fetch data for symbol {symbol}: {str(e)}"}
        
    if not bars:
        return {"error": f"No data found for symbol {symbol}"}
        
    strat = None
    if strategy_name == "rayner_teo_pullback":
        strat = RaynerTeoPullback()
    elif strategy_name == "opening_range_breakout":
        strat = OpeningRangeBreakout()
    elif strategy_name == "pdh_pdl_breakout":
        strat = PdhPdlStrategy(mode="breakout")
    elif strategy_name == "pdh_pdl_reversal":
        strat = PdhPdlStrategy(mode="reversal")
    elif strategy_name == "donchian_turtle":
        strat = DonchianTurtle()
    elif strategy_name == "rsi_connors":
        strat = RsiConnors(trend_period=50)
    elif strategy_name == "vwap_reversion":
        strat = VwapReversion()
    elif strategy_name == "gap_fade":
        strat = GapFade(gap_pct=0.005)
        
    if not strat:
        return {"error": f"Strategy {strategy_name} not found"}
        
    try:
        result = backtest(strat, bars)
        return {
            "strategy": strategy_name,
            "symbol": symbol,
            "stats": result["stats"],
            "total_trades": len(result["trades"]),
        }
    except Exception as e:
        return {"error": f"Backtest failed: {str(e)}"}
