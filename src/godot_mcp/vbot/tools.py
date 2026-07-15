"""V-Bot Mind integration tools for Godot MCP.

Connects godot-mcp to vbot-mind-mcp for autonomous V-Bot NPC behavior.
V-Bots perceive the Godot scene through this bridge and send actions back.
"""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field

from godot_mcp.vbot import _get_bridge

logger = logging.getLogger("godot_mcp.vbot.tools")

_READ_ONLY = {"readonly": True}
_MUTATING = {"mutating": True}


def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations=_MUTATING, version="0.1.0")
    async def vbot_connect(
        url: Annotated[str, Field(description="V-Bot Mind WebSocket bridge URL (default ws://127.0.0.1:11080)")] = "ws://127.0.0.1:11080",
    ) -> dict[str, Any]:
        """Connect to the V-Bot Mind WebSocket bridge for autonomous NPC behavior.

        Opens a WebSocket to vbot-mind-mcp's engine bridge (port 11080).
        Once connected, V-Bots can perceive the Godot scene and send actions.

        ## Return Format
        {"success": bool, "message": str, "data": {"connected": bool}}

        ## Examples
        vbot_connect()
        vbot_connect(url="ws://127.0.0.1:11080")
        """
        bridge = _get_bridge()
        ok = await bridge.connect(url)
        if ok:
            return {"success": True, "message": "Connected to V-Bot Mind bridge", "data": bridge.get_status()}
        return {"success": False, "message": f"Failed to connect: {bridge._last_error}", "data": bridge.get_status()}

    @mcp.tool(annotations=_MUTATING, version="0.1.0")
    async def vbot_subscribe(
        bot_ids: Annotated[list[str], Field(description="List of V-Bot IDs to subscribe to (e.g. ['vbot_abc123', 'vbot_def456']).")],
    ) -> dict[str, Any]:
        """Subscribe to V-Bot updates. Receives actions when bots think in the game loop.

        ## Return Format
        {"success": bool, "message": str}
        """
        bridge = _get_bridge()
        if not bridge.connected:
            return {"success": False, "message": "Not connected to V-Bot bridge. Call vbot_connect() first."}
        ok = await bridge.subscribe(bot_ids)
        return {"success": ok, "message": f"Subscribed to {len(bot_ids)} V-Bot(s)" if ok else "Subscribe failed"}

    @mcp.tool(annotations=_MUTATING, version="0.1.0")
    async def vbot_perceive(
        bot_id: Annotated[str, Field(description="V-Bot ID to send perception to.")],
        observations: Annotated[str, Field(description="What the V-Bot sees/hears/senses in natural language.")],
        visible_entities: Annotated[list[str] | None, Field(description="List of visible entity names/IDs in the scene.")] = None,
        world_state: Annotated[str | None, Field(description="Current world context (time of day, weather, danger level, etc.).")] = None,
    ) -> dict[str, Any]:
        """Send perception data from the Godot scene to a V-Bot.

        Feeds the V-Bot's brain with what it sees in the world. The bot will
        incorporate this into its next think cycle.

        ## Return Format
        {"success": bool, "message": str, "data": {"bot_id": str}}
        """
        bridge = _get_bridge()
        if not bridge.connected:
            return {"success": False, "message": "Not connected to V-Bot bridge. Call vbot_connect() first."}
        ok = await bridge.send_perception(bot_id, observations, visible_entities, world_state)
        return {"success": ok, "message": f"Perception sent to {bot_id}", "data": {"bot_id": bot_id}}

    @mcp.tool(annotations=_MUTATING, version="0.1.0")
    async def vbot_send_state(
        bot_id: Annotated[str, Field(description="V-Bot ID.")],
        position: Annotated[list[float] | None, Field(description="World position [x, y, z] in Godot coordinates.")] = None,
        animation: Annotated[str | None, Field(description="Current animation name, e.g. 'idle', 'walk'.")] = None,
    ) -> dict[str, Any]:
        """Send a V-Bot's current position and animation state from Godot to the brain.

        ## Return Format
        {"success": bool, "message": str}
        """
        bridge = _get_bridge()
        if not bridge.connected:
            return {"success": False, "message": "Not connected to V-Bot bridge."}
        ok = await bridge.send_bot_state(bot_id, position=position, animation=animation)
        return {"success": ok, "message": "State sent"}

    @mcp.tool(annotations=_READ_ONLY, version="0.1.0")
    async def vbot_poll_actions(
        timeout: Annotated[float, Field(description="Max seconds to wait for an action.", ge=0.1, le=10)] = 1.0,
    ) -> dict[str, Any]:
        """Poll the V-Bot bridge for pending actions from bots.

        Call this in a loop in the Godot game loop to receive bot actions
        (MOVE, SPEAK, INTERACT, IDLE, FLEE) and apply them to the scene.

        ## Return Format
        {"success": bool, "actions": [{"bot_id": str, "type": str, ...}]}

        ## Examples
        vbot_poll_actions()
        vbot_poll_actions(timeout=0.5)
        """
        bridge = _get_bridge()
        actions = await bridge.poll_actions(timeout)
        return {"success": True, "actions": actions}

    @mcp.tool(annotations=_READ_ONLY, version="0.1.0")
    async def vbot_bridge_status() -> dict[str, Any]:
        """Check the V-Bot bridge connection status.

        ## Return Format
        {"success": bool, "connected": bool, "subscribed_bots": int, "last_error": str | None}
        """
        bridge = _get_bridge()
        return {"success": True, **bridge.get_status()}

    @mcp.tool(annotations=_MUTATING, version="0.1.0")
    async def vbot_disconnect() -> dict[str, Any]:
        """Disconnect from the V-Bot Mind bridge.

        ## Return Format
        {"success": bool, "message": str}
        """
        bridge = _get_bridge()
        await bridge.disconnect()
        return {"success": True, "message": "Disconnected from V-Bot Mind bridge"}
