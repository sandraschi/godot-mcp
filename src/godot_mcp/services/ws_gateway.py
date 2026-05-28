"""WebSocket gateway for iOS mobile clients — real-time bidirectional bridge.

Architecture:
  iOS App (WebSocket) ← → WS Gateway (FastAPI) ← → Godot TCP Bridge (port 9080)
                                               ← → Python tools (itch, fleet, etc.)
                                               ← → Log ring buffer (SSE relay)

Protocol:
  Inbound: command | subscribe | unsubscribe | intent
  Outbound: ack | result | error | event | frame
"""

import asyncio
import json
import logging
import uuid

from fastapi import WebSocket, WebSocketDisconnect

from godot_mcp.services.godot_bridge import GODOT_HOST, GODOT_PORT, get_bridge
from godot_mcp.services.mobile_help import get_mobile_help

logger = logging.getLogger("godot-mcp.ws-gateway")

# ── Client Manager ────────────────────────────────────────────────────────────


class WSClient:
    """Represents a single iOS device connected via WebSocket.

    Tracks the client's app type, active channel subscriptions,
    and the underlying WebSocket connection.

    Attributes:
        id: Short 8-char UUID for log correlation.
        ws: The FastAPI WebSocket connection object.
        app: Which iOS app this client is running (spatial-vibe, state-surveiller, pocket-architect).
        subscriptions: Set of channel strings. Supports wildcard suffix (``agent:*``).
    """

    def __init__(self, websocket: WebSocket, app_name: str | None = None):
        self.id = str(uuid.uuid4())[:8]
        self.ws = websocket
        self.app = app_name
        self.subscriptions: set[str] = set()


class ClientManager:
    """Manages all connected iOS WebSocket clients.

    Provides client lifecycle (add/remove), lookup by ID or app type,
    channel-based broadcast with wildcard matching, and dead client cleanup.

    Usage::

        clients = ClientManager()  # module-level singleton
        clients.add(client)
        await clients.broadcast({"type": "event", ...}, channel="logs")
        clients.remove(client_id)
    """

    def __init__(self):
        self._clients: dict[str, WSClient] = {}

    @property
    def count(self) -> int:
        """Number of currently connected iOS clients."""
        return len(self._clients)

    def add(self, client: WSClient):
        """Register a new client connection.

        Args:
            client: The WSClient instance after successful handshake.
        """
        self._clients[client.id] = client
        logger.info("WS client connected: %s (total: %d)", client.id, self.count)

    def remove(self, client_id: str):
        """Remove a client (on disconnect or broadcast failure).

        Args:
            client_id: The short UUID assigned during handshake.
        """
        self._clients.pop(client_id, None)
        logger.info("WS client disconnected: %s (total: %d)", client_id, self.count)

    def get(self, client_id: str) -> WSClient | None:
        """Look up a client by ID.

        Args:
            client_id: Short UUID assigned during handshake.

        Returns:
            The WSClient instance, or None if not found.
        """
        return self._clients.get(client_id)

    def by_app(self, app: str) -> list[WSClient]:
        """Get all clients running a specific app.

        Args:
            app: App type string (e.g. ``"spatial-vibe"``).

        Returns:
            List of matching WSClient instances.
        """
        return [c for c in self._clients.values() if c.app == app]

    def subscribed_to(self, channel: str) -> list[WSClient]:
        """Get all clients subscribed to a channel.

        Supports wildcard suffix matching: subscribing to ``"agent:*"``
        matches broadcasts to ``"agent:bot_01"``.

        Args:
            channel: The channel name to match (e.g. ``"agent:bot_01"``, ``"logs"``).

        Returns:
            List of subscribed WSClient instances.
        """
        result = []
        for client in self._clients.values():
            for sub in client.subscriptions:
                if sub.endswith("*"):
                    prefix = sub.rstrip("*")
                    if channel.startswith(prefix):
                        result.append(client)
                        break
                elif sub == channel:
                    result.append(client)
                    break
        return result

    async def broadcast(self, message: dict, channel: str | None = None):
        """Send a message to all (or subscribed) clients.

        If ``channel`` is provided, only clients subscribed to that channel
        receive the message. If a client's send fails, it's removed automatically.

        Args:
            message: The JSON-serializable message dict (should include type and payload).
            channel: Optional channel name to filter recipients.
        """
        if channel:
            targets = self.subscribed_to(channel)
        else:
            targets = list(self._clients.values())
        for client in targets:
            try:
                await client.ws.send_json(message)
            except Exception:
                self.remove(client.id)


clients = ClientManager()

# ── Message Dispatch ─────────────────────────────────────────────────────────


def _make_response(correlation_id: str | None, msg_type: str, payload: dict) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "type": msg_type,
        "correlation_id": correlation_id,
        "payload": payload,
    }


async def _dispatch_command(client: WSClient, msg: dict) -> dict:
    """Route a 'command' message to the correct handler."""
    cmd = msg.get("payload", {})
    tool_name = cmd.get("tool", "")
    arguments = cmd.get("arguments", {})

    if not tool_name:
        return _make_response(msg.get("id"), "error", {
            "error_code": "INVALID_INTENT",
            "message": "No tool specified in command",
        })

    # Route to Godot bridge tools (prefixed with godot_)
    if tool_name.startswith("godot_"):
        bridge = get_bridge()
        if not bridge.connected:
            conn = bridge.connect()
            if not conn["success"]:
                return _make_response(msg.get("id"), "error", {
                    "error_code": "BRIDGE_DISCONNECTED",
                    "message": conn.get("error", "Godot bridge not reachable"),
                    "recovery_hint": "Ensure Godot engine is running with MCP bridge addon",
                })
        action = tool_name.replace("godot_", "")
        result = bridge.send(action, arguments)
        return _make_response(msg.get("id"), "result", {
            "success": result.get("success", False),
            "data": result.get("data", {}),
            "error": result.get("error"),
            "tool": tool_name,
        })

    # Route to Python-side tools
    try:
        from godot_mcp.server import _run_python_tool
        result = await _run_python_tool(tool_name, arguments)
        return _make_response(msg.get("id"), "result", {
            "success": result.get("success", False),
            "data": result.get("data", result),
            "error": result.get("error"),
            "tool": tool_name,
        })
    except Exception as e:
        return _make_response(msg.get("id"), "error", {
            "error_code": "TOOL_FAILED",
            "message": str(e),
        })


async def _dispatch_intent(client: WSClient, msg: dict) -> dict:
    """Route an 'intent' message — high-level semantic command with spatial/voice data.

    The intent is parsed and decomposed into tool chains based on the app type.
    """
    payload = msg.get("payload", {})
    intent_type = payload.get("intent_type", "")
    app = client.app or payload.get("app", "")

    if app == "spatial-vibe":
        return await _handle_spatial_intent(client, msg)
    if app == "state-surveiller":
        return await _handle_intervention_intent(client, msg)
    if app == "pocket-architect":
        return await _handle_generation_intent(client, msg)

    return _make_response(msg.get("id"), "error", {
        "error_code": "INVALID_INTENT",
        "message": f"Unknown app or intent_type: {app}/{intent_type}",
    })


async def _handle_spatial_intent(client: WSClient, msg: dict) -> dict:
    """Spatial Vibe-Director: decompose spatial voice intent into tool calls."""
    payload = msg.get("payload", {})
    intent_type = payload.get("intent_type", "")
    params = payload.get("parameters", {})

    bridge = get_bridge()
    if not bridge.connected:
        bridge.connect()

    if intent_type == "place_asset":
        asset_ref = params.get("asset_ref", "")
        pos = params.get("position", {"x": 0, "y": 0, "z": 0})
        material = params.get("material")
        result = bridge.send("import_glb", {
            "path": asset_ref, "name": params.get("name", "MobileAsset"),
            "position": pos, "scale": params.get("scale", 1.0),
        })
        if result.get("success") and material:
            bridge.send("set_material", {
                "node": params.get("name", "MobileAsset"),
                "color": material.get("color", "#ffffff"),
                "roughness": material.get("roughness", 0.5),
            })
        return _make_response(msg.get("id"), "result", {
            "success": result.get("success", False),
            "data": result.get("data", {}),
            "intent_type": intent_type,
        })

    if intent_type == "anchor_light":
        light_type = params.get("light_type", "omni")
        pos = params.get("position", {"x": 0, "y": 5, "z": 0})
        result = bridge.send("add_light", {
            "type": light_type,
            "name": params.get("name", "MobileLight"),
            "intensity": params.get("intensity", 1.0),
            "position": pos,
        })
        return _make_response(msg.get("id"), "result", {
            "success": result.get("success", False),
            "data": result.get("data", {}),
            "intent_type": intent_type,
        })

    if intent_type == "query_space":
        result = bridge.send("read_scene_tree")
        return _make_response(msg.get("id"), "result", {
            "success": result.get("success", False),
            "data": result.get("data", {}),
            "intent_type": intent_type,
        })

    return _make_response(msg.get("id"), "error", {
        "error_code": "INVALID_INTENT",
        "message": f"Unknown spatial intent: {intent_type}",
    })


async def _handle_intervention_intent(client: WSClient, msg: dict) -> dict:
    """State-Surveiller: intervention commands for agent testing loop."""
    payload = msg.get("payload", {})
    intervention_type = payload.get("intervention_type", "")
    params = payload.get("parameters", {})

    bridge = get_bridge()
    if not bridge.connected:
        bridge.connect()

    if intervention_type == "set_param":
        node = params.get("node_path", "")
        prop = params.get("property", "")
        value = params.get("value")
        if node and prop and value is not None:
            result = bridge.send("modify-node", {
                "node": node, "property": prop, "value": value,
            })
            return _make_response(msg.get("id"), "result", {
                "success": result.get("success", False),
                "data": result.get("data", {}),
            })
    if intervention_type == "force_restart":
        from godot_mcp.workflows.engine import BUILTIN_WORKFLOWS
        if "test_agent_restart" in BUILTIN_WORKFLOWS:
            workflow = BUILTIN_WORKFLOWS["test_agent_restart"]
            result = await workflow.run(lambda t, p: bridge.send(t.replace("godot_", ""), p))
            return _make_response(msg.get("id"), "result", {
                "success": result.get("success", False),
                "data": result.get("data", {}),
            })

    return _make_response(msg.get("id"), "error", {
        "error_code": "INVALID_INTENT",
        "message": f"Unknown intervention: {intervention_type}",
    })


async def _handle_generation_intent(client: WSClient, msg: dict) -> dict:
    """Pocket Architect: high-level generative commands."""
    payload = msg.get("payload", {})
    prompt = payload.get("prompt", "")
    mode = payload.get("mode", "environment")

    bridge = get_bridge()
    if not bridge.connected:
        bridge.connect()

    if mode == "gdscript":
        from godot_mcp.sampling.service import sample_text
        code = await sample_text(None, prompt=f"Write GDScript: {prompt}", max_tokens=1024)
        return _make_response(msg.get("id"), "result", {
            "success": True,
            "data": {"code": code, "mode": "gdscript"},
        })

    if mode in ("environment", "environment"):
        from godot_mcp.game_builder import pipeline
        try:
            plan = await pipeline.design_game(prompt)
            return _make_response(msg.get("id"), "result", {
                "success": True,
                "data": {"plan": json.loads(plan.to_json()), "mode": "environment"},
            })
        except Exception as e:
            return _make_response(msg.get("id"), "error", {
                "error_code": "TOOL_FAILED",
                "message": f"Generation failed: {e}",
            })

    return _make_response(msg.get("id"), "result", {
        "success": True,
        "data": {"message": f"Received {mode} intent: {prompt}", "mode": mode},
    })

# ── Background Tasks ─────────────────────────────────────────────────────────


async def _push_log_entries():
    """Background task: push log entries to clients subscribed to the ``logs`` channel.

    Reads from the 2000-entry ring buffer in :mod:`godot_mcp.server`, polling every 0.5s.
    Only newly appended entries since the last poll are broadcast.
    """
    from godot_mcp.server import LOG_RING
    last_idx = len(LOG_RING)
    while True:
        await asyncio.sleep(0.5)
        if len(LOG_RING) > last_idx:
            entries = list(LOG_RING)[last_idx:]
            last_idx = len(LOG_RING)
            for entry in entries:
                await clients.broadcast(
                    {"id": str(uuid.uuid4()), "type": "event",
                     "correlation_id": None,
                     "payload": {"channel": "logs", "data": entry}},
                    channel="logs",
                )


async def _push_godot_status():
    """Background task: push Godot engine metrics to ``godot:*`` subscribers.

    Calls the Godot TCP bridge's ``status`` action every 2 seconds and broadcasts
    the result (version, node_count, fps) to subscribed clients.
    """
    while True:
        await asyncio.sleep(2.0)
        bridge = get_bridge()
        if bridge.connected:
            try:
                result = bridge.send("status", timeout=2.0)
                if result.get("success"):
                    await clients.broadcast(
                        {"id": str(uuid.uuid4()), "type": "event",
                         "correlation_id": None,
                         "payload": {"channel": "godot:status", "data": result.get("data", {})}},
                        channel="godot:*",
                    )
            except Exception:
                logger.debug("Godot status push skipped (bridge busy)")


# ── WebSocket Endpoint ────────────────────────────────────────────────────────


async def _route_message(client: WSClient, msg: dict) -> dict | None:
    """Route an incoming message to the appropriate handler."""
    msg_type = msg.get("type", "")

    if msg_type == "command":
        return await _dispatch_command(client, msg)
    if msg_type == "intent":
        return await _dispatch_intent(client, msg)
    if msg_type == "subscribe":
        channels = msg.get("payload", {}).get("channels", [])
        client.subscriptions.update(channels)
        logger.info("Client %s subscribed to: %s", client.id, channels)
        return _make_response(msg.get("id"), "ack", {
            "subscribed": list(channels),
            "message": f"Subscribed to {len(channels)} channel(s)",
        })
    if msg_type == "unsubscribe":
        channels = msg.get("payload", {}).get("channels", [])
        for ch in channels:
            client.subscriptions.discard(ch)
        return _make_response(msg.get("id"), "ack", {
            "unsubscribed": list(channels),
        })

    if msg_type == "help":
        help_data = get_mobile_help().to_dict()
        return _make_response(msg.get("id"), "result", {
            "help": help_data,
        })

    return _make_response(msg.get("id"), "error", {
        "error_code": "INVALID_INTENT",
        "message": f"Unknown message type: {msg_type}. Valid: command, intent, subscribe, unsubscribe, help",
    })


async def mobile_ws_handler(websocket: WebSocket):
    """FastAPI WebSocket endpoint for iOS mobile clients."""
    await websocket.accept()

    client = WSClient(websocket)

    # Read initial handshake
    try:
        init = await asyncio.wait_for(websocket.receive_json(), timeout=5.0)
        client.app = init.get("app", init.get("payload", {}).get("app"))
        await websocket.send_json(_make_response(None, "ack", {
            "message": "Connected to godot-mcp mobile gateway v0.1.0",
            "server_version": "0.1.0",
            "client_id": client.id,
            "godot_bridge": GODOT_HOST + ":" + str(GODOT_PORT),
        }))
    except (TimeoutError, json.JSONDecodeError):
        await websocket.send_json(_make_response(None, "error", {
            "error_code": "HANDSHAKE_FAILED",
            "message": "Send initial JSON handshake with {'app': 'spatial-vibe|state-surveiller|pocket-architect'} within 5s",
        }))
        await websocket.close()
        return

    clients.add(client)

    try:
        while True:
            raw = await websocket.receive_json()
            response = await _route_message(client, raw)
            if response:
                await websocket.send_json(response)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.exception("WS error for client %s: %s", client.id, e)
    finally:
        clients.remove(client.id)


# ── Background Task Launcher ─────────────────────────────────────────────────


_background_tasks: list[asyncio.Task] = []


def start_background_tasks():
    """Call from server startup to begin log/status push loops."""
    loop = asyncio.get_event_loop()
    _background_tasks.append(loop.create_task(_push_log_entries()))
    _background_tasks.append(loop.create_task(_push_godot_status()))
    logger.info("WS gateway background tasks started")


def stop_background_tasks():
    for task in _background_tasks:
        task.cancel()
    _background_tasks.clear()
    logger.info("WS gateway background tasks stopped")
