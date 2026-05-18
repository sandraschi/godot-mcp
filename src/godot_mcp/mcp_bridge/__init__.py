"""MCP Bridge — cross-server MCP communication.

Allows godot-mcp to connect to other MCP servers and execute
their tools remotely. Uses the MCP HTTP/SSE transport.
"""
import logging

import httpx

logger = logging.getLogger("godot-mcp.bridge-client")


class MCPBridgeClient:
    def __init__(self, server_url: str):
        self.server_url = server_url.rstrip("/")
        self._session_id: str | None = None
        self._http = httpx.AsyncClient(timeout=30.0)

    async def connect(self) -> bool:
        """SSE POST to get a session ID."""
        try:
            resp = await self._http.post(f"{self.server_url}/sse")
            if resp.status_code == 200:
                logger.info("Connected to bridge: %s", self.server_url)
                return True
            logger.warning("Bridge connect failed: %s", resp.status_code)
            return False
        except Exception as e:
            logger.warning("Bridge connect error: %s", e)
            return False

    async def call_tool(self, tool_name: str, arguments: dict | None = None) -> dict:
        """Call a tool on the remote MCP server via HTTP POST."""
        try:
            payload = {"tool": tool_name, "arguments": arguments or {}}
            resp = await self._http.post(
                f"{self.server_url}/api/v1/control/tool",
                json=payload,
            )
            if resp.status_code == 200:
                return resp.json()
            return {"success": False, "error": f"HTTP {resp.status_code}", "detail": resp.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def list_tools(self) -> list[dict]:
        """List available tools from the remote MCP server (status-based)."""
        try:
            resp = await self._http.get(f"{self.server_url}/api/v1/status")
            if resp.status_code == 200:
                data = resp.json()
                return data.get("tools", [])
            return []
        except Exception as e:
            logger.warning("Bridge list_tools error: %s", e)
            return []

    async def close(self):
        await self._http.aclose()


_bridge_clients: dict[str, MCPBridgeClient] = {}


async def get_or_create_bridge(server_url: str) -> MCPBridgeClient:
    if server_url not in _bridge_clients:
        client = MCPBridgeClient(server_url)
        await client.connect()
        _bridge_clients[server_url] = client
    return _bridge_clients[server_url]
