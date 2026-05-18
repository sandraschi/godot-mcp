# Godot MCP — Architecture

**Version**: 0.1.0 | **Ports**: Backend 10993, Frontend 10992, Bridge 9080

## System Overview

```
┌─────────────────────┐     TCP (9080)     ┌──────────────────────┐     HTTP/SSE     ┌──────────────────────┐
│   Godot 4 Engine    │ ◄──────────────► │   Python MCP Server   │ ◄──────────────► │   React Webapp       │
│   (Desktop/Headless) │    JSON/NDJSON   │   FastMCP 3.2+FastAPI  │   REST + Proxy    │   Vite+TS+Tailwind   │
│   Port: 9080        │                   │   Port: 10993         │                   │   Port: 10992        │
└─────────────────────┘                   └──────────────────────┘                   └──────────────────────┘
        │                                          │                                          │
        │ GDScript                                 │ Python 3.12+                             │ TypeScript
        │ mcp_bridge.gd                            │ godot_mcp.server                         │ Vite dev server
        │ (Autoload)                               │ godot_mcp.tools                          │ React 19
        │                                          │ godot_mcp.services                       │ Tailwind CSS 3.4
        │                                          │                                          │
        ▼                                          ▼                                          ▼
   Scene Tree                              MCP Clients                              Fleet Dashboard
   Nodes, Materials                        (Claude Desktop, Cursor,                 (5 pages)
   GPU Particles, Cameras                  Continue, etc.)
```

## Component Breakdown

### 1. Godot Bridge (GDScript TCPServer — Port 9080)

Located at `src/godot_mcp/bridge/mcp_bridge.gd`. This is an **Autoload** script that runs inside the Godot engine.

**Purpose**: Accept JSON commands over TCP and execute them against the Godot scene tree.

**Key characteristics**:
- Listens on port 9080 via `TCPServer.new()`
- Single connection at a time (one MCP server client)
- Sends JSON handshake on connection: `{"type": "handshake", "version": "0.1.0", "godot_version": {"major": 4, ...}, "ready": true}`
- Processes incoming JSON messages delimited by newlines
- Dispatches to 15 action handlers (`match action` block)
- Returns JSON responses: `{"type": "response", "request_id": "...", "success": true, "data": {...}}`

**Placement**: Must be added as an Autoload in your Godot project's `project.godot`:
```ini
[autoload]
MCPBridge="*res://mcp_bridge.gd"
```

### 2. Python Backend (FastAPI + FastMCP 3.2 — Port 10993)

Located at `src/godot_mcp/server.py`. The central orchestration layer.

**Subcomponents**:

| Module | File | Purpose |
|--------|------|---------|
| Server | `src/godot_mcp/server.py` | FastAPI app with lifespan, MCP registration, REST endpoints |
| Tools | `src/godot_mcp/tools/core_tools.py` | 12 MCP tool functions with decorator registration |
| Bridge Client | `src/godot_mcp/services/godot_bridge.py` | TCP socket client connecting to GDScript bridge |

**FastAPI app** (`app`):
- Lifespan handler: auto-detects Godot, connects bridge at startup, disconnects at shutdown
- CORS middleware: allows all origins for development
- REST endpoints: `/api/v1/status`, `/api/v1/control/tool`, `/api/v1/logs/stream`

**FastMCP integration** (`mcp`):
- Created via `FastMCP.from_fastapi(app, name="Godot MCP")` — mounts `/sse` and `/messages` endpoints
- 12 tools registered via `register_all(mcp)` from `godot_mcp.tools`
- Optional CodeMode for BM25 discovery (`--agentic` flag)
- Optional bridge proxies via `MCP_BRIDGE_URLS` env var

**Dual mode**: The server supports three modes:
- `stdio`: MCP stdio transport (for direct client integration)
- `http`: FastAPI REST + SSE endpoints
- `dual`: Both — the default, used by `just serve` and `start.ps1`

### 3. React Webapp (Vite + TypeScript + Tailwind — Port 10992)

Located at `webapp/`. Fleet-standard 5-page dashboard.

**Pages**:
- Dashboard — Godot engine status, quick actions, scene summary
- Models — Upload/download STL, OBJ, velocity field files
- Logs — Live SSE log viewer with filter, pause, export
- Settings — Godot path, WebSocket port, engine config
- Help — Godot 4.0 reference, fleet pipeline, tools documentation

**Stack**:
- Vite 6 + React 19 + TypeScript
- Tailwind CSS 3.4 for styling
- Biome for TypeScript/JSX linting
- Proxies `/api` and `/sse` to backend port 10993

## Communication Flow

### TCP Handshake Sequence

```
Python Server                    Godot Bridge (GDScript)
    │                                    │
    │──── TCP connect (127.0.0.1:9080) ──►│
    │                                    │
    │◄── {"type":"handshake", ──────────│
    │      "version":"0.1.0",           │
    │      "godot_version":{"major":4,  │
    │        "minor":4,"patch":0},      │
    │      "ready":true}                │
    │                                    │
    │  [Connected state stored]          │
```

### JSON Request/Response Protocol

**Request** (Python → Godot):
```json
{
  "action": "status",
  "params": {},
  "request_id": "py_1"
}
```

**Response** (Godot → Python):
```json
{
  "type": "response",
  "request_id": "py_1",
  "success": true,
  "data": {
    "godot_version": "4.4.0",
    "node_count": 12,
    "fps": 60.0
  }
}
```

**Error Response**:
```json
{
  "type": "response",
  "request_id": "py_2",
  "success": false,
  "error": "File not found: C:/data/mesh.stl"
}
```

Messages are **newline-delimited JSON** (NDJSON). Each message is a single JSON object followed by `\n`.

### MCP Tool Call Flow

```
MCP Client (Claude Desktop)
    │
    │ POST /sse (SSE stream)
    ▼
FastMCP Server
    │
    │ @mcp.tool() → core_tools.py function
    ▼
GodotBridge.send("status", {})
    │
    │ TCP socket → JSON command
    ▼
GDScript mcp_bridge.gd
    │
    │ _cmd_status(request_id, params)
    │ Engine.get_version_info()
    │ get_tree().get_root()
    ▼
JSON response → TCP → GodotBridge → MCP tool → SSE → Client
```

## Scene Tree Operations

The bridge manipulates the Godot scene tree through these GDScript operations:

1. **Container pattern**: Nodes are organized into named containers (`STL_Imports`, `Velocity_Fields`, `Particle_Systems`, `Cameras`, `Lights`, `MCP_Scene`)
2. **Meta data**: Velocity field data is stored as node metadata (`set_meta`/`get_meta`)
3. **Recursive find**: `_find_node_by_name()` walks the entire tree
4. **Resource creation**: Meshes, materials, lights, and cameras are created procedurally via `new()` + `add_child()`

## Cross-Repo Pipeline

```
qcad-mcp (DXF/STL)
    │ plan_extrude → STL file
    │
    ├──► freecad-mcp (BIM/IFC)
    │      │ geometry → STL
    │      │
    │      └──► godot-mcp godot_import_stl
    │             │ MeshInstance3D in scene
    │             │
    ├──► FluidX3D (GPU CFD)
    │      │ velocity field → CSV
    │      │
    │      └──► godot-mcp godot_load_velocity_field
    │             │ PackedVector3Array in node metadata
    │             │
    │             └──► godot_spawn_particles
    │             └──► godot_animate_streamlines
    │             └──► godot_set_material (PBR on mesh)
    │             └──► godot_add_light (scene lighting)
    │             └──► godot_create_camera (render setup)
    │             │
    │             └──► godot_export_web
    │                    │ HTML5/WASM build
    │                    │
    │                    └──► resonite-mcp (XR world asset)
```

## File Structure

```
godot-mcp/
├── justfile                    # Command recipes (bootstrap, serve, test, etc.)
├── pyproject.toml              # Python project config (uv + Ruff + pytest)
├── uv.lock                     # Locked Python dependencies
├── start.ps1                   # Fleet-standard PowerShell launcher
├── start.bat                   # CMD wrapper → start.ps1
├── README.md                   # Project overview
├── ARCHITECTURE.md             # Detailed architecture (this document)
├── LICENSE                     # MIT
├── STATUS.md                   # Implementation status
├── project.godot               # Godot project config (for bridge addon)
├── main_bridge.tscn            # Minimal Godot scene with bridge
│
├── src/
│   └── godot_mcp/
│       ├── __init__.py
│       ├── server.py            # FastAPI app + FastMCP + REST endpoints
│       ├── tools/
│       │   ├── __init__.py      # Re-exports register_all
│       │   └── core_tools.py    # 12 MCP tool functions
│       ├── services/
│       │   ├── __init__.py
│       │   └── godot_bridge.py  # TCP socket client (GodotBridge class)
│       └── bridge/
│           └── mcp_bridge.gd    # GDScript TCPServer (runs inside Godot)
│
├── webapp/
│   ├── package.json             # Node.js deps (Vite, React, Tailwind)
│   ├── vite.config.ts           # Vite config with proxy to 10993
│   ├── tsconfig.json            # TypeScript config
│   ├── tailwind.config.js       # Tailwind CSS config
│   ├── postcss.config.js        # PostCSS config
│   ├── biome.json               # Biome linter config
│   ├── index.html               # SPA entry point
│   └── src/                     # React app source
│
├── tests/
│   ├── __init__.py
│   ├── test_bridge.py           # GodotBridge unit tests
│   ├── test_server.py           # Server module tests
│   └── test_tools.py            # MCP tool function tests
│
└── native/
    ├── Cargo.toml               # Tauri 2.0 Rust dependencies
    ├── tauri.conf.json          # Tauri window + security config
    └── src/
        └── main.rs              # Tauri entry point
```

## Port Allocation

| Port | Component | Protocol | Description |
|------|-----------|----------|-------------|
| **10992** | Webapp (Frontend) | HTTP | Vite dev server, React SPA, proxies `/api` → 10993 |
| **10993** | Backend (Server) | HTTP + SSE | FastAPI REST + FastMCP SSE transport |
| **9080** | Godot Bridge | TCP | Internal JSON protocol (not exposed to network) |

All ports are from the fleet reserved range 10700-11000. The backend/frontend use adjacent ports (10992/10993) per the Adjacency Rule.

The Godot bridge port (9080) is internal-only — communication between the Python server and the local Godot engine process. It is not exposed to any network interface beyond localhost.

## Security Notes

- Godot bridge binds to `127.0.0.1:9080` (localhost only)
- No authentication on the bridge — it assumes a trusted local process
- REST API uses CORS `allow_origins=["*"]` for development convenience
- No secrets or API keys in the codebase
- `GODOT_PATH` and `GODOT_HOST` are configurable via environment variables, not hardcoded
