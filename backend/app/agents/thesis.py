import json
from app.agents.base import Agent
from app.agents.llm import get_llm_client
from app.core.memory import get_vector_store

class ThesisAgent(Agent):
    name = "thesis"

    def run(self, context: dict) -> dict:
        symbol = context.get("symbol") or context.get("ticker")
        if not symbol:
            return {"error": "No symbol or ticker provided in context."}
            
        symbol = symbol.upper()
        
        # Pull inputs from context (synthesized by other agents in orchestrator)
        tech_analysis = context.get("technical_analysis", {})
        news_analysis = context.get("news_analysis", {})
        macro_analysis = context.get("macro_analysis", {})
        
        prompt = f"""
Create a unified Investment Thesis for symbol {symbol}:

1. Technical Analyst view:
- Outlook: {tech_analysis.get('conclusion')}
- Evidence: {json.dumps(tech_analysis.get('evidence'))}

2. News Catalyst Analyst view:
- Sentiment Score: {news_analysis.get('sentiment_score')}
- Synthesis: {news_analysis.get('explanation')}

3. Macro Regime Analyst view:
- Market Regime: {macro_analysis.get('market_regime')}
- Bias: {macro_analysis.get('regime_bias')}

Synthesize these views into a cohesive, explainable investment thesis. Detail the core catalyst, key entry/exit rationale, and main risk factors.

You MUST respond with a JSON object containing:
- "verdict": "buy", "sell", or "neutral".
- "core_thesis": A detailed paragraph summarizing the unified thesis.
- "catalysts": A list of key positive drivers.
- "risks": A list of key risk factors.
- "target_duration": "short_term" (days) or "medium_term" (weeks/months).
"""
        
        system_instruction = (
            "You are a Senior Investment Officer. Synthesize technical, news, and macro perspectives "
            "into a single, cohesive investment thesis. Be rigorous, objective, and clearly state risk factors. "
            "Return a valid JSON object matching the requested schema."
        )
        
        # Call LLM
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
            result["symbol"] = symbol
            
            # Save the final thesis to the Vector Store for memory/audit tracking
            vector_store = get_vector_store()
            vector_store.add_record(
                text=result["core_thesis"],
                metadata={
                    "symbol": symbol,
                    "verdict": result["verdict"],
                    "record_type": "investment_thesis",
                    "technical_outlook": tech_analysis.get('conclusion'),
                    "news_sentiment": news_analysis.get('sentiment_score'),
                    "macro_regime": macro_analysis.get('market_regime')
                }
            )
            
            result["inputs_used"] = {
                "technical_conclusion": tech_analysis.get('conclusion'),
                "news_sentiment": news_analysis.get('sentiment_score'),
                "macro_regime": macro_analysis.get('market_regime')
            }
            return result
        except Exception as e:
            return {
                "error": f"Failed to parse thesis agent response: {str(e)}",
                "raw_response": response_str
            }


class ReflectionAgent(Agent):
    name = "reflection"

    def run(self, context: dict) -> dict:
        symbol = context.get("symbol") or context.get("ticker")
        trade_details = context.get("trade_details", {})
        
        if not symbol:
            return {"error": "No symbol or ticker provided in context."}
            
        symbol = symbol.upper()
        
        # 1. Retrieve the historical investment thesis from the Vector Store
        vector_store = get_vector_store()
        memories = vector_store.query(
            text=f"Investment thesis for {symbol}",
            filter_metadata={"symbol": symbol, "record_type": "investment_thesis"},
            limit=1
        )
        
        historical_thesis = "No historical thesis found in memory store."
        if memories:
            historical_thesis = memories[0]["text"]
            
        # 2. Formulate LLM prompt to grade the thesis assumptions against the trade outcome
        prompt = f"""
Reflect on the investment thesis for symbol {symbol}:

Historical Thesis:
"{historical_thesis}"

Actual Trade Outcome:
- P&L: ${trade_details.get('pnl')} ({trade_details.get('pnl_r')} R)
- Entry Time: {trade_details.get('entry_time')}
- Exit Time: {trade_details.get('exit_time')}
- Exit Reason: {trade_details.get('exit_reason')}

Evaluate:
1. Did the thesis assumptions hold true?
2. What did we get right and what did we get wrong?
3. What is the final learning/grade for this trade?

You MUST respond with a JSON object containing:
- "grade": "A", "B", "C", "D", or "F" based on assumption accuracy (not just profit).
- "learnings": A list of key takeaways / lessons learned.
- "thesis_accuracy": "accurate", "partially_accurate", or "inaccurate".
- "explanation": A detailed reflection explaining the grade.
"""
        
        system_instruction = (
            "You are a Post-Mortem Reflection Officer. Grade past predictions and investment theses "
            "against actual market trade outcomes. Be honest, self-critical, and detail lessons learned. "
            "Return a valid JSON object matching the requested schema."
        )
        
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
            result["symbol"] = symbol
            
            # Save reflection record to memory store for learning history
            vector_store.add_record(
                text=result["explanation"],
                metadata={
                    "symbol": symbol,
                    "record_type": "post_mortem_reflection",
                    "grade": result["grade"],
                    "pnl": trade_details.get('pnl')
                }
            )
            
            result["inputs_used"] = {
                "historical_thesis_found": bool(memories),
                "pnl": trade_details.get('pnl'),
                "exit_reason": trade_details.get('exit_reason')
            }
            return result
        except Exception as e:
            return {
                "error": f"Failed to parse reflection agent response: {str(e)}",
                "raw_response": response_str
            }
