# Godot MCP Server — Reference

**Version**: 0.1.0 | **Port**: 10993 | **Framework**: FastMCP 3.2

## What Is FastMCP 3.2?

FastMCP is the Python framework for building MCP (Model Context Protocol) servers. Version 3.2 is the current fleet standard.

### Key Concepts

**Tool Registration**: Tools are registered at import time via the `@mcp.tool()` decorator. All tools must be imported (directly or via portmanteau re-exports) in the server's `__init__.py` or tools `__init__.py` chain before the server starts. No import = no tool exposed.

**SSE Transport**: FastMCP 3.2 uses Server-Sent Events (SSE) for MCP communication. The server exposes an `/sse` endpoint where MCP clients connect and receive streaming tool results.

**Context Injection**: MCP tools can receive a `Context` object injected by FastMCP at runtime. This provides access to the active sampling context, request metadata, and logging.

```python
from fastmcp import Context

async def my_tool(ctx: Context = None) -> dict:
    """Tool that uses MCP context."""
    if ctx:
        await ctx.info("Processing...")
    return {"success": True}
```

**Pydantic v2 Mandate**: FastMCP 3.2 is built on Pydantic v2. Legacy v1 patterns are prohibited:
- **Reject**: `model.dict()`, `model.json()`, `parse_obj()`
- **Require**: `model.model_dump()`, `model.model_dump_json()`, `model.model_validate()`

**CodeMode** (Experimental): BM25-powered discovery mode for agentic workflows. Import via:

```python
try:
    from fastmcp.experimental.transforms import CodeMode
except ImportError:
    CodeMode = None
```

Apply with `--agentic` CLI flag only. CodeMode takes zero arguments in 3.2.

## How godot-mcp Uses FastMCP

### from_fastapi() Pattern

godot-mcp uses the dual-mode pattern: FastAPI app with FastMCP mounted:

```python
from fastapi import FastAPI
from fastmcp import FastMCP

app = FastAPI(lifespan=lifespan)
mcp = FastMCP.from_fastapi(app, name="Godot MCP")
```

This automatically:
- Mounts `/sse` endpoint for MCP clients
- Mounts `/messages` endpoint for MCP message handling
- Preserves all existing FastAPI routes (`/api/v1/*`)
- Both MCP and REST can run simultaneously on the same port

### Tool Registration

All 12 tools are registered from `godot_mcp.tools` via the `register_all()` function:

```python
from godot_mcp.tools import register_all

register_all(mcp)
```

Each tool is registered with annotations:
- `READ_ONLY` = `{"readonly": True}` — safe for read operations
- `MUTATING` = `{"mutating": True}` — modifies Godot scene state

### Bridge Proxy (Optional)

The server can forward MCP tools from other servers via `MCP_BRIDGE_URLS`:

```powershell
$env:MCP_BRIDGE_URLS = "http://localhost:10966/sse,http://localhost:10944/sse"
```

This creates `add_provider(create_proxy(url))` for each URL, enabling cross-repo tool aggregation.

## 12 MCP Tools

### 1. godot_status

**Access**: READ_ONLY

Query the Godot engine for version, scene root node count, and current FPS.

```
Parameters: (none)
Returns: {success: bool, data: {godot_version: str, node_count: int, root_nodes: [...], fps: float, bridge_connected: bool}}
```

### 2. godot_import_stl

**Access**: MUTATING

Import an STL mesh into the current Godot scene as a MeshInstance3D. Reads binary STL vertex/normal data and creates an ArrayMesh.

```
Parameters:
  path (str, required):        Absolute path to STL file
  name (str, default "STL_Mesh"):    Node name
  scale (float, default 1.0):  Uniform scale factor (min 0.001)
  position_x/y/z (float):      Scene position (default 0.0)

Returns: {success: bool, data: {imported: bool, name: str, vertices: int, aabb: {size_x/y/z: float}}}
```

### 3. godot_load_velocity_field

**Access**: MUTATING

Load a CSV velocity field dataset (CFD/FluidX3D format) into the Godot scene as node metadata.

```
Parameters:
  csv_path (str, required):    Absolute path to CSV file (x,y,z,vx,vy,vz columns)
  name (str, default "VelocityField"): Node name for the data container

Returns: {success: bool, data: {loaded: bool, name: str, point_count: int, bbox: {min_x/y/z: float, max_x/y/z: float}}}
```

### 4. godot_spawn_particles

**Access**: MUTATING

Create a GPUParticles3D system with configurable emission box, count, color, and draw pass sphere mesh.

```
Parameters:
  count (int, default 1000):   Number of GPU particles (1–1,000,000)
  name (str, default "StreamlineParticles"): Node name
  color (str, default "#00aaff"): Hex particle color
  spread_x/y/z (float):        Emission box extents (default 5.0)

Returns: {success: bool, data: {spawned: bool, name: str, count: int, particle_system: str}}
```

### 5. godot_animate_streamlines

**Access**: MUTATING

Animate GPU particles along a previously loaded velocity field. Adjusts emission box to match velocity field bounds and sets velocity range from field vectors.

```
Parameters:
  velocity_field (str, default "VelocityField"):   Name of velocity field data node
  particle_system (str, default "StreamlineParticles"): Name of particle system node
  speed (float, default 1.0): Animation speed multiplier

Returns: {success: bool, data: {animated: bool, particle_system: str, velocity_field: str, speed_multiplier: float, point_count: int}}
```

### 6. godot_create_camera

**Access**: MUTATING

Create a Camera3D with orbit controls (mouse drag to rotate, scroll to zoom, Alt+drag to pan).

```
Parameters:
  name (str, default "MCP_Camera"):        Node name
  position_x/y/z (float):                  Camera position (default 0, 5, 10)
  look_at_x/y/z (float):                   Target point (default 0, 0, 0)
  fov (float, default 75.0):               Field of view in degrees (1–179)

Returns: {success: bool, data: {created: bool, name: str, fov: float, position: {x/y/z: float}}}
```

### 7. godot_add_light

**Access**: MUTATING

Add a dynamic light source to the Godot scene. Supports directional (sun), ambient (fill), and omni (point) lights.

```
Parameters:
  light_type (str, default "directional"):  "directional", "ambient", or "omni"
  name (str, default auto-generated):        Node name
  intensity (float, default 1.0):            Light energy (min 0.0)
  position_x/y/z (float, default 5.0):       Position (omni only)

Returns: {success: bool, data: {created: bool, name: str, type: str, intensity: float}}
```

### 8. godot_set_material

**Access**: MUTATING

Assign a StandardMaterial3D (PBR) to a mesh node. Sets albedo color and roughness.

```
Parameters:
  node (str, required):          Target MeshInstance3D node name
  color (str, default "#ffffff"): Hex albedo color
  roughness (float, default 0.5): PBR roughness (0 = mirror, 1 = matte)

Returns: {success: bool, data: {set: bool, node: str, color: str, roughness: float}}
```

### 9. godot_export_web

**Access**: MUTATING

Export the current scene to HTML5/WebAssembly. Requires HTML5 export templates installed. Falls back to CLI instructions if templates unavailable.

```
Parameters:
  output_path (str, default "user://export/web/index.html"): Output path (res:// or absolute)

Returns: {success: bool, data: {exported: bool, message: str, requires_cli: bool}}
```

### 10. godot_read_scene_tree

**Access**: READ_ONLY

Read the full Godot scene tree as a nested JSON structure with all children recursively.

```
Parameters: (none)
Returns: {success: bool, data: {scene_tree: {name: str, type: str, path: str, children: [...]}, node_count: int}}
```

### 11. godot_set_config

**Access**: MUTATING

Write a setting to the project.godot INI-style configuration file via ConfigFile API.

```
Parameters:
  section (str, required):   Config section name (e.g., "application", "rendering")
  key (str, required):       Config key to set
  value (str, required):     Config value

Returns: {success: bool, data: {updated: bool, section: str, key: str, value: str}}
```

### 12. godot_headless_verify

**Access**: READ_ONLY

Check whether the Godot engine is running in headless mode. Returns suggested CLI command for headless script execution.

```
Parameters:
  script (str, default "res://dev/mcp_verify.gd"): Path to a GDScript to verify

Returns: {success: bool, data: {headless: bool, script_path: str, message: str}}
```

## REST API Endpoints

### GET /api/v1/status

Server status including Godot engine and bridge connectivity.

**Response**:
```json
{
  "ok": true,
  "service": "godot-mcp",
  "version": "0.1.0",
  "godot": {
    "available": true,
    "path": "C:\\Program Files\\Godot\\godot.exe",
    "host": "127.0.0.1",
    "port": 9080,
    "ws_connected": true
  }
}
```

### POST /api/v1/control/tool

Execute a Godot MCP tool via REST (alternative to SSE transport).

**Request**:
```json
{
  "tool": "godot_status",
  "arguments": {}
}
```

**Response**:
```json
{
  "success": true,
  "message": "Tool executed",
  "tool": "godot_status",
  "data": {
    "godot_version": "4.4.0",
    "node_count": 12,
    "fps": 60.0
  },
  "arguments": {}
}
```

**Error (unknown tool)**:
```json
{
  "detail": "Unknown tool: bad_tool_name"
}
```
HTTP 400

### GET /api/v1/logs/stream

Server-Sent Events stream of all server logs. Ring buffer of 2000 most recent entries.

**Event format**:
```
data: 2026-05-18 12:34:56,789 - godot-mcp - INFO - Godot MCP startup — engine found at C:\Program Files\Godot\godot.exe
```

## MCP Client Configuration

### Claude Desktop

```json
{
  "mcpServers": {
    "godot": {
      "url": "http://localhost:10993/sse",
      "transport": "sse"
    }
  }
}
```

### Cursor

```json
{
  "mcpServers": {
    "godot": {
      "url": "http://localhost:10993/sse"
    }
  }
}
```

### Continue (VS Code Extension)

```json
{
  "mcpServers": {
    "godot": {
      "url": "http://localhost:10993/sse",
      "transport": "sse"
    }
  }
}
```

### Stdio Mode (Direct Process)

Stdio mode is available for clients that spawn the process directly:

```json
{
  "mcpServers": {
    "godot": {
      "command": "uv",
      "args": ["run", "python", "-m", "godot_mcp.server", "--mode", "stdio"]
    }
  }
}
```

## Tool Annotations

Each tool is registered with MCP annotations that inform AI clients about safety:

| Tool | Annotation | Rationale |
|------|-----------|-----------|
| `godot_status` | READ_ONLY | Reads engine state, no modifications |
| `godot_import_stl` | MUTATING | Creates MeshInstance3D in scene |
| `godot_load_velocity_field` | MUTATING | Creates data node with metadata |
| `godot_spawn_particles` | MUTATING | Creates GPU particle system |
| `godot_animate_streamlines` | MUTATING | Modifies particle material parameters |
| `godot_create_camera` | MUTATING | Creates camera node |
| `godot_add_light` | MUTATING | Creates light node |
| `godot_set_material` | MUTATING | Modifies mesh material |
| `godot_export_web` | MUTATING | Triggers build export |
| `godot_read_scene_tree` | READ_ONLY | Reads hierarchy, no modifications |
| `godot_set_config` | MUTATING | Writes to project.godot file |
| `godot_headless_verify` | READ_ONLY | Checks mode, no modifications |

## CodeMode (BM25 Discovery)

When started with the `--agentic` flag, the server enables CodeMode — an experimental FastMCP feature that uses BM25 (Best Match 25) ranking to discover relevant tools and code for the current agentic context:

```powershell
uv run python -m godot_mcp.server --mode dual --port 10993 --agentic
```

CodeMode is applied during CLI orchestration only. It is not active in the default server mode.

## Return Format Schema

All tools follow the standard fleet return format:

```json
{
  "success": true,
  "data": {
    // Tool-specific structured data
  }
}
```

**Error case**:
```json
{
  "success": false,
  "error": "Human-readable error message"
}
```

The `data` field contains structured data suitable for follow-up tool calls by AI agents. The `success` boolean allows quick success/failure branching.
