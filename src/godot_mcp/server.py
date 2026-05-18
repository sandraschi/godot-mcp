"""
FastMCP 3.2 Unified Gateway for Godot 4.0 engine control via WebSocket bridge.

Architecture:
  Godot 4.0 Engine → WebSocket bridge (port 9080) → MCP server → REST API + SSE.

The server communicates with a running Godot editor or headless build via
WebSocket. Godot must have the MCP plugin/addon loaded to accept commands.
"""

import asyncio
import collections
import logging
import os
import shutil
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastmcp import FastMCP
from fastmcp.server import create_proxy
from pydantic import BaseModel, Field

try:
    from fastmcp.experimental.transforms import CodeMode
except ImportError:
    CodeMode = None

from godot_mcp.services.godot_bridge import GODOT_HOST, GODOT_PATH, GODOT_PORT, GodotBridge
from godot_mcp.tools import register_all

logger = logging.getLogger("godot-mcp")

_bridge = GodotBridge()

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
    _state["ws_connected"] = False

    if godot_exe:
        logger.info("Godot MCP startup — engine found at %s", godot_exe)
    else:
        logger.warning("Godot MCP startup — godot.exe not found in PATH or GODOT_PATH. Set GODOT_PATH env var.")

    logger.info("Godot MCP TCP bridge: %s:%s", GODOT_HOST, GODOT_PORT)

    # Attempt bridge connection at startup
    result = _bridge.connect()
    if result["success"]:
        _state["ws_connected"] = True
        logger.info("Godot bridge connected: %s", result.get("data", {}))
    else:
        logger.warning("Godot bridge not available at startup: %s", result.get("error", "unknown"))

    yield

    _bridge.disconnect()
    logger.info("Godot MCP shutdown — bridge disconnected")


# ── FastAPI App ──────────────────────────────────────────────────────────────

app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

mcp = FastMCP.from_fastapi(app, name="Godot MCP")

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

# 12 tools registered via core_tools.register():
#   godot_status            (READ_ONLY)  — engine version, node count, FPS
#   godot_import_stl        (MUTATING)   — import STL mesh from uploads
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


# ── REST API ──────────────────────────────────────────────────────────────────


@app.get("/api/v1/status")
async def api_status():
    """Server status including Godot engine and WebSocket bridge info."""
    return {
        "ok": True,
        "service": "godot-mcp",
        "version": "0.1.0",
        "godot": {
            "available": _state.get("godot_available", False),
            "path": _state.get("godot_path", ""),
            "host": _state.get("godot_host", GODOT_HOST),
            "port": _state.get("godot_port", GODOT_PORT),
            "ws_connected": _state.get("ws_connected", False),
        },
    }


# ── REST API — Tool Bridge ────────────────────────────────────────────────────


class ToolRequest(BaseModel):
    tool: str = Field(
        description="Tool name: godot_status, godot_import_stl, godot_load_velocity_field, godot_spawn_particles, godot_animate_streamlines, godot_create_camera, godot_add_light, godot_set_material, godot_export_web, godot_read_scene_tree, godot_set_config, godot_headless_verify"
    )
    arguments: dict = Field(default_factory=dict, description="Tool arguments as a dict")


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
        "godot_read_scene_tree": (None, "read_scene_tree"),
        "godot_set_config": (None, "set_config"),
        "godot_headless_verify": (None, "headless_verify"),
    }
    if req.tool not in action_map:
        raise HTTPException(400, f"Unknown tool: {req.tool}")
    try:
        if not _bridge.connected:
            conn_result = _bridge.connect()
            if not conn_result["success"]:
                return {"success": False, "message": conn_result.get("error", "Bridge not connected"), "tool": req.tool}

        result = _bridge.send(action_map[req.tool][1], req.arguments)
        return {
            "success": result.get("success", False),
            "message": "Tool executed",
            "tool": req.tool,
            "data": result.get("data", {}),
            "arguments": req.arguments,
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"success": False, "message": str(e), "tool": req.tool, "arguments": req.arguments}


# ── Log Ring Buffer ──────────────────────────────────────────────────────────

LOG_RING = collections.deque(maxlen=2000)


class LogHandler(logging.Handler):
    def emit(self, record):
        LOG_RING.append(self.format(record))


_log_handler = LogHandler()
_log_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logger.addHandler(_log_handler)


@app.get("/api/v1/logs/stream")
async def stream_logs():
    async def gen():
        for line in list(LOG_RING):
            yield f"data: {line}\n\n"
        idx = len(LOG_RING)
        while True:
            if idx < len(LOG_RING):
                yield f"data: {LOG_RING[idx]}\n\n"
                idx += 1
            await asyncio.sleep(0.1)

    return StreamingResponse(gen(), media_type="text/event-stream")


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
