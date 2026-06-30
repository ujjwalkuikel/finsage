import json
from app.agents.base import Agent
from app.agents.llm import get_llm_client

class MacroAgent(Agent):
    name = "macro"

    def run(self, context: dict) -> dict:
        # 1. Gather macro indicators (defaulting to standard market indicators in dev)
        macro_data = self._gather_macro_indicators()
        
        prompt = f"""
Analyze the current macroeconomic indicators:

- S&P 500 relative to 200-day SMA: {macro_data['spy_above_200sma']}
- VIX Level: {macro_data['vix_level']}
- US 10Y-2Y Treasury Yield Spread: {macro_data['yield_spread']}%
- Inflation Rate (CPI YoY): {macro_data['cpi_yoy']}%
- Federal Funds Rate: {macro_data['fed_funds_rate']}%

Evaluate the current market regime. Is it bull trending, bear trending, mean reverting in a range, or highly volatile?

You MUST respond with a JSON object containing:
- "market_regime": "bull_trending", "bear_trending", "mean_reverting_range", or "high_volatility".
- "vix_status": "low" (VIX < 15), "normal" (15 <= VIX <= 25), or "fear" (VIX > 25).
- "rate_regime": A brief summary of the interest rate stance (e.g. "rising rates", "pause", "cutting").
- "evidence": A list of strings justifying the regime classification.
- "regime_bias": "risk_on", "risk_off", or "defensive_income".
"""
        
        system_instruction = (
            "You are a Macro Regime Analyst. Classify interest rate regimes, market volatility, "
            "and overall market trend bias. Be objective and avoid emotional predictions. "
            "Return a valid JSON object matching the requested schema."
        )
        
        # 2. Call LLM
        client = get_llm_client()
        response_str = client.generate(
            prompt=prompt,
            json_mode=True,
            system_instruction=system_instruction
        )
        
        try:
            cleaned = response_str.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            
            result = json.loads(cleaned)
            result["inputs_used"] = macro_data
            return result
        except Exception as e:
            return {
                "error": f"Failed to parse macro agent response: {str(e)}",
                "raw_response": response_str
            }

    def _gather_macro_indicators(self) -> dict:
        """Gathers standard macro indicators (can pull from Fred/Yahoo later)."""
        return {
            "spy_above_200sma": "above",  # bull market regime
            "vix_level": 15.8,            # moderate volatility
            "yield_spread": 0.05,         # slightly flat yield curve
            "cpi_yoy": 3.1,               # stable to slightly elevated cpi
            "fed_funds_rate": 5.25        # high rates pause
        }
