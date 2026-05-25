# Godot MCP

<p align="center">
  <a href="https://github.com/casey/just"><img src="https://img.shields.io/badge/just-ready_to_go-7c5cfc?style=flat-square&logo=just&logoColor=white" alt="Just"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.13+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://github.com/PrefectHQ/fastmcp"><img src="https://img.shields.io/badge/FastMCP-3.2-7c5cfc?style=flat-square" alt="FastMCP"></a>
</p>

[![CI](https://github.com/sandraschi/godot-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/sandraschi/godot-mcp/actions/workflows/ci.yml)
AI-driven Godot 4.0 engine control via MCP tools. Import STL/GLB/OBJ geometry, load CFD velocity fields, spawn GPU particle systems, assign PBR materials, control cameras, and export HTML5 builds — all through FastMCP 3.2 tools over SSE transport. Designed as the visualization endpoint for the fleet CAD→CFD→render pipeline (qcad-mcp → freecad-mcp → FluidX3D → godot-mcp) and the blender-mcp → godot-mcp game asset pipeline.

## Contents

- [Installation](docs/install.md)
- [Architecture](docs/architecture.md)
- [Godot 4 Docs](docs/godot.md)
- [MCP Server](docs/mcp-server.md)
- [API Reference](docs/api.md)
- [AI Game Dev Flows](docs/ai-flows.md)
- [CLI Reference](docs/cli.md)
- [Comparison: Godot vs Unity vs Unreal](docs/comparison.md)
- [Example Projects](docs/examples.md)
- [Agentic Game Dev](docs/agentic-game-dev.md)
- [Little Game Guide](docs/little-game-guide.md) — study repos, AI workflow, Windows/iOS distribution
- [AI and Indie Games](docs/ai-and-indie-games.md) — is AI the death of indie? (scope, hobby vs career)
- [Ship to itch.io](docs/ship-to-itch.md) — Butler tools, `/ship` dashboard, env vars
- [Fleet game pipeline](docs/fleet-game-pipeline.md) — blender/worldlabs → Godot; splats vs GLB
- [Fleet assessment](docs/FLEET_ASSESSMENT.md) — implementation status and gaps
- [Community](docs/community.md)
- [History](docs/history.md)
- [PRD](docs/PRD.md)
- [Game Builder Pipeline](docs/SPEC_GAME_BUILDER.md) — AI-native game creation: prompt → worlds → Godot → itch.io
- [Sample Games](samples/README.md)

## Quick Start

```powershell
just bootstrap       # uv sync + npm install + Godot
just serve           # MCP + REST (10993)
just godot-bridge    # TCP bridge in Godot (9080) — required for engine tools
just bridge-test     # confirm godot_status
just web             # dashboard (10992)
```

Or `.\start.ps1` for backend + webapp only (start bridge separately).

**Play a sample game:** `just demo-list` then `just demo-run platformer` (see [samples/README.md](samples/README.md)).

**Export & ship a sample:** `just little-game-export web dodge` then open **`/ship`** in the dashboard, or `just ship web dodge` (requires `BUTLER_API_KEY` + `ITCH_TARGET`).

## Key Features

- **Game Builder** — 6 new MCP tools: `design_game`, `generate_game_worlds`, `compose_game_scene`, `generate_game_logic`, `export_and_ship`, `build_game`. Natural language → GamePlan → Marble worlds → Godot scene → GDScript → HTML5. See [SPEC](docs/SPEC_GAME_BUILDER.md).
- **6 itch ship tools** — `itch_status`, `godot_export_release`, `itch_push_preview`, `itch_push`, `itch_latest_version`, `ship_to_itch`
- **Godot 4 engine control** — scene graph via TCP bridge (port 9080)
- **Multi-format import** — STL (binary), GLB/GLTF (via GLTFDocument), OBJ (via ResourceLoader)
- **CFD velocity fields** — load FluidX3D data, animate streamlines with GPU particles
- **PBR materials** — assign physically-based materials to any mesh surface
- **HTML5 export** — build WebAssembly/WebGL with `godot --headless --export-release` fallback
- **itch.io shipping** — Butler push from CLI, MCP, REST, or dashboard `/ship` (export → preview → push)
- **REST API** — FastAPI gateway on port 10993 alongside MCP SSE
- **Tauri native wrapper** — `native/` directory for desktop distribution (~5 MB)

## Cross-Repo Pipeline

```
qcad-mcp (DXF/STL) → freecad-mcp (BIM/IFC) → FluidX3D (GPU CFD)
                                                  ↓
                                          CSV velocity field
                                                  ↓
                                          godot-mcp (import + visualize)
                                                  ↓
                              ┌───────────────────┼───────────────────┐
                              ↓                   ↓                   ↓
                        Resonite (XR)      Web (HTML5)        Tauri (native)
```

## License

MIT — see [LICENSE](LICENSE).

- [Godot Engine](https://godotengine.org/)
- [FluidX3D](https://github.com/ProjectPhysX/FluidX3D)
- [qcad-mcp](https://github.com/sandraschi/qcad-mcp)
