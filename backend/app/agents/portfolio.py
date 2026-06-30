import json
from app.agents.base import Agent
from app.agents.llm import get_llm_client
from app.engine import db

class PortfolioAgent(Agent):
    name = "portfolio"

    def run(self, context: dict) -> dict:
        # 1. Fetch trade ledger stats
        trades = db.all_trades(limit=200)
        open_trades = [t for t in trades if t["status"] == "open"]
        
        # Calculate concentrations
        symbol_counts = {}
        strategy_counts = {}
        for t in open_trades:
            symbol_counts[t["symbol"]] = symbol_counts.get(t["symbol"], 0) + 1
            strategy_counts[t["strategy"]] = strategy_counts.get(t["strategy"], 0) + 1
            
        total_open = len(open_trades)
        symbol_pct = {k: round(v / total_open if total_open > 0 else 0, 2) for k, v in symbol_counts.items()}
        strategy_pct = {k: round(v / total_open if total_open > 0 else 0, 2) for k, v in strategy_counts.items()}
        
        # 2. Construct LLM prompt
        prompt = f"""
Analyze the current portfolio concentration and exposures:

Total Open Positions: {total_open}
Position Exposure by Symbol:
{json.dumps(symbol_pct, indent=2)}

Position Exposure by Strategy:
{json.dumps(strategy_pct, indent=2)}

Please evaluate:
1. Concentration risk: is it low, medium, or high?
2. Recommendations: do we need to rebalance, pause any strategies, or limit further positions in specific symbols?

You MUST respond with a JSON object containing:
- "concentration_risk": "low", "medium", or "high".
- "exposures": {{
     "symbol_exposures": {json.dumps(symbol_pct)},
     "strategy_exposures": {json.dumps(strategy_pct)}
  }}
- "evidence": A list of strings explaining your assessment.
- "recommendations": A list of specific actionable recommendations.
"""
        
        system_instruction = (
            "You are a Portfolio Manager. Analyze position concentrations, exposure limits, "
            "and suggest rebalancing actions. Remain objective, quantitative, and data-driven. "
            "Return a valid JSON object matching the requested schema."
        )
        
        # 3. Call LLM
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
            result["inputs_used"] = {
                "total_open_positions": total_open,
                "symbol_counts": symbol_counts,
                "strategy_counts": strategy_counts
            }
            return result
        except Exception as e:
            return {
                "error": f"Failed to parse portfolio agent response: {str(e)}",
                "raw_response": response_str
            }
