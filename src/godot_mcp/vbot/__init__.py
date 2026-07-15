"""V-Bot Mind bridge for Godot — WebSocket client to vbot-mind-mcp (port 11080).

Connects to the V-Bot Mind WebSocket bridge, subscribes to bot IDs,
sends perception data from the Godot scene, and receives action commands
to drive V-Bot NPCs.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

logger = logging.getLogger("godot_mcp.vbot")

_VBOT_WS_URL = "ws://127.0.0.1:11080"


class VBotBridge:
    """WebSocket client to vbot-mind-mcp bridge."""

    def __init__(self):
        self._ws = None
        self._connected = False
        self._subscribed_bots: set[str] = set()
        self._pending_actions: list[dict[str, Any]] = []
        self._last_error: str | None = None

    @property
    def connected(self) -> bool:
        return self._connected

    async def connect(self, url: str = _VBOT_WS_URL) -> bool:
        """Open WebSocket connection to the V-Bot Mind bridge."""
        if self._connected:
            return True
        try:
            import websockets

            self._ws = await websockets.connect(url)
            self._connected = True
            self._last_error = None
            logger.info("Connected to V-Bot Mind bridge at %s", url)
            return True
        except Exception as e:
            self._last_error = str(e)
            logger.warning("V-Bot bridge connect failed: %s", e)
            self._connected = False
            return False

    async def disconnect(self) -> None:
        if self._ws:
            try:
                await self._ws.close()
            except Exception:
                pass
        self._ws = None
        self._connected = False
        self._subscribed_bots.clear()

    async def subscribe(self, bot_ids: list[str]) -> bool:
        """Subscribe to updates for one or more V-Bots."""
        if not self._connected:
            return False
        try:
            msg = json.dumps({"type": "subscribe", "bot_ids": bot_ids})
            await self._ws.send(msg)
            self._subscribed_bots.update(bot_ids)
            return True
        except Exception as e:
            self._last_error = str(e)
            return False

    async def send_perception(
        self,
        bot_id: str,
        observations: str,
        visible_entities: list[str] | None = None,
        world_state: str | None = None,
    ) -> bool:
        """Send perception data for a V-Bot."""
        if not self._connected:
            return False
        try:
            msg: dict[str, Any] = {
                "type": "perception",
                "bot_id": bot_id,
                "observations": observations,
                "visible_entities": visible_entities or [],
            }
            if world_state:
                msg["world_state"] = world_state
            await self._ws.send(json.dumps(msg))
            return True
        except Exception as e:
            self._last_error = str(e)
            return False

    async def send_bot_state(
        self,
        bot_id: str,
        position: list[float] | None = None,
        rotation: list[float] | None = None,
        animation: str | None = None,
    ) -> bool:
        """Send V-Bot position/state from the Godot scene."""
        if not self._connected:
            return False
        try:
            msg: dict[str, Any] = {"type": "bot_state", "bot_id": bot_id}
            if position:
                msg["position"] = position
            if rotation:
                msg["rotation"] = rotation
            if animation:
                msg["animation"] = animation
            await self._ws.send(json.dumps(msg))
            return True
        except Exception as e:
            self._last_error = str(e)
            return False

    async def poll_actions(self, timeout: float = 1.0) -> list[dict[str, Any]]:
        """Read pending actions from the bridge."""
        if not self._connected or not self._ws:
            return self._pending_actions
        try:
            async with asyncio.timeout(timeout):
                raw = await self._ws.recv()
            msg = json.loads(raw)
            action_type = msg.get("type", "")
            if action_type in ("bot_command", "action"):
                self._pending_actions.append(msg)
        except TimeoutError:
            pass
        except Exception as e:
            self._last_error = str(e)
            logger.warning("V-Bot bridge poll error: %s", e)

        actions = list(self._pending_actions)
        self._pending_actions.clear()
        return actions

    async def list_bots(self) -> list[dict[str, Any]]:
        """Request bot list from the bridge."""
        if not self._connected:
            return []
        try:
            await self._ws.send(json.dumps({"type": "list_bots"}))
            raw = await self._ws.recv()
            resp = json.loads(raw)
            return resp.get("bots", [])
        except Exception as e:
            self._last_error = str(e)
            return []

    def get_status(self) -> dict[str, Any]:
        return {
            "connected": self._connected,
            "subscribed_bots": len(self._subscribed_bots),
            "last_error": self._last_error,
        }


_bridge: VBotBridge | None = None


def _get_bridge() -> VBotBridge:
    global _bridge
    if _bridge is None:
        _bridge = VBotBridge()
    return _bridge
