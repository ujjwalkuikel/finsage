import json
from app.agents.base import Agent
from app.agents.llm import call_llm
from app.agents.tools import get_indicators, run_backtest

class TechnicalAgent(Agent):
    name = "technical"

    def run(self, context: dict) -> dict:
        symbol = context.get("symbol") or context.get("ticker")
        if not symbol:
            return {"error": "No symbol or ticker provided in context."}
            
        symbol = symbol.upper()
        
        # 1. Fetch indicators from deterministic engine
        data = get_indicators(symbol)

        if "error" in data:
            return data
            
        # 2. Run backtests from deterministic engine
        bt_rayner = run_backtest("rayner_teo_pullback", symbol)
        bt_rsi = run_backtest("rsi_connors", symbol)
        
        # Safe extraction of backtest stats
        stats_rayner = bt_rayner.get("stats", {}) if "error" not in bt_rayner else {}
        stats_rsi = bt_rsi.get("stats", {}) if "error" not in bt_rsi else {}
        
        # 3. Formulate the prompt
        inds = data["indicators"]
        perf = data["performance"]
        
        prompt = f"""
Analyze the technical data for symbol: {symbol}.

Latest Price: ${data['latest_price']} (as of {data['time']})
Performance:
- 1-Day: {perf['perf_1d_pct']}%
- 5-Day: {perf['perf_5d_pct']}%
- 20-Day: {perf['perf_20d_pct']}%

Technical Indicators:
- SMA 20: {inds['sma20']}
- SMA 50: {inds['sma50']}
- SMA 200: {inds['sma200']}
- RSI (2): {inds['rsi2']}
- RSI (14): {inds['rsi14']}
- ATR (14): {inds['atr14']}
- 20-Day Average Volume: {inds['avg_volume_20d']}

Strategy Backtest Results (last 1 year of daily history):
1. Rayner-Teo Pullback:
- Total Trades: {bt_rayner.get('total_trades', 0)}
- Win Rate: {stats_rayner.get('win_rate', 0.0)}%
- Expectancy: {stats_rayner.get('expectancy_r', 0.0)} R per trade
- Profit Factor: {stats_rayner.get('profit_factor', 0.0)}
- Max Drawdown: {stats_rayner.get('max_dd', 0.0)}

2. RSI(2) Connors Mean Reversion:
- Total Trades: {bt_rsi.get('total_trades', 0)}
- Win Rate: {stats_rsi.get('win_rate', 0.0)}%
- Expectancy: {stats_rsi.get('expectancy_r', 0.0)} R per trade
- Profit Factor: {stats_rsi.get('profit_factor', 0.0)}
- Max Drawdown: {stats_rsi.get('max_dd', 0.0)}

Based on the above deterministic technical indicators and backtest results, provide your analysis.

You MUST respond with a JSON object containing:
- "conclusion": A string ("bullish", "bearish", or "neutral") summarizing the overall technical outlook.
- "evidence": A list of strings, where each string is a specific evidence statement explaining your conclusion, referencing the SMA alignment, RSI levels, performance, or strategy backtests.
- "inputs_used": A dictionary containing all the input metrics you actually referenced or relied on for your analysis. Do not include metrics you did not use.
"""
        
        system_instruction = (
            "You are a Senior Technical Analyst. Your job is to interpret technical indicators and backtest results "
            "for a ticker. You must be objective, factual, and strictly data-driven. Do not invent any values or write "
            "vague prose. Every statement in your evidence must refer to the provided numbers. Your response MUST "
            "be a valid JSON object matching the requested schema."
        )
        
        # 4. Call LLM
        response_str = call_llm(
            prompt=prompt,
            json_mode=True,
            system_instruction=system_instruction
        )
        
        # 5. Parse and return response
        try:
            # Strip markdown block formatting if LLM includes it
            cleaned_response = response_str.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            result = json.loads(cleaned_response)
            
            # Inject symbol and metadata
            result["symbol"] = symbol
            result["latest_price"] = data["latest_price"]
            result["time"] = data["time"]
            
            return result
        except Exception as e:
            return {
                "error": f"Failed to parse LLM response: {str(e)}",
                "raw_response": response_str
            }
