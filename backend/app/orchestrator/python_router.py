from app.orchestrator.base import BaseOrchestrator
from app.agents.technical import TechnicalAgent
from app.agents.news import NewsAgent
from app.agents.macro import MacroAgent
from app.agents.thesis import ThesisAgent
from app.agents.risk import RiskAgent

class PythonOrchestrator(BaseOrchestrator):
    """
    A pure-Python sequential state orchestrator.
    Executes the multi-agent graph in a deterministic path without third-party frameworks.
    """
    def orchestrate(self, symbol: str, proposed_trade: dict = None) -> dict:
        symbol = symbol.upper()
        state = {
            "symbol": symbol,
            "proposed_trade": proposed_trade,
            "technical_analysis": {},
            "news_analysis": {},
            "macro_analysis": {},
            "thesis": {},
            "risk_analysis": {},
            "status": "success"
        }

        # 1. Technical Agent Node
        try:
            tech_agent = TechnicalAgent()
            state["technical_analysis"] = tech_agent.run({"symbol": symbol})
            if "error" in state["technical_analysis"]:
                state["status"] = "error"
                state["error"] = f"TechnicalAgent failed: {state['technical_analysis']['error']}"
                return state
        except Exception as e:
            state["status"] = "error"
            state["error"] = f"TechnicalAgent exception: {str(e)}"
            return state

        # 2. News Agent Node
        try:
            news_agent = NewsAgent()
            state["news_analysis"] = news_agent.run({"symbol": symbol})
        except Exception as e:
            state["news_analysis"] = {"error": str(e)}

        # 3. Macro Agent Node
        try:
            macro_agent = MacroAgent()
            state["macro_analysis"] = macro_agent.run({"symbol": symbol})
        except Exception as e:
            state["macro_analysis"] = {"error": str(e)}

        # 4. Thesis Agent Node (Synthesizer)
        try:
            thesis_agent = ThesisAgent()
            thesis_context = {
                "symbol": symbol,
                "technical_analysis": state["technical_analysis"],
                "news_analysis": state["news_analysis"],
                "macro_analysis": state["macro_analysis"]
            }
            state["thesis"] = thesis_agent.run(thesis_context)
        except Exception as e:
            state["thesis"] = {"error": str(e)}

        # 5. Risk Agent Node (Veto check)
        if proposed_trade:
            try:
                risk_agent = RiskAgent()
                risk_context = {
                    "symbol": symbol,
                    "proposed_trade": proposed_trade
                }
                state["risk_analysis"] = risk_agent.run(risk_context)
            except Exception as e:
                state["risk_analysis"] = {"error": str(e), "veto": True, "reason": "Risk analysis execution failed."}
        else:
            state["risk_analysis"] = {
                "veto": False,
                "reason": "No proposed trade provided for risk assessment."
            }

        return state
