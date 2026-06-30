import asyncio
import logging
from contextlib import AsyncExitStack
from typing import Dict, List, Optional, Any
from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client, StdioServerParameters

logger = logging.getLogger("app.mcp")

class MCPConnection:
    """
    Wraps an active connection (streams and ClientSession) to an MCP server.
    """
    def __init__(self, name: str, session: ClientSession, exit_stack: AsyncExitStack, server_url: Optional[str] = None):
        self.name = name
        self.session = session
        self.exit_stack = exit_stack
        self.server_url = server_url
        self.is_connected = True

    async def close(self):
        if self.is_connected:
            try:
                await self.exit_stack.aclose()
            except Exception as e:
                logger.error(f"Error closing exit stack for {self.name}: {e}")
            self.is_connected = False


class MCPClientManager:
    """
    Manages connections to remote (SSE) and local (Stdio) MCP servers.
    Provides methods to list tools and execute tool calls across active servers.
    """
    def __init__(self):
        self.connections: Dict[str, MCPConnection] = {}
        self.lock = asyncio.Lock()

    async def connect_sse(self, name: str, url: str, headers: Optional[Dict[str, str]] = None) -> bool:
        """
        Connects to a remote MCP server via SSE transport.
        """
        async with self.lock:
            # If already connected, close the old one
            if name in self.connections:
                logger.info(f"Reconnecting {name} MCP server...")
                await self.connections[name].close()
                del self.connections[name]

            exit_stack = AsyncExitStack()
            try:
                logger.info(f"Connecting to remote MCP server '{name}' via SSE at {url}...")
                
                # Establish SSE streams connection
                connection = await exit_stack.enter_async_context(
                    sse_client(url=url, headers=headers)
                )
                read_stream, write_stream = connection

                # Initialize ClientSession
                session = await exit_stack.enter_async_context(
                    ClientSession(read_stream, write_stream)
                )
                await session.initialize()

                self.connections[name] = MCPConnection(
                    name=name,
                    session=session,
                    exit_stack=exit_stack,
                    server_url=url
                )
                logger.info(f"Successfully connected to remote MCP server '{name}'")
                return True
            except Exception as e:
                logger.error(f"Failed to connect to remote MCP server '{name}' at {url}: {e}")
                await exit_stack.aclose()
                return False

    async def connect_stdio(self, name: str, command: str, args: List[str], env: Optional[Dict[str, str]] = None) -> bool:
        """
        Connects to a local MCP server via stdio transport (spawns subprocess).
        """
        async with self.lock:
            if name in self.connections:
                await self.connections[name].close()
                del self.connections[name]

            exit_stack = AsyncExitStack()
            try:
                logger.info(f"Launching local MCP server '{name}' via command: {command} {' '.join(args)}...")
                server_params = StdioServerParameters(command=command, args=args, env=env)
                
                connection = await exit_stack.enter_async_context(stdio_client(server_params))
                read_stream, write_stream = connection

                session = await stack.enter_async_context(ClientSession(read_stream, write_stream))
                await session.initialize()

                self.connections[name] = MCPConnection(
                    name=name,
                    session=session,
                    exit_stack=exit_stack
                )
                logger.info(f"Successfully launched and connected to local MCP server '{name}'")
                return True
            except Exception as e:
                logger.error(f"Failed to launch local MCP server '{name}': {e}")
                await exit_stack.aclose()
                return False

    async def disconnect(self, name: str):
        async with self.lock:
            if name in self.connections:
                logger.info(f"Disconnecting MCP server '{name}'...")
                await self.connections[name].close()
                del self.connections[name]

    async def disconnect_all(self):
        async with self.lock:
            names = list(self.connections.keys())
            for name in names:
                logger.info(f"Disconnecting MCP server '{name}'...")
                await self.connections[name].close()
                del self.connections[name]

    def is_connected(self, name: str) -> bool:
        return name in self.connections and self.connections[name].is_connected

    async def list_tools(self, name: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retrieves list of tools for a specific connected server, or all of them.
        """
        results = {}
        async with self.lock:
            targets = [name] if name else list(self.connections.keys())
            
            for target in targets:
                conn = self.connections.get(target)
                if not conn or not conn.is_connected:
                    continue
                try:
                    tools_result = await conn.session.list_tools()
                    # Parse tools from session response
                    tools_list = []
                    for t in tools_result.tools:
                        tools_list.append({
                            "name": t.name,
                            "description": t.description,
                            "inputSchema": t.inputSchema
                        })
                    results[target] = tools_list
                except Exception as e:
                    logger.error(f"Failed to list tools for '{target}': {e}")
                    results[target] = [{"error": str(e)}]
        return results

    async def execute_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calls a specific tool on a specific connected MCP server.
        """
        async with self.lock:
            conn = self.connections.get(server_name)
            if not conn:
                return {"error": f"MCP server '{server_name}' is not connected."}
            if not conn.is_connected:
                return {"error": f"MCP server '{server_name}' connection is inactive."}
                
            try:
                result = await conn.session.call_tool(tool_name, arguments)
                # Convert the CallToolResult to a JSON-serializable dictionary
                content_list = []
                for content in result.content:
                    if hasattr(content, "text"):
                        content_list.append({"type": "text", "text": content.text})
                    elif hasattr(content, "json"):
                        content_list.append({"type": "json", "json": content.json})
                return {
                    "ok": True,
                    "content": content_list,
                    "isError": getattr(result, "isError", False)
                }
            except Exception as e:
                logger.error(f"Error calling tool '{tool_name}' on '{server_name}': {e}")
                return {"error": str(e)}

# Singleton manager instance
mcp_manager = MCPClientManager()
