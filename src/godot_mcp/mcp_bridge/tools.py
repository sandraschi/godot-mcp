"""MCP tools for cross-server bridging."""

from typing import Annotated

from fastmcp import Context
from pydantic import Field

from godot_mcp.mcp_bridge import get_or_create_bridge

_READ_ONLY = {"readonly": True}
_MUTATING = {"mutating": True}


async def bridge_connect(
    server_url: Annotated[str, Field(description="URL of the remote MCP server (e.g. http://localhost:10966).")],
    ctx: Context = None,
) -> dict:
    """Connect to another fleet MCP server via its REST API.

    ## Return Format
    {"success": bool, "server": str}
    """
    client = await get_or_create_bridge(server_url)
    ok = await client.connect()
    return {"success": ok, "server": server_url}


async def bridge_call_tool(
    server_url: Annotated[str, Field(description="Remote MCP server URL.")],
    tool_name: Annotated[str, Field(description="Tool name to call on remote server.")],
    arguments: Annotated[dict, Field(description="Tool arguments.", default={})] = {},
    ctx: Context = None,
) -> dict:
    """Call a tool on a remote fleet MCP server.

    ## Return Format
    {"success": bool, "tool": str, "result": {...}}

    ## Examples
    await bridge_call_tool(server_url="http://localhost:10993", tool_name="godot_status")
    """
    client = await get_or_create_bridge(server_url)
    result = await client.call_tool(tool_name, arguments)
    return {"success": result.get("success", False), "tool": tool_name, "server": server_url, "result": result}


def register(mcp):
    mcp.tool(annotations=_MUTATING, version="0.1.0")(bridge_connect)
    mcp.tool(annotations=_READ_ONLY, version="0.1.0")(bridge_call_tool)
