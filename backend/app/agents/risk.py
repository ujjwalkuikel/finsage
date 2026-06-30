import json
from app.agents.base import Agent
from app.agents.llm import get_llm_client
from app.core import config
from app.engine import db

class RiskAgent(Agent):
    name = "risk"

    def run(self, context: dict) -> dict:
        symbol = context.get("symbol") or context.get("ticker")
        proposed_trade = context.get("proposed_trade")
        
        # Risk assessment parameters from deterministic config
        account_size = config.ACCOUNT_SIZE
        risk_pct_limit = config.RISK_PCT_PER_TRADE
        daily_max_loss_limit = config.DAILY_MAX_LOSS_PCT
        
        # Pull ledger stats for concentration checks
        trades = db.all_trades(limit=100)
        open_trades = [t for t in trades if t["status"] == "open"]
        total_open = len(open_trades)
        
        symbol_open_count = sum(1 for t in open_trades if t["symbol"] == symbol)
        symbol_concentration = (symbol_open_count / total_open) if total_open > 0 else 0.0
        
        # 1. Deterministic calculation: check proposed trade risk
        veto = False
        reason = "Trade complies with all deterministic risk thresholds."
        adjusted_qty = None
        
        if proposed_trade:
            entry = float(proposed_trade.get("entry", 0.0))
            stop = float(proposed_trade.get("stop", 0.0))
            qty = float(proposed_trade.get("qty", 0.0))
            side = proposed_trade.get("side", "long")
            
            # Risk per share
            risk_per_share = abs(entry - stop)
            total_trade_risk = risk_per_share * qty
            max_allowed_risk = account_size * risk_pct_limit
            
            if total_trade_risk > max_allowed_risk:
                veto = True
                # Calculate maximum allowed quantity to stay inside 1% risk
                if risk_per_share > 0:
                    adjusted_qty = round(max_allowed_risk / risk_per_share, 2)
                reason = f"VETO: Proposed trade risk (${round(total_trade_risk, 2)}) exceeds the maximum allowed 1% account risk (${round(max_allowed_risk, 2)})."
            
            # Concentration check: Veto if we have too many positions in one symbol
            elif symbol_concentration >= 0.25:
                veto = True
                reason = f"VETO: Concentration limit breached. Ticker {symbol} represents {round(symbol_concentration * 100, 1)}% of open portfolio positions (limit 25%)."

        # 2. Compile metrics for LLM verification (explainability check)
        prompt = f"""
Evaluate the proposed trade for symbol {symbol}:
- Proposed Trade: {json.dumps(proposed_trade)}
- Account Size: ${account_size}
- Risk Limit Per Trade: {risk_pct_limit * 100}% (${account_size * risk_pct_limit})
- Current Portfolio Concentration for {symbol}: {round(symbol_concentration * 100, 1)}%

Review the risk team's verdict:
- Deterministic Veto: {veto}
- Reason: {reason}
- Suggested Adjusted Qty: {adjusted_qty}

Explain the portfolio safety implications of this verdict.

You MUST respond with a JSON object containing:
- "veto": true or false.
- "reason": A detailed explanation of why the trade was vetoed or approved.
- "adjusted_qty": A float or null indicating the maximum safe size.
- "risk_metrics": {{
      "total_trade_risk": {total_trade_risk if proposed_trade else 0.0},
      "max_allowed_risk": {account_size * risk_pct_limit},
      "concentration": {symbol_concentration}
  }}
"""
        
        system_instruction = (
            "You are a Risk Officer. Enforce strict risk limits and evaluate portfolio concentration. "
            "You can veto trades or suggest lower sizes, but you can NEVER relax risk limits. "
            "Return a valid JSON object matching the requested schema."
        )
        
        # 3. Call LLM for final write-up and verification
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
            # Enforce deterministic veto regardless of LLM suggestion for safety
            if veto:
                result["veto"] = True
                result["reason"] = f"{reason} | LLM Note: {result.get('reason', '')}"
                if adjusted_qty is not None:
                    result["adjusted_qty"] = adjusted_qty
            
            result["inputs_used"] = {
                "account_size": account_size,
                "risk_pct_limit": risk_pct_limit,
                "symbol_concentration": symbol_concentration,
                "total_open_positions": total_open
            }
            return result
        except Exception as e:
            return {
                "error": f"Failed to parse risk agent response: {str(e)}",
                "raw_response": response_str
            }
