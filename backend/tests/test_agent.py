import unittest
from unittest.mock import patch, MagicMock
from app.agents.llm import call_llm
from app.agents.tools import get_indicators, run_backtest
from app.agents.technical import TechnicalAgent

class TestAgentComponents(unittest.TestCase):

    @patch("app.agents.llm.httpx.post")
    @patch("app.core.config.GEMINI_API_KEY", "mock_gemini_key")
    def test_call_llm_gemini(self, mock_post):
        # Mock successful Gemini API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "Bullish technical indicators."}
                        ]
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        res = call_llm("test prompt")
        self.assertEqual(res, "Bullish technical indicators.")
        mock_post.assert_called_once()

    @patch("app.agents.tools.PolygonFeed")
    @patch("app.core.config.POLYGON_API_KEY", "mock_poly_key")
    def test_get_indicators(self, mock_feed_class):
        # Mock bars generator
        mock_feed = MagicMock()
        from app.engine.strategy import Bar
        mock_feed.bars.return_value = [
            Bar(time="2026-06-25", open=100.0, high=105.0, low=98.0, close=102.0, volume=1000000.0)
            for _ in range(250)
        ]
        mock_feed_class.return_value = mock_feed

        res = get_indicators("AAPL")
        self.assertNotIn("error", res)
        self.assertEqual(res["symbol"], "AAPL")
        self.assertEqual(res["latest_price"], 102.0)
        self.assertIn("sma20", res["indicators"])
        self.assertIn("rsi14", res["indicators"])

    @patch("app.validation.gauntlet.backtest")
    @patch("app.agents.tools.PolygonFeed")
    @patch("app.core.config.POLYGON_API_KEY", "mock_poly_key")
    def test_run_backtest(self, mock_feed_class, mock_backtest):

        # Mock feed bars
        mock_feed = MagicMock()
        from app.engine.strategy import Bar
        mock_feed.bars.return_value = [
            Bar(time="2026-06-25", open=100.0, high=105.0, low=98.0, close=102.0, volume=1000000.0)
            for _ in range(50)
        ]
        mock_feed_class.return_value = mock_feed

        # Mock backtest return
        mock_backtest.return_value = {
            "trades": [],
            "stats": {"win_rate": 60.0, "expectancy_r": 1.5, "profit_factor": 1.8, "max_dd": 0.05}
        }

        res = run_backtest("rayner_teo_pullback", "AAPL")
        self.assertNotIn("error", res)
        self.assertEqual(res["strategy"], "rayner_teo_pullback")
        self.assertEqual(res["stats"]["win_rate"], 60.0)

    @patch("app.agents.technical.call_llm")
    @patch("app.agents.technical.run_backtest")
    @patch("app.agents.technical.get_indicators")
    def test_technical_agent_run(self, mock_indicators, mock_backtest, mock_call_llm):
        # Mock get_indicators and run_backtest
        mock_indicators.return_value = {
            "symbol": "AAPL",
            "latest_price": 150.0,
            "time": "2026-06-25",
            "indicators": {"sma200": 140.0, "rsi14": 45.0, "sma20": 148.0, "sma50": 145.0, "rsi2": 10.0, "atr14": 3.0, "avg_volume_20d": 100000.0},
            "performance": {"perf_1d_pct": 1.0, "perf_5d_pct": 2.0, "perf_20d_pct": 5.0}
        }
        mock_backtest.return_value = {
            "total_trades": 5,
            "stats": {"win_rate": 60.0, "expectancy_r": 1.2, "profit_factor": 1.5, "max_dd": 0.04}
        }
        
        # Mock LLM returning expected json
        mock_call_llm.return_value = """
        {
            "conclusion": "bullish",
            "evidence": ["Price is above 200 SMA", "RSI(2) is oversold"],
            "inputs_used": {"sma200": 140.0, "rsi2": 10.0}
        }
        """

        agent = TechnicalAgent()
        res = agent.run({"symbol": "AAPL"})
        
        self.assertNotIn("error", res)
        self.assertEqual(res["symbol"], "AAPL")
        self.assertEqual(res["conclusion"], "bullish")
        self.assertEqual(len(res["evidence"]), 2)
        self.assertEqual(res["inputs_used"]["rsi2"], 10.0)
