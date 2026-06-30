import unittest
from unittest.mock import patch, MagicMock
from app.orchestrator.python_router import PythonOrchestrator
from app.orchestrator.graph import LangGraphOrchestrator

class TestOrchestrators(unittest.TestCase):

    @patch("app.agents.technical.TechnicalAgent.run")
    @patch("app.agents.news.NewsAgent.run")
    @patch("app.agents.macro.MacroAgent.run")
    @patch("app.agents.thesis.ThesisAgent.run")
    @patch("app.agents.risk.RiskAgent.run")
    def test_python_orchestrator(self, mock_risk, mock_thesis, mock_macro, mock_news, mock_technical):
        # Setup mocks
        mock_technical.return_value = {"conclusion": "bullish", "evidence": ["Price > 200 SMA"]}
        mock_news.return_value = {"sentiment_score": 0.5}
        mock_macro.return_value = {"market_regime": "bull_trending"}
        mock_thesis.return_value = {"verdict": "buy", "core_thesis": "Unified thesis text."}
        mock_risk.return_value = {"veto": False, "reason": "Passed risk checks."}

        orchestrator = PythonOrchestrator()
        result = orchestrator.orchestrate("AAPL", proposed_trade={"entry": 100.0, "stop": 95.0, "qty": 10})
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["symbol"], "AAPL")
        self.assertEqual(result["technical_analysis"]["conclusion"], "bullish")
        self.assertEqual(result["news_analysis"]["sentiment_score"], 0.5)
        self.assertEqual(result["macro_analysis"]["market_regime"], "bull_trending")
        self.assertEqual(result["thesis"]["verdict"], "buy")
        self.assertEqual(result["risk_analysis"]["veto"], False)

    @patch("app.agents.technical.TechnicalAgent.run")
    @patch("app.agents.news.NewsAgent.run")
    @patch("app.agents.macro.MacroAgent.run")
    @patch("app.agents.thesis.ThesisAgent.run")
    @patch("app.agents.risk.RiskAgent.run")
    def test_langgraph_orchestrator_fallback(self, mock_risk, mock_thesis, mock_macro, mock_news, mock_technical):
        # Verify that if LangGraph is run (either via native or fallback), it routes correctly
        mock_technical.return_value = {"conclusion": "bullish", "evidence": ["Price > 200 SMA"]}
        mock_news.return_value = {"sentiment_score": 0.5}
        mock_macro.return_value = {"market_regime": "bull_trending"}
        mock_thesis.return_value = {"verdict": "buy", "core_thesis": "Unified thesis text."}
        mock_risk.return_value = {"veto": False, "reason": "Passed risk checks."}

        orchestrator = LangGraphOrchestrator()
        result = orchestrator.orchestrate("AAPL", proposed_trade={"entry": 100.0, "stop": 95.0, "qty": 10})
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["symbol"], "AAPL")
        self.assertEqual(result["technical_analysis"]["conclusion"], "bullish")
        self.assertEqual(result["thesis"]["verdict"], "buy")
