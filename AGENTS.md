# AGENTS.md — godot-mcp Context

**Repo**: godot-mcp — AI-driven Godot 4.4 engine control via MCP + game builder pipeline  
**Version**: 0.3.0 (49 MCP tools)  
**Python**: 3.10+ | **FastMCP**: 3.2.0+ | **Godot**: 4.4 | **Frontend**: Vite 7 + React 19

## Essential Paths

| Path | Purpose |
|------|---------|
| `src/godot_mcp/server.py` | FastMCP server + FastAPI gateway (port 10993) |
| `src/godot_mcp/services/godot_bridge.py` | TCP bridge client to Godot (port 9080) |
| `src/godot_mcp/bridge/mcp_bridge.gd` | GDScript autoload — TCP server inside Godot |
| `src/godot_mcp/game_builder/` | AI game-from-prompt pipeline (6 tools) |
| `src/godot_mcp/fleet/` | Cross-server fleet pipeline (6 tools) |
| `src/godot_mcp/itch/` | Butler/itch.io shipping (6 tools) |
| `src/godot_mcp/tools/core_tools.py` | Godot engine control tools (14) |
| `src/godot_mcp/sampling/` | LLM sampling tools (2) |
| `src/godot_mcp/mcp_bridge/` | Cross-server MCP bridge tools (2) |
| `src/godot_mcp/workflows/` | Workflow engine + 3 built-in workflows |
| `webapp/` | Vite React dashboard (port 10992) |
| `templates/` | Godot project templates + export presets |
| `samples/` | Sample games + MCPB bundles |
| `native/` | Tauri 2.0 desktop wrapper |
| `docs/SPEC_GAME_BUILDER.md` | Game Builder architecture spec |
| `justfile` | Task runner — `just serve`, `just godot-bridge`, etc. |

## Module Registration

All tools register via `src/godot_mcp/tools/__init__.py` → `register_all(mcp)`. Each module has a `register(mcp)` function. New modules MUST be added to the `register_all` imports and calls.

## Key Dependencies

- **worldlabs-mcp** (port 10865): Called via `MCPBridgeClient` from `godot_mcp.mcp_bridge` for Marble world generation
- **Godot 4.4** (port 9080): TCP bridge using `mcp_bridge.gd` autoload
- **Butler** (`BUTLER_API_KEY`): itch.io CLI for shipping

## Conventions

- Annotations: `_READ_ONLY = {"readonly": True}`, `_MUTATING = {"mutating": True}` per module
- Docstrings: Args in `Annotated[T, Field(...)]`, return format in docstring body
- Types: Pydantic v2 (`model_dump`, `model_validate`), no legacy `dict()`/`parse_obj()`
- Linting: Ruff (Python), Biome (web)
- Ports: 10993 backend, 10992 frontend, 9080 Godot bridge

Install docs: follow mcp-central-docs/standards/AGENT_INSTALL_REFERENCE.md
