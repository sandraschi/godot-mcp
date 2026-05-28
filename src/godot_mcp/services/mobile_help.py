"""Mobile gateway self-documenting help system.

Provides structured, machine-readable help for iOS mobile clients.
All protocol schemas, tool maps, error codes, and examples are defined here
as dataclasses — the single source of truth for the mobile protocol.

Usage::

    # Get the full help document as a dict (for REST endpoint)
    help_dict = generate_help_dict()

    # Get as formatted JSON (for debugging)
    help_json = generate_help_json()

    # Get one-liner for startup banner
    summary = get_endpoint_summary()

Endpoints:
    GET /mobile/v1/help     — Full protocol reference as JSON
    WS type: "help"         — Same content streamed over WebSocket

Extending:
    To add a new tool, intent chain, channel, or error code, add the entries
    to the dataclass lists below. The REST endpoint and WS response will
    automatically include them on next server restart.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from typing import Any

logger = logging.getLogger("godot-mcp.mobile-help")

# ── Bridge Action Map ─────────────────────────────────────────────────────────


@dataclass
class BridgeAction:
    action: str
    description: str
    params: list[str]
    returns: list[str]
    status: str = "active"  # active | bonus | planned


BRIDGE_ACTIONS: list[BridgeAction] = [
    BridgeAction("status", "Query Godot engine version, node count, FPS", [], ["version", "node_count", "fps"]),
    BridgeAction("import_stl", "Import STL mesh into scene as MeshInstance3D", ["path", "name", "scale", "position{x,y,z}"], ["imported", "name", "vertices", "aabb"]),
    BridgeAction("import_glb", "Import GLB/GLTF 3D model (native Godot importer)", ["path", "name", "scale", "position{x,y,z}"], ["imported", "name", "total_nodes", "mesh_count"]),
    BridgeAction("play_animation", "Play or list AnimationPlayer clips on imported GLB", ["root_name", "animation", "loop", "speed_scale"], ["playing", "animation", "available_animations", "listed", "animations"]),
    BridgeAction("import_obj", "Import OBJ mesh with MTL material support", ["path", "name", "scale", "position{x,y,z}"], ["imported", "name"]),
    BridgeAction("load_velocity_field", "Load CFD velocity field CSV into node metadata", ["csv_path", "name"], ["loaded", "name", "point_count", "bbox"]),
    BridgeAction("spawn_particles", "Create GPUParticles3D system", ["count", "name", "color", "spread_{x,y,z}"], ["spawned", "name", "count"]),
    BridgeAction("animate_streamlines", "Animate particles along loaded velocity field", ["velocity_field", "particle_system", "speed"], ["animated", "particle_system", "speed_multiplier"]),
    BridgeAction("create_camera", "Create Camera3D with orbit controls", ["name", "position{x,y,z}", "look_at{x,y,z}", "fov"], ["created", "name", "fov", "position"]),
    BridgeAction("add_light", "Add directional / ambient / omni light source", ["type", "name", "intensity", "position{x,y,z}"], ["created", "name", "type", "intensity"]),
    BridgeAction("set_material", "Assign PBR StandardMaterial3D to mesh node", ["node", "color", "roughness"], ["set", "node", "color", "roughness"]),
    BridgeAction("export_web", "Export scene to HTML5/WebAssembly", ["output_path"], ["exported", "message", "output_path"]),
    BridgeAction("read_scene_tree", "Read full scene hierarchy as nested JSON", [], ["scene_tree{name,type,path,children[]}", "node_count"]),
    BridgeAction("set_config", "Write setting to project.godot ConfigFile", ["section", "key", "value"], ["updated", "section", "key", "value"]),
    BridgeAction("headless_verify", "Check headless mode status", ["script"], ["headless", "script_path", "message"]),
    BridgeAction("add_node", "Add a child node to the scene tree", ["parent_path", "node_type", "name"], ["success", "node_path"], "bonus"),
    BridgeAction("remove_node", "Remove a node from the scene tree", ["path"], ["success"], "bonus"),
    BridgeAction("save_scene", "Save the current scene to disk", ["path"], ["success", "path"], "bonus"),
    BridgeAction("modify-node", "Modify a node property (mass, position, etc.)", ["node", "property", "value"], ["success"], "bonus"),
]

# ── Python Tool Map ───────────────────────────────────────────────────────────


@dataclass
class PythonTool:
    tool: str
    description: str
    domain: str
    version: str
    annotations: str


PYTHON_TOOLS: list[PythonTool] = [
    PythonTool("itch_status", "Query itch.io/Butler status and API key validity", "itch", "0.2.1", "READ_ONLY"),
    PythonTool("godot_export_release", "Export Godot project to target platform (web/windows)", "itch", "0.2.1", "MUTATING"),
    PythonTool("itch_push_preview", "Preview butler push diff without publishing", "itch", "0.2.1", "READ_ONLY"),
    PythonTool("itch_push", "Push build to itch.io via Butler", "itch", "0.2.1", "MUTATING"),
    PythonTool("itch_latest_version", "Get latest uploaded version for an itch.io game", "itch", "0.2.1", "READ_ONLY"),
    PythonTool("ship_to_itch", "Full export → preview → push pipeline", "itch", "0.2.1", "MUTATING"),
    PythonTool("fleet_exchange_status", "Check fleet exchange directory status", "fleet", "0.2.1", "READ_ONLY"),
    PythonTool("fleet_import_from_exchange", "Import asset from fleet exchange by path", "fleet", "0.2.1", "READ_ONLY"),
    PythonTool("fleet_worldlabs_get_world", "Get world generation status from worldlabs-mcp", "fleet", "0.2.1", "READ_ONLY"),
    PythonTool("fleet_worldlabs_stage_mesh", "Stage a Marble world mesh in the exchange", "fleet", "0.2.1", "MUTATING"),
    PythonTool("fleet_worldlabs_stage_splat", "Stage a 3D Gaussian splat in the exchange", "fleet", "0.2.1", "MUTATING"),
    PythonTool("fleet_worldlabs_import_mesh", "Import a staged Marble mesh into Godot", "fleet", "0.2.1", "MUTATING"),
    PythonTool("workflow_list", "List all built-in agentic workflows", "workflows", "0.1.0", "READ_ONLY"),
    PythonTool("workflow_run", "Execute a built-in workflow by name", "workflows", "0.1.0", "MUTATING"),
]

# ── Intent → Tool Chain Map ────────────────────────────────────────────────────


@dataclass
class ToolChain:
    app: str
    intent: str
    description: str
    tool_sequence: list[str]


TOOL_CHAINS: list[ToolChain] = [
    ToolChain("spatial-vibe", "place_asset", "Import and position a 3D asset at a spatial anchor", ["godot_import_glb", "godot_set_material"]),
    ToolChain("spatial-vibe", "anchor_light", "Place a dynamic light at a spatial position", ["godot_add_light"]),
    ToolChain("spatial-vibe", "wire_trigger", "Create a trigger zone between two anchors", ["godot_read_scene_tree", "workflow_run"]),
    ToolChain("spatial-vibe", "move_node", "Reposition an existing node in the scene", ["godot_read_scene_tree", "modify-node"]),
    ToolChain("spatial-vibe", "delete_node", "Remove a node from the scene tree", ["remove_node"]),
    ToolChain("spatial-vibe", "query_space", "Get full scene tree as JSON", ["godot_read_scene_tree"]),
    ToolChain("state-surveiller", "reparent", "Change a node's parent in the scene tree", ["godot_read_scene_tree", "modify-node"]),
    ToolChain("state-surveiller", "set_param", "Modify a property on a scene node", ["modify-node"]),
    ToolChain("state-surveiller", "force_restart", "Force-restart a stuck test agent", ["workflow_run"]),
    ToolChain("state-surveiller", "kill_agent", "Terminate a running test agent", ["bridge_call_tool"]),
    ToolChain("state-surveiller", "resume_loop", "Resume the automated agent testing loop", ["workflow_run"]),
    ToolChain("pocket-architect", "generate:environment", "Design and compose a full game environment from a prompt", ["design_game", "generate_game_worlds", "compose_game_scene"]),
    ToolChain("pocket-architect", "generate:asset", "Search depot and import a 3D asset by description", ["artifact_search", "godot_import_glb", "godot_set_material"]),
    ToolChain("pocket-architect", "generate:ui_theme", "Generate a UI theme via material advisor", ["godot_set_config", "prompt_execute"]),
    ToolChain("pocket-architect", "generate:behavior", "Generate GDScript behavior from spec", ["ai_generate_gdscript", "game_eval"]),
    ToolChain("pocket-architect", "approve", "Register a generated artifact in the depot", ["artifact_register"]),
    ToolChain("pocket-architect", "reject", "Discard a generated artifact", ["artifact_delete"]),
    ToolChain("pocket-architect", "tweak", "Re-run generation with modified constraints", ["prompt_execute"]),
]

# ── Subscription Channels ──────────────────────────────────────────────────────


@dataclass
class Channel:
    channel: str
    description: str
    push_frequency: str
    payload_shape: str


CHANNELS: list[Channel] = [
    Channel("agent:*", "All test agent state changes (stuck, crashed, completed)", "~2s", '{"agent_id", "status", "scene_state", "last_error"}'),
    Channel("agent:{id}", "Specific agent's state changes only", "~2s", '{"agent_id", "status", "current_action", "duration_sec"}'),
    Channel("logs", "Server log entries (ring buffer, 2000 entries)", "~0.5s", '{"channel": "logs", "data": "timestamp - level - message"}'),
    Channel("frames:{id}", "Streamed screenshot frames from a specific agent", "~1s", '{"channel": "frames:{id}", "data": "base64 PNG"}'),
    Channel("godot:status", "Godot engine periodic status", "~2s", '{"version", "node_count", "fps", "bridge_connected"}'),
    Channel("progress", "Long-running operation progress (generation, export)", "on change", '{"step", "pct", "message"}'),
]

# ── Error Codes ────────────────────────────────────────────────────────────────


@dataclass
class ErrorCode:
    code: str
    when: str
    recovery: str
    http_status: int


ERROR_CODES: list[ErrorCode] = [
    ErrorCode("BRIDGE_DISCONNECTED", "Godot engine not running or bridge port 9080 unreachable", "Show 'Start Godot' prompt on iOS. Ensure the MCP bridge addon is loaded.", 503),
    ErrorCode("ANCHOR_NOT_FOUND", "Spatial anchor lost tracking (ARKit tracking state 'limited'/'unavailable')", "Ask user to re-scan the physical surface and re-place the anchor.", 404),
    ErrorCode("TOOL_FAILED", "godot-mcp tool returned an error (invalid params, bridge busy, etc.)", "Display the tool error message to the user. Retry with corrected params.", 400),
    ErrorCode("INVALID_INTENT", "Voice transcription confidence < 0.4 or unknown intent_type for the app", "Ask user to rephrase. Show available intent types for their app.", 400),
    ErrorCode("AUTH_EXPIRED", "JWT token has expired (24h default lifetime)", "Re-authenticate via the auth endpoint to get a fresh token.", 401),
    ErrorCode("RATE_LIMITED", "Too many rapid commands (threshold: 30/min per client)", "Back off and retry with exponential backoff.", 429),
    ErrorCode("HANDSHAKE_FAILED", "Initial WebSocket handshake JSON was invalid or timed out", "Send a valid JSON object with 'app' field within 5 seconds of connecting.", 400),
    ErrorCode("UPGRADE_REQUIRED", "iOS client protocol version is below server minimum", "Update the iOS app to the latest version.", 426),
]

# ── Protocol Schemas ───────────────────────────────────────────────────────────


PROTOCOL_SCHEMAS: dict[str, Any] = {
    "envelope": {
        "inbound": {
            "id": "string (uuid-v4, generated by client if omitted)",
            "type": "command | intent | subscribe | unsubscribe | help",
            "app": "spatial-vibe | state-surveiller | pocket-architect (optional for command/help)",
            "payload": "dict — app-specific (see sections below)",
        },
        "outbound": {
            "id": "string (uuid-v4, generated by server)",
            "type": "ack | result | error | event | frame",
            "correlation_id": "string | null — echoes the inbound message id",
            "payload": "dict — response-specific",
        },
    },
    "handshake": {
        "client_sends": {'{"app": "spatial-vibe"}', '{"app": "state-surveiller"}', '{"app": "pocket-architect"}'},
        "server_responds": {
            "type": "ack",
            "payload.message": "Connected to godot-mcp mobile gateway v0.1.0",
            "payload.server_version": "0.1.0",
            "payload.client_id": "short-uuid (8 chars)",
            "payload.godot_bridge": "host:port",
        },
    },
    "message_types": {
        "command": "Execute a specific godot-mcp tool by name. payload: {tool: str, arguments: dict}",
        "intent": "High-level semantic action. payload depends on app — see app sections.",
        "subscribe": "Register for push channels. payload: {channels: [str]}. Supports wildcard with *.",
        "unsubscribe": "Unregister from push channels. payload: {channels: [str]}.",
        "help": "Request protocol help. Returns this document structure. payload: {} (empty).",
    },
    "response_types": {
        "ack": "Confirmation (subscribe, unsubscribe, handshake).",
        "result": "Synchronous command/intent result.",
        "error": "Error with error_code, message, recovery_hint.",
        "event": "Server-pushed event for subscribed channels.",
        "frame": "Server-pushed base64-encoded frame image.",
    },
    "apps": {
        "spatial-vibe": {
            "description": "Phone as spatial lens — ARKit anchors + voice → Godot scene manipulation",
            "intent_types": ["place_asset", "anchor_light", "wire_trigger", "move_node", "delete_node", "query_space"],
            "payload_schema": {"intent_type": "str", "transcript": "str (voice transcription)", "confidence": "0.0-1.0", "parameters": "dict"},
            "anchor_schema": {"anchor_id": "uuid", "transform": {"position", "rotation", "scale"}, "tracking_state": "normal|limited|unavailable"},
        },
        "state-surveiller": {
            "description": "Real-time multi-agent test monitoring + hot-fix intervention dashboard",
            "intent_types": ["reparent", "set_param", "force_restart", "kill_agent", "resume_loop"],
            "payload_schema": {"intervention_type": "str", "target_agent": "str", "parameters": "dict"},
            "subscription_channels": ["agent:*", "agent:{id}", "logs", "frames:{id}"],
        },
        "pocket-architect": {
            "description": "Minimalist prompt-to-asset generative deck",
            "intent_types": ["generate:environment", "generate:asset", "generate:ui_theme", "generate:behavior", "approve", "reject", "tweak"],
            "payload_schema": {"prompt": "str", "mode": "environment|asset|ui_theme|behavior|gdscript", "constraints": "dict", "outputs_requested": "[str]"},
            "output_types": ["screenshot", "video_clip", "scene_file", "gdscript"],
        },
    },
}

# ── Examples ───────────────────────────────────────────────────────────────────


EXAMPLES: list[dict[str, Any]] = [
    {
        "title": "WebSocket handshake + subscribe to logs",
        "app": "any",
        "code": [
            "# 1. Connect to ws://host:10993/mobile/v1",
            '# 2. Send: {"app": "state-surveiller"}',
            "# 3. Server responds with ack + client_id",
            '# 4. Send: {"type": "subscribe", "payload": {"channels": ["logs", "godot:status"]}}',
            "# 5. Receive push events every ~0.5-2s",
        ],
    },
    {
        "title": "Spatial Vibe: place an asset",
        "app": "spatial-vibe",
        "code": [
            '{"type": "intent", "app": "spatial-vibe",',
            ' "payload": {',
            '   "intent_type": "place_asset",',
            '   "transcript": "drop a tower against the wall",',
            '   "target_anchor": "wall_001",',
            '   "parameters": {',
            '     "asset_ref": "artifact:lowpoly_tower_01",',
            '     "material": {"color": "#4488ff", "roughness": 0.3}',
            "   }",
            " }}",
        ],
        "expected_response": '{"type": "result", "payload": {"success": true, "scene_tree_path": "/root/..."}}',
    },
    {
        "title": "State Surveiller: inject physics fix",
        "app": "state-surveiller",
        "code": [
            '{"type": "command", "app": "state-surveiller",',
            ' "payload": {',
            '   "tool": "modify-node",',
            '   "arguments": {',
            '     "node": "/root/World/Debris/debris_07",',
            '     "property": "mass",',
            '     "value": 0.5',
            "   }",
            " }}",
        ],
    },
    {
        "title": "Pocket Architect: generate GDScript",
        "app": "pocket-architect",
        "code": [
            '{"type": "intent", "app": "pocket-architect",',
            ' "payload": {',
            '   "prompt": "auto-flickering emission shader for sci-fi panels",',
            '   "mode": "gdscript",',
            '   "outputs_requested": ["gdscript"]',
            " }}",
        ],
        "expected_response": '{"type": "result", "payload": {"success": true, "data": {"code": "...", "mode": "gdscript"}}}',
    },
    {
        "title": "Direct tool call: query scene tree",
        "app": "any",
        "code": [
            '{"type": "command",',
            ' "payload": {"tool": "godot_read_scene_tree", "arguments": {}}}',
        ],
    },
    {
        "title": "Direct tool call: export to web",
        "app": "any",
        "code": [
            '{"type": "command",',
            ' "payload": {"tool": "godot_export_web", "arguments": {"output_path": "/tmp/preview.html"}}}',
        ],
    },
]

# ── Help Generator ─────────────────────────────────────────────────────────────


@dataclass
class MobileHelp:
    version: str = "0.1.0"
    title: str = "godot-mcp Mobile Gateway"
    description: str = "WebSocket + REST gateway for iOS mobile clients. Three apps supported: Spatial Vibe-Director (XR blueprinting), State-Surveiller & QA Crucible (agent monitoring), Pocket Vibe-Architect (generative steering)."
    endpoints: dict[str, str] = field(default_factory=lambda: {
        "ws://host:10993/mobile/v1": "Primary WebSocket endpoint (bidirectional, subscriptions, streaming)",
        "POST /mobile/v1/command": "REST fallback (stateless, no subscriptions)",
        "GET /mobile/v1/help": "This help document as JSON",
    })
    protocol: dict[str, Any] = field(default_factory=lambda: PROTOCOL_SCHEMAS)
    bridge_actions: list[dict[str, Any]] = field(default_factory=lambda: [asdict(a) for a in BRIDGE_ACTIONS])
    python_tools: list[dict[str, Any]] = field(default_factory=lambda: [asdict(t) for t in PYTHON_TOOLS])
    tool_chains: list[dict[str, Any]] = field(default_factory=lambda: [asdict(c) for c in TOOL_CHAINS])
    channels: list[dict[str, Any]] = field(default_factory=lambda: [asdict(c) for c in CHANNELS])
    error_codes: list[dict[str, Any]] = field(default_factory=lambda: [asdict(e) for e in ERROR_CODES])
    examples: list[dict[str, Any]] = field(default_factory=lambda: EXAMPLES)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "title": self.title,
            "description": self.description,
            "endpoints": self.endpoints,
            "protocol": self.protocol,
            "bridge_actions": self.bridge_actions,
            "python_tools": self.python_tools,
            "tool_chains": self.tool_chains,
            "channels": self.channels,
            "error_codes": self.error_codes,
            "examples": self.examples,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


_help_singleton: MobileHelp | None = None


def get_mobile_help() -> MobileHelp:
    global _help_singleton
    if _help_singleton is None:
        _help_singleton = MobileHelp()
    return _help_singleton


def generate_help_dict() -> dict[str, Any]:
    """Return the full help document as a plain dict — for REST endpoint use."""
    return get_mobile_help().to_dict()


def generate_help_json(indent: int = 2) -> str:
    """Return the full help document as formatted JSON."""
    return get_mobile_help().to_json(indent)


def get_endpoint_summary() -> str:
    """One-line endpoint summary for startup banner."""
    return (
        "Mobile gateway: ws://0.0.0.0:10993/mobile/v1 | "
        "REST: POST /mobile/v1/command | "
        "Help: GET /mobile/v1/help"
    )
