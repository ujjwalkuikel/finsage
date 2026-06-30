import unittest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from app.core.mcp_client import MCPClientManager, MCPConnection

# Helper to run async tests in unittest
def async_test(coro):
    def wrapper(*args, **kwargs):
        return asyncio.run(coro(*args, **kwargs))
    return wrapper

class TestMCPClientManager(unittest.TestCase):

    def setUp(self):
        self.manager = MCPClientManager()

    @patch("app.core.mcp_client.sse_client")
    @patch("app.core.mcp_client.ClientSession")
    @async_test
    async def test_connect_sse_success(self, mock_session_cls, mock_sse_client):
        # 1. Setup mock streams
        mock_read = AsyncMock()
        mock_write = AsyncMock()
        
        mock_connection = AsyncMock()
        mock_connection.__aenter__.return_value = (mock_read, mock_write)
        mock_sse_client.return_value = mock_connection

        # 2. Setup mock session
        mock_session = AsyncMock()
        mock_session.initialize = AsyncMock()
        
        mock_session_context = AsyncMock()
        mock_session_context.__aenter__.return_value = mock_session
        mock_session_cls.return_value = mock_session_context

        # 3. Call connect_sse
        ok = await self.manager.connect_sse(
            name="test_server",
            url="http://mock-mcp-server/sse",
            headers={"Authorization": "Bearer mock-token"}
        )

        # 4. Verify results
        self.assertTrue(ok)
        self.assertTrue(self.manager.is_connected("test_server"))
        self.assertEqual(self.manager.connections["test_server"].server_url, "http://mock-mcp-server/sse")
        
        mock_sse_client.assert_called_once_with(url="http://mock-mcp-server/sse", headers={"Authorization": "Bearer mock-token"})
        mock_session.initialize.assert_called_once()

    @patch("app.core.mcp_client.sse_client")
    @async_test
    async def test_connect_sse_failure(self, mock_sse_client):
        mock_sse_client.side_effect = Exception("Connection failed")
        
        ok = await self.manager.connect_sse(
            name="test_server",
            url="http://mock-mcp-server/sse"
        )
        
        self.assertFalse(ok)
        self.assertFalse(self.manager.is_connected("test_server"))

    @async_test
    async def test_list_tools(self):
        # Setup mock connection & session
        mock_session = AsyncMock()
        
        # Mock ListToolsResult structure
        mock_tool = MagicMock()
        mock_tool.name = "buy_stock"
        mock_tool.description = "Place a buy order"
        mock_tool.inputSchema = {"type": "object"}
        
        mock_result = MagicMock()
        mock_result.tools = [mock_tool]
        mock_session.list_tools.return_value = mock_result
        
        mock_stack = AsyncMock()
        
        conn = MCPConnection(
            name="test_server",
            session=mock_session,
            exit_stack=mock_stack
        )
        self.manager.connections["test_server"] = conn

        # List tools
        res = await self.manager.list_tools("test_server")
        
        self.assertIn("test_server", res)
        self.assertEqual(len(res["test_server"]), 1)
        self.assertEqual(res["test_server"][0]["name"], "buy_stock")
        self.assertEqual(res["test_server"][0]["description"], "Place a buy order")

    @async_test
    async def test_execute_tool(self):
        # Setup mock session
        mock_session = AsyncMock()
        
        # Mock CallToolResult
        mock_content = MagicMock()
        mock_content.text = "Order filled successfully."
        
        mock_result = MagicMock()
        mock_result.content = [mock_content]
        mock_result.isError = False
        mock_session.call_tool.return_value = mock_result
        
        mock_stack = AsyncMock()
        
        conn = MCPConnection(
            name="test_server",
            session=mock_session,
            exit_stack=mock_stack
        )
        self.manager.connections["test_server"] = conn

        # Execute tool
        res = await self.manager.execute_tool(
            server_name="test_server",
            tool_name="buy_stock",
            arguments={"symbol": "AAPL", "qty": 10}
        )

        self.assertTrue(res["ok"])
        self.assertEqual(res["content"][0]["text"], "Order filled successfully.")
        mock_session.call_tool.assert_called_once_with("buy_stock", {"symbol": "AAPL", "qty": 10})
