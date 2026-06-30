import unittest
from unittest.mock import patch, MagicMock
from app.agents.agent_execution import propose_and_execute_trade
from app.engine.strategy import Bar

class TestAgentExecution(unittest.TestCase):

    @patch("app.agents.agent_execution.db.insert_open_trade")
    @patch("app.agents.agent_execution.db.all_trades")
    @patch("app.agents.agent_execution.get_indicators")
    @patch("app.core.config.POLYGON_API_KEY", "mock_key")
    def test_propose_and_execute_trade_success(self, mock_get_indicators, mock_all_trades, mock_insert_trade):
        # 1. Mock inputs
        mock_all_trades.return_value = [] # no open positions
        
        mock_get_indicators.return_value = {
            "symbol": "AAPL",
            "latest_price": 150.0,
            "time": "2026-06-26",
            "indicators": {"atr14": 3.0}
        }
        
        mock_insert_trade.return_value = 42 # Mock trade ID
        
        thesis_result = {"verdict": "buy"}
        risk_result = {"veto": False, "adjusted_qty": 10.0}

        # 2. Run execution
        res = propose_and_execute_trade("AAPL", thesis_result, risk_result)

        # 3. Assertions
        self.assertEqual(res["status"], "executed")
        self.assertIn("trade", res)
        self.assertEqual(res["trade"]["qty"], 10.0)
        self.assertEqual(res["trade"]["side"], "long")
        self.assertEqual(res["trade"]["entry_price"], 150.0)
        # stop = 150.0 - 2 * 3.0 = 144.0
        self.assertEqual(res["trade"]["stop_price"], 144.0)
        # target = 150.0 + 2 * (2 * 3.0) = 162.0
        self.assertEqual(res["trade"]["target_price"], 162.0)
        mock_insert_trade.assert_called_once()

    @patch("app.agents.agent_execution.db.all_trades")
    def test_propose_and_execute_trade_vetoed(self, mock_all_trades):
        thesis_result = {"verdict": "buy"}
        risk_result = {"veto": True, "reason": "Concentration limit breached."}

        res = propose_and_execute_trade("AAPL", thesis_result, risk_result)
        self.assertEqual(res["status"], "vetoed")
        self.assertIn("Risk officer vetoed trade", res["message"])
        mock_all_trades.assert_not_called()
