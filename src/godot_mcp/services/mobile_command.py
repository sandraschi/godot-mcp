"""MobileCommand — Pydantic models for iOS mobile intent normalization.

Defines the canonical message types for all three iOS apps. Every command
from the mobile gateway is validated here before dispatch.

Architecture:
  iOS Raw JSON → WS Gateway → MobileCommand (validation) → Dispatch → godot-mcp tools
"""

from __future__ import annotations

import json
import logging
import uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger("godot-mcp.mobile-command")

# ── Enums ─────────────────────────────────────────────────────────────────────


class AppType(str, Enum):
    """Which iOS app is sending this message.

    Each app has its own intent types and dispatch handlers.
    - spatial-vibe: ARKit spatial lens → Godot scene manipulation
    - state-surveiller: Multi-agent test monitoring + hot-fix dashboard
    - pocket-architect: Prompt-driven generative asset pipeline
    """
    spatial_vibe = "spatial-vibe"
    state_surveiller = "state-surveiller"
    pocket_architect = "pocket-architect"


class MessageType(str, Enum):
    """Category of message an iOS client can send over the gateway.

    - command: Direct invocation of a godot-mcp tool by name
    - intent: High-level semantic action decomposed into tool chains
    - subscribe: Register for push notification channels
    - unsubscribe: Unregister from push notification channels
    """
    command = "command"
    intent = "intent"
    subscribe = "subscribe"
    unsubscribe = "unsubscribe"


class IntentType(str, Enum):
    """All semantic intents across all three iOS apps.

    Namespaced by app:
      spatial-vibe:     place_asset, anchor_light, wire_trigger, move_node, delete_node, query_space
      state-surveiller: reparent, set_param, force_restart, kill_agent, resume_loop
      pocket-architect: generate:environment, generate:asset, generate:ui_theme, generate:behavior, approve, reject, tweak
    """
    # Spatial Vibe-Director
    place_asset = "place_asset"
    anchor_light = "anchor_light"
    wire_trigger = "wire_trigger"
    move_node = "move_node"
    delete_node = "delete_node"
    query_space = "query_space"
    # State Surveiller
    reparent = "reparent"
    set_param = "set_param"
    force_restart = "force_restart"
    kill_agent = "kill_agent"
    resume_loop = "resume_loop"
    # Pocket Architect
    generate_environment = "generate:environment"
    generate_asset = "generate:asset"
    generate_ui_theme = "generate:ui_theme"
    generate_behavior = "generate:behavior"
    approve = "approve"
    reject = "reject"
    tweak = "tweak"


class ChannelName(str, Enum):
    """Available subscription channels for server-push events.

    Supports wildcard suffix matching: subscribing to 'agent:*' matches 'agent:bot_01'.
    """
    agent_all = "agent:*"
    agent_specific = "agent:{id}"
    logs = "logs"
    frames = "frames:{id}"
    godot_status = "godot:status"
    progress = "progress"


# ── Payload Models ────────────────────────────────────────────────────────────


class SpatialTransform(BaseModel):
    """Position, rotation, and scale of a spatial anchor from ARKit.

    Rotation uses quaternion representation (x, y, z, w). All vectors
    use dict format for easy JSON serialization: {"x": 0.0, "y": 0.0, "z": 0.0}
    """
    position: dict[str, float] = Field(default_factory=lambda: {"x": 0.0, "y": 0.0, "z": 0.0})
    rotation: dict[str, float] = Field(default_factory=lambda: {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0})
    scale: dict[str, float] = Field(default_factory=lambda: {"x": 1.0, "y": 1.0, "z": 1.0})


class PhysicalSpace(BaseModel):
    """Physical room description from ARKit environment scanning."""
    room_shape: str = "open"
    floor_level: float = 0.0
    dimensions: dict[str, float] = Field(default_factory=lambda: {"width": 5.0, "length": 5.0, "height": 3.0})


class SpatialAnchor(BaseModel):
    """Complete spatial anchor from iOS ARKit, mapping physical surfaces to Godot coordinates.

    The ``transform`` places the anchor relative to the ARKit world origin.
    ``tracking_state`` indicates whether ARKit currently has a lock on this anchor.
    """
    anchor_id: str = ""
    transform: SpatialTransform = Field(default_factory=SpatialTransform)
    physical_space: PhysicalSpace = Field(default_factory=PhysicalSpace)
    tracking_state: str = "normal"


class SpatialIntentPayload(BaseModel):
    """Voice + gesture intent for the Spatial Vibe-Director app.

    Combines ARKit anchor data with natural language voice transcription
    and structured parameters for Godot scene manipulation.
    """
    intent_type: IntentType
    transcript: str = ""
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    target_anchor: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)


class InterventionPayload(BaseModel):
    """Hot-fix intervention for the State-Surveiller app.

    Used to modify a running agent test — adjusting physics parameters,
    reparenting nodes, or restarting stuck agents without restarting
    the Godot engine.
    """
    intervention_type: IntentType
    target_agent: str = ""
    parameters: dict[str, Any] = Field(default_factory=dict)


class GenerationIntentPayload(BaseModel):
    """Generation request for the Pocket Architect app.

    A natural-language prompt with mode and constraints. The server
    decomposes this into tool chains (LLM sampling, asset import,
    scene composition, shader generation).
    """
    prompt: str
    mode: str = "environment"
    constraints: dict[str, Any] = Field(default_factory=dict)
    outputs_requested: list[str] = Field(default_factory=lambda: ["screenshot", "gdscript"])


class SubscriptionPayload(BaseModel):
    """Channel subscription request. Supports wildcard suffix matching."""
    channels: list[str]


class CommandPayload(BaseModel):
    """Direct tool invocation payload.

    The ``tool`` field matches godot-mcp tool names (e.g. ``godot_read_scene_tree``).
    Bridge tools are prefixed with ``godot_``; Python tools use their module name.
    """
    tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    action_map: str | None = None


# ── Envelope ──────────────────────────────────────────────────────────────────


class MobileCommand(BaseModel):
    """Canonical mobile command envelope — every iOS message is validated here.

    This is the single point of entry validation for all mobile gateway traffic.
    The ``type`` field determines which payload schema is validated against:

    - ``command`` → :class:`CommandPayload` — direct tool invocation
    - ``intent`` → :class:`SpatialIntentPayload` / :class:`InterventionPayload` / :class:`GenerationIntentPayload`
    - ``subscribe`` / ``unsubscribe`` → :class:`SubscriptionPayload`

    If validation fails, the gateway returns an error with ``INVALID_INTENT`` code
    *before* any tool code is executed.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType
    app: AppType | None = None
    timestamp: str | None = None
    payload: dict[str, Any]

    # ── Helpers ───────────────────────────────────────────────────────────

    @field_validator("payload")
    @classmethod
    def validate_payload(cls, v: dict, info: Any) -> dict:
        """Ensure payload shape matches the message type."""
        msg_type = info.data.get("type")
        if msg_type == MessageType.command:
            CommandPayload.model_validate(v)
        elif msg_type == MessageType.subscribe or msg_type == MessageType.unsubscribe:
            SubscriptionPayload.model_validate(v)
        elif msg_type == MessageType.intent:
            app = info.data.get("app")
            if app == AppType.spatial_vibe:
                SpatialIntentPayload.model_validate(v)
            elif app == AppType.state_surveiller:
                InterventionPayload.model_validate(v)
            elif app == AppType.pocket_architect:
                GenerationIntentPayload.model_validate(v)
        return v

    def to_json(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_json(cls, raw: str) -> MobileCommand:
        data = json.loads(raw)
        return cls.model_validate(data)

    @classmethod
    def from_dict(cls, data: dict) -> MobileCommand:
        return cls.model_validate(data)


# ── Response Models ──────────────────────────────────────────────────────────


class MobileResponse(BaseModel):
    """Standard response envelope for all mobile gateway responses.

    - ``ack``: Confirmation (subscribe, unsubscribe, handshake)
    - ``result``: Synchronous command/intent result with data
    - ``error``: Error with error_code, message, and recovery_hint
    - ``event``: Server-pushed event for subscribed channels
    - ``frame``: Server-pushed base64-encoded image frame
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str = "ack"
    correlation_id: str | None = None
    payload: dict[str, Any]


# ── Dispatch Layer ───────────────────────────────────────────────────────────


class MobileDispatchResult(BaseModel):
    """Normalized result from the MobileDispatcher.

    Every dispatch path returns this model. The WS gateway wraps it into
    the response envelope. ``error_code`` and ``recovery_hint`` enable
    the iOS client to show actionable error messages.
    """
    success: bool
    message: str = ""
    data: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    error_code: str | None = None
    recovery_hint: str | None = None


class MobileDispatcher:
    """Routes validated :class:`MobileCommand` instances to godot-mcp tool calls.

    This is the single entry point for all iOS-originating actions. It
    dispatches to either the Godot TCP bridge (:class:`GodotBridge`) or
    Python-side tool runners depending on the tool name prefix.

    Usage::

        dispatcher = get_dispatcher()
        cmd = MobileCommand.from_dict(raw_message)
        result = await dispatcher.dispatch(cmd)

    Three dispatch paths:

    - ``command`` → :meth:`_handle_command` — direct tool by name
    - ``intent`` → :meth:`_handle_intent` → app-specific handler
      - ``spatial-vibe`` → :meth:`_dispatch_spatial`
      - ``state-surveiller`` → :meth:`_dispatch_intervention`
      - ``pocket-architect`` → :meth:`_dispatch_generation`
    """

    def __init__(self):
        self._bridge = None

    @property
    def bridge(self):
        if self._bridge is None:
            from godot_mcp.services.godot_bridge import get_bridge
            self._bridge = get_bridge()
        return self._bridge

    async def dispatch(self, cmd: MobileCommand) -> MobileDispatchResult:
        """Route a validated MobileCommand to the appropriate handler."""
        if cmd.type == MessageType.command:
            return await self._handle_command(cmd)
        if cmd.type == MessageType.intent:
            return await self._handle_intent(cmd)
        return MobileDispatchResult(
            success=False, error=f"Unsupported type: {cmd.type}",
            error_code="INVALID_INTENT",
        )

    async def _handle_command(self, cmd: MobileCommand) -> MobileDispatchResult:
        """Direct tool invocation."""
        payload = CommandPayload.model_validate(cmd.payload)
        tool = payload.tool

        if tool.startswith("godot_"):
            if not self.bridge.connected:
                conn = self.bridge.connect()
                if not conn["success"]:
                    return MobileDispatchResult(
                        success=False, error=conn.get("error", "Bridge not connected"),
                        error_code="BRIDGE_DISCONNECTED",
                        recovery_hint="Ensure Godot engine is running with MCP bridge addon",
                    )
            action = tool.replace("godot_", "")
            result = self.bridge.send(action, payload.arguments)
            return MobileDispatchResult(
                success=result.get("success", False),
                data=result.get("data", {}),
                error=result.get("error"),
            )

        # Python-side tool
        try:
            from godot_mcp.server import _run_python_tool
            if tool == "workflow_run":
                result = await _run_python_tool(tool, payload.arguments)
            else:
                result = await _run_python_tool(tool, payload.arguments)
            return MobileDispatchResult(
                success=result.get("success", False),
                data=result.get("data", result),
                error=result.get("error"),
            )
        except Exception as e:
            return MobileDispatchResult(
                success=False, error=str(e),
                error_code="TOOL_FAILED",
            )

    async def _handle_intent(self, cmd: MobileCommand) -> MobileDispatchResult:
        """High-level intent decomposition."""
        app = cmd.app
        payload = cmd.payload

        if app == AppType.spatial_vibe:
            return await self._dispatch_spatial(payload)
        if app == AppType.state_surveiller:
            return await self._dispatch_intervention(payload)
        if app == AppType.pocket_architect:
            return await self._dispatch_generation(payload)

        return MobileDispatchResult(
            success=False, error=f"Unknown app: {app}",
            error_code="INVALID_INTENT",
        )

    async def _dispatch_spatial(self, payload: dict) -> MobileDispatchResult:
        intent = SpatialIntentPayload.model_validate(payload)
        params = intent.parameters

        if intent.intent_type == IntentType.place_asset:
            asset = params.get("asset_ref", "")
            pos = params.get("position", {"x": 0, "y": 0, "z": 0})
            name = params.get("name", asset.split("/")[-1] if "/" in asset else "MobileAsset")
            result = self.bridge.send("import_glb", {
                "path": asset, "name": name, "position": pos,
                "scale": params.get("scale", 1.0),
            })
            if result.get("success"):
                mat = params.get("material")
                if mat:
                    self.bridge.send("set_material", {
                        "node": name, "color": mat.get("color", "#ffffff"),
                        "roughness": mat.get("roughness", 0.5),
                    })
            return MobileDispatchResult(
                success=result.get("success", False),
                data=result.get("data", {}),
                error=result.get("error"),
            )

        if intent.intent_type == IntentType.anchor_light:
            pos = params.get("position", {"x": 0, "y": 5, "z": 0})
            result = self.bridge.send("add_light", {
                "type": params.get("light_type", "omni"),
                "name": params.get("name", "MobileLight"),
                "intensity": params.get("intensity", 1.0),
                "position": pos,
            })
            return MobileDispatchResult(
                success=result.get("success", False),
                data=result.get("data", {}),
            )

        if intent.intent_type == IntentType.query_space:
            result = self.bridge.send("read_scene_tree")
            return MobileDispatchResult(
                success=result.get("success", False),
                data=result.get("data", {}),
            )

        return MobileDispatchResult(
            success=False, error=f"Unknown spatial intent: {intent.intent_type}",
            error_code="INVALID_INTENT",
        )

    async def _dispatch_intervention(self, payload: dict) -> MobileDispatchResult:
        intent = InterventionPayload.model_validate(payload)
        params = intent.parameters

        if intent.intervention_type == IntentType.set_param:
            node = params.get("node_path", "")
            prop = params.get("property", "")
            value = params.get("value")
            if node and prop and value is not None:
                result = self.bridge.send("modify-node", {
                    "node": node, "property": prop, "value": value,
                })
                return MobileDispatchResult(
                    success=result.get("success", False),
                    data=result.get("data", {}),
                )

        if intent.intervention_type == IntentType.force_restart:
            result = self.bridge.send("headless_verify")
            return MobileDispatchResult(
                success=True,
                message="Restart signal sent",
                data=result.get("data", {}),
            )

        return MobileDispatchResult(
            success=False,
            error=f"Unknown intervention: {intent.intervention_type}",
            error_code="INVALID_INTENT",
        )

    async def _dispatch_generation(self, payload: dict) -> MobileDispatchResult:
        intent = GenerationIntentPayload.model_validate(payload)

        if intent.mode == "gdscript":
            from godot_mcp.sampling.service import sample_text
            try:
                code = await sample_text(
                    None,
                    prompt=f"Write GDScript:\n\n{intent.prompt}",
                    max_tokens=1024,
                )
                return MobileDispatchResult(
                    success=True,
                    data={"code": code, "mode": "gdscript", "prompt": intent.prompt},
                )
            except Exception as e:
                return MobileDispatchResult(
                    success=False, error=str(e), error_code="TOOL_FAILED",
                )

        if intent.mode == "environment":
            from godot_mcp.game_builder import pipeline
            try:
                plan = await pipeline.design_game(intent.prompt)
                return MobileDispatchResult(
                    success=True,
                    data={"plan": json.loads(plan.to_json()), "mode": "environment"},
                    message=f"Game: {plan.title} ({plan.genre or 'arcade'})",
                )
            except Exception as e:
                return MobileDispatchResult(
                    success=False, error=str(e), error_code="TOOL_FAILED",
                )

        return MobileDispatchResult(
            success=True,
            data={"message": f"Received {intent.mode} intent", "mode": intent.mode},
        )


# Singleton
_dispatcher: MobileDispatcher | None = None


def get_dispatcher() -> MobileDispatcher:
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = MobileDispatcher()
    return _dispatcher
