from typing import TypedDict, Optional
from app.orchestrator.base import BaseOrchestrator

try:
    from langgraph.graph import StateGraph, END
    HAS_LANGGRAPH = True
except ImportError:
    HAS_LANGGRAPH = False

# LangGraph State Schema
class OrchestratorState(TypedDict):
    symbol: str
    proposed_trade: Optional[dict]
    technical_analysis: dict
    news_analysis: dict
    macro_analysis: dict
    thesis: dict
    risk_analysis: dict
    status: str
    error: Optional[str]


class LangGraphOrchestrator(BaseOrchestrator):
    """
    LangGraph-based multi-agent orchestrator.
    Builds and compiles a conditional state routing graph using LangGraph.
    Falls back to PythonOrchestrator if the langgraph package is not installed.
    """
    def orchestrate(self, symbol: str, proposed_trade: dict = None) -> dict:
        if not HAS_LANGGRAPH:
            # Fall back to the pure-Python orchestrator if langgraph is not installed
            from app.orchestrator.python_router import PythonOrchestrator
            return PythonOrchestrator().orchestrate(symbol, proposed_trade)

        symbol = symbol.upper()
        
        # 1. Define nodes
        def run_technical_node(state: OrchestratorState) -> dict:
            from app.agents.technical import TechnicalAgent
            try:
                res = TechnicalAgent().run({"symbol": state["symbol"]})
                if "error" in res:
                    return {"technical_analysis": res, "status": "error", "error": res["error"]}
                return {"technical_analysis": res}
            except Exception as e:
                return {"technical_analysis": {"error": str(e)}, "status": "error", "error": str(e)}

        def run_news_node(state: OrchestratorState) -> dict:
            from app.agents.news import NewsAgent
            try:
                res = NewsAgent().run({"symbol": state["symbol"]})
                return {"news_analysis": res}
            except Exception as e:
                return {"news_analysis": {"error": str(e)}}

        def run_macro_node(state: OrchestratorState) -> dict:
            from app.agents.macro import MacroAgent
            try:
                res = MacroAgent().run({"symbol": state["symbol"]})
                return {"macro_analysis": res}
            except Exception as e:
                return {"macro_analysis": {"error": str(e)}}

        def run_thesis_node(state: OrchestratorState) -> dict:
            from app.agents.thesis import ThesisAgent
            try:
                res = ThesisAgent().run({
                    "symbol": state["symbol"],
                    "technical_analysis": state["technical_analysis"],
                    "news_analysis": state["news_analysis"],
                    "macro_analysis": state["macro_analysis"]
                })
                return {"thesis": res}
            except Exception as e:
                return {"thesis": {"error": str(e)}}

        def run_risk_node(state: OrchestratorState) -> dict:
            from app.agents.risk import RiskAgent
            if state["proposed_trade"]:
                try:
                    res = RiskAgent().run({
                        "symbol": state["symbol"],
                        "proposed_trade": state["proposed_trade"]
                    })
                    return {"risk_analysis": res}
                except Exception as e:
                    return {"risk_analysis": {"error": str(e), "veto": True, "reason": "Risk analysis run failed."}}
            else:
                return {"risk_analysis": {"veto": False, "reason": "No proposed trade provided."}}

        # 2. Build graph workflow
        workflow = StateGraph(OrchestratorState)

        workflow.add_node("technical", run_technical_node)
        workflow.add_node("news", run_news_node)
        workflow.add_node("macro", run_macro_node)
        workflow.add_node("thesis", run_thesis_node)
        workflow.add_node("risk", run_risk_node)

        # Start -> Technical -> News -> Macro -> Thesis -> Risk -> End
        workflow.set_entry_point("technical")
        
        # Handle conditional error routing (stop if technical fails)
        def route_technical(state: OrchestratorState) -> str:
            if state.get("status") == "error":
                return END
            return "news"

        workflow.add_conditional_edges(
            "technical",
            route_technical,
            {
                END: END,
                "news": "news"
            }
        )
        
        workflow.add_edge("news", "macro")
        workflow.add_edge("macro", "thesis")
        workflow.add_edge("thesis", "risk")
        workflow.add_edge("risk", END)

        # 3. Compile and Run
        app_graph = workflow.compile()
        initial_state = {
            "symbol": symbol,
            "proposed_trade": proposed_trade,
            "technical_analysis": {},
            "news_analysis": {},
            "macro_analysis": {},
            "thesis": {},
            "risk_analysis": {},
            "status": "success",
            "error": None
        }
        
        final_state = app_graph.invoke(initial_state)
        return dict(final_state)


def get_orchestrator() -> BaseOrchestrator:
    """Factory to retrieve the configured Orchestrator client."""
    # To enforce a specific client regardless of langgraph availability, config can be read here.
    return LangGraphOrchestrator()
