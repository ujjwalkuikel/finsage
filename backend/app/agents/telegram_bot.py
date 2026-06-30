import time
import httpx
import logging
from app.core import config
from app.agents.technical import TechnicalAgent

logger = logging.getLogger("uvicorn")

def format_analysis_markdown(result: dict) -> str:
    symbol = result.get("symbol", "UNKNOWN")
    price = result.get("latest_price", "N/A")
    time_str = result.get("time", "N/A")
    conclusion = result.get("conclusion", "neutral").upper()
    
    emoji = "🐂" if "BULL" in conclusion else "🐻" if "BEAR" in conclusion else "⚖️"
    
    lines = [
        f"📊 *Technical Analysis for {symbol}*",
        f"💰 *Latest Price:* ${price} (as of {time_str})",
        f"🎯 *Outlook:* {emoji} *{conclusion}*",
        "",
        "*Evidence:*",
    ]
    
    for ev in result.get("evidence", []):
        lines.append(f"• {ev}")
        
    lines.append("")
    lines.append("*Inputs Relied Upon:*")
    
    inputs = result.get("inputs_used", {})
    for k, v in inputs.items():
        key_name = k.replace("_", " ").title()
        if isinstance(v, dict):
            lines.append(f"  _{key_name}_:")
            for sub_k, sub_v in v.items():
                sub_key = sub_k.replace("_", " ").title()
                lines.append(f"    • {sub_key}: `{sub_v}`")
        else:
            lines.append(f"  • {key_name}: `{v}`")
            
    return "\n".join(lines)

def run_polling_bot():
    token = config.TELEGRAM_BOT_TOKEN
    if not token:
        logger.error("Error: TELEGRAM_BOT_TOKEN is not set in environment.")
        return
        
    base_url = f"https://api.telegram.org/bot{token}"
    logger.info("Starting Telegram bot polling loop...")
    
    offset = 0
    agent = TechnicalAgent()
    
    # Simple polling loop
    with httpx.Client(timeout=40.0) as client:
        while True:
            try:
                url = f"{base_url}/getUpdates"
                params = {"offset": offset, "timeout": 30}
                response = client.get(url, params=params)
                if response.status_code != 200:
                    logger.error(f"Telegram API returned status {response.status_code}")
                    time.sleep(5)
                    continue
                    
                updates = response.json().get("result", [])
                for update in updates:
                    offset = update["update_id"] + 1
                    message = update.get("message", {})
                    text = message.get("text", "").strip()
                    chat_id = message.get("chat", {}).get("id")
                    
                    if not chat_id or not text:
                        continue
                        
                    logger.info(f"Telegram bot: received message: '{text}' from chat {chat_id}")
                    
                    # Command parsing: expect symbol or /analyze symbol or $symbol
                    symbol = None
                    if text.startswith("/start"):
                        welcome_text = (
                            "👋 Welcome to the FinSage AII Technical Research Assistant!\n\n"
                            "Send me any stock ticker (e.g. `AAPL` or `NVDA`) or use `/analyze AAPL` "
                            "to get a detailed, data-driven technical analysis and backtest report."
                        )
                        client.post(f"{base_url}/sendMessage", json={"chat_id": chat_id, "text": welcome_text})
                        continue
                    elif text.startswith("/analyze "):
                        symbol = text[len("/analyze "):].strip()
                    elif text.startswith("$"):
                        symbol = text[1:].strip()
                    else:
                        # Plain text ticker checks (1-5 alphabetical chars)
                        candidate = text.strip().upper()
                        if candidate.isalpha() and 1 <= len(candidate) <= 5:
                            symbol = candidate
                            
                    if symbol:
                        symbol = symbol.upper()
                        client.post(f"{base_url}/sendMessage", json={
                            "chat_id": chat_id, 
                            "text": f"Analyzing {symbol}... Please wait. 🔍"
                        })
                        
                        try:
                            # Run analysis using TechnicalAgent
                            result = agent.run({"symbol": symbol})
                            if "error" in result:
                                reply = f"❌ Error analyzing {symbol}: {result['error']}"
                            else:
                                reply = format_analysis_markdown(result)
                        except Exception as ex:
                            reply = f"❌ Technical error during analysis: {str(ex)}"
                            
                        # Send result back
                        client.post(f"{base_url}/sendMessage", json={
                            "chat_id": chat_id,
                            "text": reply,
                            "parse_mode": "Markdown"
                        })
                        
            except Exception as e:
                logger.error(f"Telegram bot polling loop exception: {str(e)}")
                time.sleep(5)

if __name__ == "__main__":
    run_polling_bot()
