import json
import httpx
import datetime as dt
from app.agents.base import Agent
from app.agents.llm import get_llm_client
from app.core import config

class NewsAgent(Agent):
    name = "news"

    def run(self, context: dict) -> dict:
        symbol = context.get("symbol") or context.get("ticker")
        if not symbol:
            return {"error": "No symbol or ticker provided in context."}
            
        symbol = symbol.upper()
        
        # 1. Gather news headlines
        headlines = self._fetch_news(symbol)
        
        if not headlines:
            return {
                "symbol": symbol,
                "sentiment_score": 0.0,
                "catalysts": [],
                "inputs_used": {"news_count": 0},
                "explanation": "No recent news headlines found for analysis."
            }
            
        # 2. Compile headlines for LLM prompt
        news_text = "\n".join([f"- {h['headline']} (Source: {h['source']})" for h in headlines[:10]])
        
        prompt = f"""
Analyze the recent news headlines for symbol {symbol}:

{news_text}

Classify each news item's impact as positive, negative, or neutral.
Calculate an overall sentiment score for the stock between -1.0 (extremely bearish) and +1.0 (extremely bullish).

You MUST respond with a JSON object containing:
- "sentiment_score": A float between -1.0 and 1.0.
- "catalysts": A list of dicts, each with:
    - "headline": The original headline.
    - "impact": "positive", "negative", or "neutral".
    - "explanation": Brief reason for classification.
- "explanation": A paragraph synthesizing the overall news picture for this stock.
"""
        
        system_instruction = (
            "You are a News Catalyst Analyst. Analyze news headlines, classify their market impact, "
            "and compute a sentiment score. Do not inject opinions not supported by the headlines. "
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
            # Clean markdown formatting if present
            cleaned = response_str.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            
            result = json.loads(cleaned)
            result["symbol"] = symbol
            result["inputs_used"] = {
                "news_count": len(headlines[:10]),
                "headlines": [h["headline"] for h in headlines[:10]]
            }
            return result
        except Exception as e:
            return {
                "error": f"Failed to parse news agent response: {str(e)}",
                "raw_response": response_str
            }

    def _fetch_news(self, symbol: str) -> list[dict]:
        """Fetches news from Finnhub, falling back to mock news in dev mode."""
        if config.FINNHUB_KEY:
            try:
                today = dt.date.today().isoformat()
                week_ago = (dt.date.today() - dt.timedelta(days=7)).isoformat()
                url = f"https://finnhub.io/api/v1/company-news"
                params = {
                    "symbol": symbol,
                    "from": week_ago,
                    "to": today,
                    "token": config.FINNHUB_KEY
                }
                response = httpx.get(url, params=params, timeout=15.0)
                if response.status_code == 200:
                    news_data = response.json()
                    return [{"headline": item.get("headline"), "source": item.get("source", "Finnhub")} for item in news_data]
            except Exception as e:
                print(f"Finnhub news fetch failed: {str(e)}. Falling back to mock news.")
                
        # Mock headlines for testing/dev
        return [
            {"headline": f"{symbol} shares surge as quarterly revenue beats analyst estimates.", "source": "MarketWatch"},
            {"headline": f"Analysts upgrade {symbol} to Buy, citing strong product demand and high margins.", "source": "Reuters"},
            {"headline": f"Competitor launches new rival product, putting pressure on {symbol}'s market share.", "source": "Bloomberg"},
            {"headline": f"Industry regulatory shift could create headwind for sector players including {symbol}.", "source": "WSJ"},
        ]
