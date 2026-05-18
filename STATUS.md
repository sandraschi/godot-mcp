# Status — godot-mcp

**Status**: v0.1.0 — 12 MCP tools implemented. TCP bridge client ready.

**Repo**: `D:\Dev\repos\godot-mcp`
**Ports**: Backend 10993, Frontend 10992
**Created**: 2026-05

## Architecture

Godot 4.0 engine → TCP bridge (port 9080) → MCP server → REST API + SSE + Vite webapp.

Core bridge: Godot 4.0 GDScript TCPServer addon (`src/godot_mcp/bridge/mcp_bridge.gd`) that listens for JSON commands on a local TCP server. The MCP server connects as a client via `godot_mcp.services.godot_bridge` and relays MCP tool calls.

See `ARCHITECTURE.md` for full design.

## Implemented (12 tools)

| Tool | Access | Status |
|------|--------|--------|
| `godot_status` | READ_ONLY | Implemented |
| `godot_import_stl` | MUTATING | Implemented |
| `godot_load_velocity_field` | MUTATING | Implemented |
| `godot_spawn_particles` | MUTATING | Implemented |
| `godot_animate_streamlines` | MUTATING | Implemented |
| `godot_create_camera` | MUTATING | Implemented |
| `godot_add_light` | MUTATING | Implemented |
| `godot_set_material` | MUTATING | Implemented |
| `godot_export_web` | MUTATING | Implemented |
| `godot_read_scene_tree` | READ_ONLY | Implemented |
| `godot_set_config` | MUTATING | Implemented |
| `godot_headless_verify` | READ_ONLY | Implemented |

## Implemented

- FastMCP 3.2 server scaffold with dual-mode (stdio/http/dual)
- REST API: /api/v1/status, /api/v1/control/tool, /api/v1/logs/stream
- SSE log streaming endpoint
- Godot engine auto-detection (PATH + GODOT_PATH env var)
- CORS middleware, lifespan state management
- TCP bridge client with connect/disconnect/send/recv JSON protocol
- Bridge auto-connect in server lifespan startup/shutdown
- Fleet-standard Vite + React webapp (5 pages)
- justfile with bootstrap, serve, web, dev, lint, fix, test, check, health
- start.ps1 + start.bat fleet-standard launch scripts

## Next Steps

1. Deploy GDScript bridge addon in a Godot 4.0 project
2. Integration test with running Godot engine
3. Connect qcad-mcp STL pipeline → godot_mcp import → FluidX3D velocity → particles
4. Integration test with freecad-mcp STL → godot import
