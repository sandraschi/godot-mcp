"""
FastMCP 3.x Unified Gateway for Godot 4.x engine control via TCP bridge.

Architecture:
  Godot 4.x Engine → TCP bridge (newline-JSON, port 9080) → MCP server → REST API + SSE + MCP-over-HTTP.

The server communicates with a running Godot editor or headless build over a
plain TCP socket. Godot must have the MCP bridge addon loaded to accept commands.
"""

import asyncio
import logging
import os
import shutil
import sys
import time as _time
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastmcp import FastMCP
from fastmcp.server import create_proxy
from pydantic import BaseModel, Field

try:
    from fastmcp.experimental.transforms import CodeMode
except ImportError:
    CodeMode = None

from godot_mcp.artifacts.routes import router as artifacts_router
from godot_mcp.fleet.routes import router as fleet_router
from godot_mcp.game_builder.routes import router as game_builder_router
from godot_mcp.itch.routes import router as itch_router
from godot_mcp.routes.logs import router as logs_router
from godot_mcp.services.activity_log import install_log_handler, log_activity, query_logs
from godot_mcp.services.godot_bridge import GODOT_HOST, GODOT_PATH, GODOT_PORT, get_bridge
from godot_mcp.services.mobile_command import MobileCommand, MobileResponse, get_dispatcher
from godot_mcp.services.mobile_help import generate_help_dict, get_endpoint_summary
from godot_mcp.services.ws_gateway import mobile_ws_handler, start_background_tasks, stop_background_tasks
from godot_mcp.steam.routes import router as steam_router
from godot_mcp.tools import register_all

logger = logging.getLogger("godot-mcp")

try:
    from importlib.metadata import version as _pkg_version

    __version__ = _pkg_version("godot-mcp")
except Exception:
    __version__ = "0.3.0"

# The ONE shared bridge instance (services.godot_bridge module singleton).
_bridge = get_bridge()

# ── Config ───────────────────────────────────────────────────────────────────

DEFAULT_PORT = 10993
DEFAULT_HOST = "0.0.0.0"  # noqa: S104


def _find_godot() -> str | None:
    """Locate godot.exe on the system."""
    if GODOT_PATH and Path(GODOT_PATH).is_file():
        return GODOT_PATH
    found = shutil.which("godot") or shutil.which("godot.exe")
    if found:
        return found
    # Check common install paths on Windows
    candidates = [
        r"C:\Program Files\Godot\godot.exe",
        r"C:\Program Files (x86)\Godot\godot.exe",
        str(Path.home() / "Godot" / "godot.exe"),
    ]
    for p in candidates:
        if Path(p).is_file():
            return p
    return None


# ── Lifespan ─────────────────────────────────────────────────────────────────

_state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    godot_exe = _find_godot()
    _state["godot_path"] = godot_exe or ""
    _state["godot_available"] = godot_exe is not None
    _state["godot_host"] = GODOT_HOST
    _state["godot_port"] = GODOT_PORT

    if godot_exe:
        logger.info("Godot MCP startup — engine found at %s", godot_exe)
    else:
        logger.warning("Godot MCP startup — godot.exe not found in PATH or GODOT_PATH. Set GODOT_PATH env var.")

    logger.info("Godot MCP TCP bridge: %s:%s", GODOT_HOST, GODOT_PORT)

    # Attempt bridge connection at startup (blocking socket — off the event loop)
    result = await asyncio.to_thread(_bridge.connect)
    if result["success"]:
        logger.info("Godot bridge connected: %s", result.get("data", {}))
    else:
        logger.warning("Godot bridge not available at startup: %s", result.get("error", "unknown"))

    # Start iOS mobile gateway background tasks (log push, status push)
    install_log_handler()
    log_activity("server", "Godot MCP started", level="INFO", meta={"version": __version__})
    start_background_tasks()
    logger.info(get_endpoint_summary())

    try:
        if _mcp_http_app is not None:
            # Run the FastMCP HTTP transport's lifespan (session manager/task group)
            async with _mcp_http_app.lifespan(_mcp_http_app):
                yield
        else:
            yield
    finally:
        stop_background_tasks()
        _bridge.disconnect()
        logger.info("Godot MCP shutdown — bridge disconnected")


# ── FastAPI App ──────────────────────────────────────────────────────────────

app = FastAPI(lifespan=lifespan)
_tauri_desktop = os.environ.get("GODOT_TAURI", "").lower() in ("1", "true", "yes")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:10993",
        "http://localhost:10993",
        "http://goliath:10993",
        "http://tauri.localhost",
        "https://tauri.localhost",
        "tauri://localhost",
    ],
    allow_origin_regex=r"https?://tauri\.localhost(:\d+)?" if _tauri_desktop else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register artifact marketplace routes
app.include_router(artifacts_router)
app.include_router(fleet_router)
app.include_router(game_builder_router)
app.include_router(itch_router)
app.include_router(steam_router)
app.include_router(logs_router)

mcp = FastMCP.from_fastapi(app, name="Godot MCP")

# ── Skills Provider (FastMCP 3.1+ Resource-based) ──────────────────────────

try:
    from godot_mcp.skills import get_skill_markdown, list_skills

    @mcp.resource("skill://{skill_name}/SKILL.md")
    async def skill_resource(skill_name: str) -> str:
        content = get_skill_markdown(skill_name)
        if content is None:
            raise ValueError(f"Skill not found: {skill_name}")
        return content

    @mcp.resource("skill://list")
    async def skill_list_resource() -> str:
        import json

        return json.dumps(list_skills())

    logger.info("Skills provider registered")
except Exception as e:
    logger.warning("Skills provider not loaded: %s", e)

# ── MCP Bridge Proxies ───────────────────────────────────────────────────────

_bridge_proxies = []
bridge_urls = os.getenv("MCP_BRIDGE_URLS", "")
for url in bridge_urls.split(","):
    url = url.strip()
    if url:
        try:
            mcp.add_provider(create_proxy(url))
            _bridge_proxies.append(url)
        except Exception:
            logger.warning("Failed to register MCP bridge proxy for %s", url)

# ── MCP Tools ────────────────────────────────────────────────────────────────

# 15 engine-control tools registered via core_tools.register():
#   godot_status            (READ_ONLY)  — engine version, node count, FPS
#   godot_import_stl        (MUTATING)   — import STL mesh from uploads
#   godot_import_glb        (MUTATING)   — import GLB/GLTF via GLTFDocument
#   godot_import_obj        (MUTATING)   — import Wavefront OBJ
#   godot_play_animation    (MUTATING)   — play/list GLB AnimationPlayer clips
#   godot_load_velocity_field (MUTATING) — load CSV velocity data into scene
#   godot_spawn_particles   (MUTATING)   — create GPU particle system
#   godot_animate_streamlines (MUTATING) — animate particles along velocity field
#   godot_create_camera     (MUTATING)   — create camera with orbit controls
#   godot_add_light         (MUTATING)   — add directional/ambient/omni light
#   godot_set_material      (MUTATING)   — set PBR material on mesh node
#   godot_export_web        (MUTATING)   — export scene to HTML5
#   godot_read_scene_tree   (READ_ONLY)  — dump scene hierarchy as JSON
#   godot_set_config        (MUTATING)   — write to project.godot config
#   godot_headless_verify   (READ_ONLY)  — check headless mode + CLI command

register_all(mcp)

# ── MCP-over-HTTP transport (mounted so --mode http/dual actually serves MCP) ─

_mcp_http_app = None
try:
    _mcp_http_app = mcp.http_app(path="/")
    app.mount("/mcp", _mcp_http_app)
    logger.info("MCP HTTP transport mounted at /mcp")
except Exception as e:
    logger.warning("MCP HTTP transport not mounted: %s", e)

# ── Skills REST endpoints ─────────────────────────────────────────────────────


@app.get("/api/v1/skills")
async def list_skills_api():
    """List all available skills."""
    try:
        from godot_mcp.skills import list_skills

        return {"success": True, "skills": list_skills()}
    except Exception as e:
        return {"success": False, "skills": [], "error": str(e)}


@app.get("/api/v1/skills/{skill_name}")
async def get_skill_api(skill_name: str):
    """Get the content of a specific skill."""
    try:
        from godot_mcp.skills import get_skill_markdown

        content = get_skill_markdown(skill_name)
        if content is None:
            return {"success": False, "error": f"Skill not found: {skill_name}"}
        return {"success": True, "name": skill_name, "content": content}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Fleet-standard health / diagnostics ────────────────────────────────────────

_server_start = _time.time()

_TOOL_COUNT = 49
_TOOL_NAMES = [
    "godot_status", "godot_version", "godot_open_project", "godot_save_project",
    "godot_import_glb", "godot_import_stl", "godot_import_obj", "godot_export_release",
    "godot_export_html5", "godot_set_scene", "godot_run_scene", "godot_stop_scene",
    "godot_add_node", "godot_modify_node", "godot_remove_node",
    "itch_butler_status", "itch_push_build", "itch_preview_build", "itch_list_builds",
    "itch_channel_history",
    "steam_status", "steam_set_app_id", "steam_stage_build", "ship_to_steam_prerelease",
    "ship_to_steam_release", "ship_to_steam",
    "fleet_exchange_status", "fleet_import_from_exchange",
    "fleet_worldlabs_get_world", "fleet_worldlabs_stage_mesh",
    "fleet_worldlabs_stage_splat", "fleet_worldlabs_import_mesh",
    "design_game", "generate_game_worlds", "compose_game_scene",
    "generate_game_logic", "export_and_ship", "build_game",
    "ship_windows_steam_beta", "ship_windows_steam_release",
    "sample_text", "generate_image",
    "mcp_bridge_call", "mcp_bridge_list_servers",
    "run_workflow", "list_workflows", "get_workflow",
]


@app.get("/api/health")
@app.get("/api/v1/health")
async def fleet_health():
    return {
        "status": "ok",
        "server": "godot-mcp",
        "version": __version__,
        "uptime_seconds": int(_time.time() - _server_start),
        "tool_count": _TOOL_COUNT,
    }


@app.get("/api/v1/diagnostics")
async def fleet_diagnostics():
    return {
        "status": "ok",
        "server": "godot-mcp",
        "version": __version__,
        "uptime_seconds": int(_time.time() - _server_start),
        "tool_count": _TOOL_COUNT,
        "tools": [{"name": n} for n in _TOOL_NAMES],
        "system": {"windows": sys.platform == "win32"},
        "errors": [],
    }


# ── REST API ──────────────────────────────────────────────────────────────────


@app.get("/api/v1/status")
async def api_status():
    """Server status including Godot engine and TCP bridge info."""
    from godot_mcp.fleet.service import fleet_exchange_status
    from godot_mcp.itch.service import itch_status
    from godot_mcp.steam.service import steam_status

    itch = await asyncio.to_thread(itch_status)
    fleet = await asyncio.to_thread(fleet_exchange_status)
    steam = await asyncio.to_thread(steam_status)
    return {
        "ok": True,
        "service": "godot-mcp",
        "version": __version__,
        "godot": {
            "available": _state.get("godot_available", False),
            "path": _state.get("godot_path", ""),
            "host": _bridge.host,
            "port": _bridge.port,
            "bridge_connected": _bridge.connected,
            # legacy key kept for webapp/mobile compatibility
            "ws_connected": _bridge.connected,
        },
        "itch": itch,
        "steam": steam,
        "fleet": fleet,
    }


@app.get("/api/capabilities")
async def api_capabilities():
    """Runtime feature gating for the webapp (fleet capability introspection standard)."""
    from godot_mcp.itch import butler
    from godot_mcp.sampling.service import sampling_capabilities

    butler_exe = await asyncio.to_thread(butler.find_butler)
    steam_url = os.getenv("STEAM_MCP_URL", "http://127.0.0.1:11020")
    worldlabs_url = os.getenv("WORLDLABS_BRIDGE_URL", "http://127.0.0.1:10865")
    return {
        "service": "godot-mcp",
        "version": __version__,
        "capabilities": {
            "godot_engine": _state.get("godot_available", False),
            "godot_bridge_connected": _bridge.connected,
            "itch_butler": butler_exe is not None,
            "itch_api_key": bool(os.getenv("BUTLER_API_KEY", "").strip()),
            "steam_mcp_url": steam_url,
            "worldlabs_url": worldlabs_url,
            "sampling": sampling_capabilities(),
            "mcp_http": _mcp_http_app is not None,
            "mobile_gateway": True,
            "logs": True,
        },
    }


# ── Files listing ─────────────────────────────────────────────────────────────


_FILES_DIR = Path(os.getenv("GODOT_MCP_UPLOADS_DIR", str(Path(__file__).parent.parent.parent / "uploads")))
_OUTPUTS_DIR = Path(os.getenv("GODOT_MCP_OUTPUTS_DIR", str(Path(__file__).parent.parent.parent / "outputs")))


@app.get("/api/v1/files")
async def list_files():
    """List uploaded files and output files."""
    uploads = []
    outputs = []
    if _FILES_DIR.is_dir():
        for f in sorted(_FILES_DIR.iterdir()):
            if f.is_file():
                uploads.append({"name": f.name, "size_kb": round(f.stat().st_size / 1024, 1)})
    if _OUTPUTS_DIR.is_dir():
        for f in sorted(_OUTPUTS_DIR.iterdir()):
            if f.is_file():
                outputs.append({"name": f.name, "size_kb": round(f.stat().st_size / 1024, 1)})
    return {"uploads": uploads, "outputs": outputs}


@app.get("/api/v1/download/{file_name}")
async def download_file(file_name: str):
    """Download a file from uploads or outputs."""
    for base in [_FILES_DIR, _OUTPUTS_DIR]:
        target = base / file_name
        if target.is_file():
            from fastapi.responses import FileResponse

            return FileResponse(str(target))
    raise HTTPException(404, "File not found")


# ── REST API — Tool Bridge ────────────────────────────────────────────────────


class ToolRequest(BaseModel):
    tool: str = Field(description="Tool name (godot_* or itch_* / steam_* / ship_to_*)")
    arguments: dict = Field(default_factory=dict, description="Tool arguments as a dict")


async def _run_python_tool(tool: str, arguments: dict) -> dict:
    from godot_mcp.itch import service as itch_service

    if tool == "itch_status":
        return await asyncio.to_thread(itch_service.itch_status)
    if tool == "godot_export_release":
        return await asyncio.to_thread(itch_service.godot_export_release_tool, **arguments)
    if tool == "itch_push_preview":
        return await asyncio.to_thread(itch_service.itch_push_preview, **arguments)
    if tool == "itch_push":
        return await asyncio.to_thread(itch_service.itch_push, **arguments)
    if tool == "itch_latest_version":
        return await asyncio.to_thread(itch_service.itch_latest_version, **arguments)
    if tool == "ship_to_itch":
        return await asyncio.to_thread(itch_service.ship_to_itch, **arguments)
    if tool in {
        "steam_status",
        "steam_checklist",
        "steam_monetization_guide",
        "steam_stage_build",
        "ship_to_steam_prerelease",
        "ship_to_steam_release",
        "ship_to_steam",
    }:
        from godot_mcp.steam import service as steam_service

        handlers = {
            "steam_status": steam_service.steam_status,
            "steam_checklist": steam_service.steam_checklist,
            "steam_monetization_guide": steam_service.steam_monetization_guide,
            "steam_stage_build": steam_service.stage_windows_build,
            "ship_to_steam_prerelease": steam_service.steam_upload_prerelease,
            "ship_to_steam_release": steam_service.steam_upload_release,
            "ship_to_steam": steam_service.ship_to_steam,
        }
        return await asyncio.to_thread(handlers[tool], **arguments)
    if tool == "fleet_exchange_status":
        from godot_mcp.fleet.service import fleet_exchange_status

        return await asyncio.to_thread(fleet_exchange_status)
    if tool == "fleet_import_from_exchange":
        from godot_mcp.fleet.service import fleet_import_from_exchange

        return await asyncio.to_thread(fleet_import_from_exchange, **arguments)
    if tool == "fleet_worldlabs_get_world":
        from godot_mcp.fleet.service import fleet_worldlabs_get_world

        return await asyncio.to_thread(fleet_worldlabs_get_world, **arguments)
    if tool == "fleet_worldlabs_stage_mesh":
        from godot_mcp.fleet.service import fleet_worldlabs_stage_mesh

        return await asyncio.to_thread(fleet_worldlabs_stage_mesh, **arguments)
    if tool == "fleet_worldlabs_stage_splat":
        from godot_mcp.fleet.service import fleet_worldlabs_stage_splat

        return await asyncio.to_thread(fleet_worldlabs_stage_splat, **arguments)
    if tool == "fleet_worldlabs_import_mesh":
        from godot_mcp.fleet.service import fleet_worldlabs_import_mesh

        return await asyncio.to_thread(fleet_worldlabs_import_mesh, **arguments)
    if tool == "workflow_list":
        from godot_mcp.workflows.tools import workflow_list

        return await workflow_list()
    if tool == "workflow_run":
        from godot_mcp.workflows.tools import workflow_run

        return await workflow_run(**arguments)
    if tool == "design_game":
        from godot_mcp.game_builder import service as gb_service

        return await gb_service.service_design_game(arguments.get("game_concept", ""))
    if tool == "generate_game_worlds":
        from godot_mcp.game_builder import service as gb_service

        return await gb_service.service_generate_worlds(
            arguments.get("game_plan_json", ""),
            arguments.get("worldlabs_url", "http://127.0.0.1:10865"),
        )
    if tool == "compose_game_scene":
        from godot_mcp.game_builder import service as gb_service

        return await gb_service.service_compose_scene(
            arguments.get("game_plan_json", ""),
            arguments.get("worlds_result_json", ""),
        )
    if tool == "generate_game_logic":
        from godot_mcp.game_builder import service as gb_service

        return await gb_service.service_generate_logic(
            arguments.get("game_plan_json", ""),
            arguments.get("game_project_path", ""),
        )
    if tool == "export_and_ship":
        from godot_mcp.game_builder import service as gb_service

        return await gb_service.service_export_and_ship(
            arguments.get("game_plan_json", ""),
            arguments.get("game_project_path", ""),
            arguments.get("itch_target", ""),
            arguments.get("channel", "html"),
        )
    if tool == "build_game":
        from godot_mcp.game_builder import service as gb_service

        return await gb_service.service_build_game(
            arguments.get("game_concept", ""),
            arguments.get("worldlabs_url", "http://127.0.0.1:10865"),
            arguments.get("game_project_path", ""),
            arguments.get("ship", False),
            arguments.get("itch_target", ""),
        )
    if tool == "prompt_execute":
        from godot_mcp.prompts.tools import execute_prompt

        return await execute_prompt(
            arguments.get("prompt_id", ""),
            arguments.get("params", {}),
        )
    if tool == "prefab_apply":
        from godot_mcp.prefabs.tools import apply_prefab

        return await apply_prefab(
            arguments.get("prefab", ""),
            arguments.get("params", {}),
        )
    if tool == "mcpb_build":
        from godot_mcp.mcpb.tools import build_mcpb

        return await build_mcpb(
            arguments.get("name", ""),
            arguments.get("description", ""),
            arguments.get("tool_sequence", []),
        )
    if tool == "mcpb_inspect":
        from godot_mcp.mcpb.tools import inspect_mcpb

        return inspect_mcpb(arguments.get("path", ""))
    raise HTTPException(400, f"Unknown tool: {tool}")


PYTHON_TOOLS = {
    "itch_status",
    "godot_export_release",
    "itch_push_preview",
    "itch_push",
    "itch_latest_version",
    "ship_to_itch",
    "steam_status",
    "steam_checklist",
    "steam_monetization_guide",
    "steam_stage_build",
    "ship_to_steam_prerelease",
    "ship_to_steam_release",
    "ship_to_steam",
    "fleet_exchange_status",
    "fleet_import_from_exchange",
    "fleet_worldlabs_get_world",
    "fleet_worldlabs_stage_mesh",
    "fleet_worldlabs_stage_splat",
    "fleet_worldlabs_import_mesh",
    "workflow_list",
    "workflow_run",
    "design_game",
    "generate_game_worlds",
    "compose_game_scene",
    "generate_game_logic",
    "export_and_ship",
    "build_game",
    "prompt_execute",
    "prefab_apply",
    "mcpb_build",
    "mcpb_inspect",
}


@app.post("/api/v1/control/tool")
async def execute_tool(req: ToolRequest):
    """Execute a Godot MCP tool via REST bridge."""
    action_map = {
        "godot_status": (None, "status"),
        "godot_import_stl": (None, "import_stl"),
        "godot_load_velocity_field": (None, "load_velocity_field"),
        "godot_spawn_particles": (None, "spawn_particles"),
        "godot_animate_streamlines": (None, "animate_streamlines"),
        "godot_create_camera": (None, "create_camera"),
        "godot_add_light": (None, "add_light"),
        "godot_set_material": (None, "set_material"),
        "godot_export_web": (None, "export_web"),
        "godot_import_glb": (None, "import_glb"),
        "godot_import_obj": (None, "import_obj"),
        "godot_play_animation": (None, "play_animation"),
        "godot_read_scene_tree": (None, "read_scene_tree"),
        "godot_set_config": (None, "set_config"),
        "godot_headless_verify": (None, "headless_verify"),
        "godot_add_node": (None, "add_node"),
        "godot_remove_node": (None, "remove_node"),
        "godot_modify_node": (None, "modify_node"),
        "godot_save_scene": (None, "save_scene"),
    }
    if req.tool in PYTHON_TOOLS:
        try:
            result = await _run_python_tool(req.tool, req.arguments)
            success = result.get("success", False)
            log_activity(
                "tool_call",
                f"{req.tool} ({'ok' if success else 'fail'})",
                level="INFO" if success else "ERROR",
                meta={"tool": req.tool, "arguments": req.arguments},
            )
            return {
                "success": success,
                "message": "Tool executed",
                "tool": req.tool,
                "data": result.get("data", result),
                "error": result.get("error"),
                "arguments": req.arguments,
            }
        except HTTPException:
            raise
        except Exception as e:
            log_activity("tool_call", f"{req.tool} (error: {e})", level="ERROR", meta={"tool": req.tool})
            return {"success": False, "message": str(e), "tool": req.tool, "arguments": req.arguments}

    if req.tool not in action_map:
        raise HTTPException(400, f"Unknown tool: {req.tool}")
    try:
        if not _bridge.connected:
            conn_result = await asyncio.to_thread(_bridge.connect)
            if not conn_result["success"]:
                return {"success": False, "message": conn_result.get("error", "Bridge not connected"), "tool": req.tool}

        action = action_map[req.tool][1]
        timeout = 300.0 if action == "export_web" else 10.0
        result = await asyncio.to_thread(_bridge.send, action, req.arguments, timeout)
        success = result.get("success", False)
        log_activity(
            "tool_call",
            f"{req.tool} ({'ok' if success else 'fail'})",
            level="INFO" if success else "ERROR",
            meta={"tool": req.tool},
        )
        return {
            "success": success,
            "message": "Tool executed",
            "tool": req.tool,
            "data": result.get("data", {}),
            "arguments": req.arguments,
        }
    except HTTPException:
        raise
    except Exception as e:
        log_activity("tool_call", f"{req.tool} (error: {e})", level="ERROR", meta={"tool": req.tool})
        return {"success": False, "message": str(e), "tool": req.tool, "arguments": req.arguments}


# ── Legacy SSE log stream (feeds from activity log) ──────────────────────────


@app.get("/api/v1/logs/stream")
async def stream_logs():
    async def gen():
        snapshot = query_logs(limit=200, offset=0, sort="desc")
        for entry in reversed(snapshot["entries"]):
            line = f"{entry['timestamp']} [{entry['level']}] {entry['kind']}: {entry['detail']}"
            yield f"data: {line}\n\n"
        last_id = snapshot["entries"][0]["id"] if snapshot["entries"] else "0"
        while True:
            tail = query_logs(limit=50, after_id=last_id, sort="asc")
            for entry in tail["entries"]:
                line = f"{entry['timestamp']} [{entry['level']}] {entry['kind']}: {entry['detail']}"
                yield f"data: {line}\n\n"
                last_id = entry["id"]
            await asyncio.sleep(1)

    return StreamingResponse(gen(), media_type="text/event-stream")


# ── iOS Mobile Gateway ────────────────────────────────────────────────────────


@app.websocket("/mobile/v1")
async def mobile_websocket(websocket: WebSocket):
    """WebSocket gateway for iOS mobile clients (Spatial Vibe / State Surveiller / Pocket Architect).

    Protocol:
      Handshake: send JSON {"app": "spatial-vibe" | "state-surveiller" | "pocket-architect"}
      Messages:  {"type": "command" | "intent" | "subscribe" | "unsubscribe", "payload": {...}}
    """
    await mobile_ws_handler(websocket)


@app.get("/mobile/v1/help")
async def mobile_help():
    """Full protocol reference for iOS mobile clients — machine-readable JSON."""
    return generate_help_dict()


@app.post("/mobile/v1/command")
async def mobile_command_fallback(cmd: MobileCommand):
    """REST fallback for iOS mobile commands (stateless, no subscriptions)."""
    dispatcher = get_dispatcher()
    result = await dispatcher.dispatch(cmd)
    return MobileResponse(
        type="result" if result.success else "error",
        correlation_id=cmd.id,
        payload=result.model_dump(),
    ).model_dump()


# ── Addon Install ─────────────────────────────────────────────────────────────


class AddonInstallRequest(BaseModel):
    project_path: str = Field(description="Absolute path to the Godot project root (contains project.godot)")


BRIDGE_GD_PATH = Path(__file__).parent / "bridge" / "mcp_bridge.gd"
PLUGIN_CFG_CONTENT = """[plugin]
name=MCP Bridge
description=TCP server for MCP commands
author=godot-mcp
version=0.3.0
script=mcp_bridge.gd
"""


@app.post("/api/v1/addon/install")
async def install_addon(req: AddonInstallRequest):
    """Install the Godot MCP bridge addon into a target project."""
    project = Path(req.project_path).resolve()
    addon_dir = project / "addons" / "mcp_bridge"

    if not (project / "project.godot").is_file():
        raise HTTPException(400, f"Not a Godot project: no project.godot found at {project}")

    if not BRIDGE_GD_PATH.is_file():
        raise HTTPException(500, f"Bridge GDScript not found at {BRIDGE_GD_PATH}")

    addon_dir.mkdir(parents=True, exist_ok=True)

    import shutil

    shutil.copy2(str(BRIDGE_GD_PATH), str(addon_dir / "mcp_bridge.gd"))
    (addon_dir / "plugin.cfg").write_text(PLUGIN_CFG_CONTENT, encoding="utf-8")

    log_activity("addon_install", f"Addon installed to {addon_dir}", level="INFO")
    return {
        "success": True,
        "addon_path": str(addon_dir),
        "message": f"MCP Bridge addon installed to {addon_dir}. Add it as an Autoload in Project > Project Settings > Autoload.",
    }


# ── Settings (persist) ────────────────────────────────────────────────────────


class SettingsUpdate(BaseModel):
    godot_path: str = ""
    godot_host: str = "127.0.0.1"
    godot_ws_port: int = 9080


STATE_PATH = Path.home() / ".godot-mcp" / "settings.json"


def _load_settings() -> dict:
    if STATE_PATH.is_file():
        try:
            import json

            return json.loads(STATE_PATH.read_text())
        except Exception:
            return {}
    return {}


def _save_settings(data: dict):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    import json

    STATE_PATH.write_text(json.dumps(data, indent=2))


@app.get("/api/v1/settings")
async def get_settings():
    return _load_settings()


@app.put("/api/v1/settings")
async def save_settings(req: SettingsUpdate):
    data = req.model_dump()
    _save_settings(data)
    # Drop the current bridge connection so the next connect() picks up the
    # new host/port/path from ~/.godot-mcp/settings.json (env still wins).
    _bridge.disconnect()
    log_activity("settings", "Settings saved (bridge will reconnect with new config)", level="INFO", meta=data)
    return {"success": True, "message": "Settings saved. Bridge reconnects with the new config on next use."}


# ── Entry point ──────────────────────────────────────────────────────────────


async def _run_stdio():
    await mcp.run_stdio_async()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Godot MCP Server")
    parser.add_argument("--mode", choices=["stdio", "http", "dual"], default="stdio")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--agentic", action="store_true", help="Enable CodeMode BM25 discovery")
    args = parser.parse_args()

    if args.agentic and CodeMode is not None:
        mcp._transforms.append(CodeMode())

    if args.mode == "stdio":
        asyncio.run(_run_stdio())
    else:
        logger.info("Starting Godot MCP on %s:%s", args.host, args.port)
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
