# Godot MCP

[![CI](https://github.com/sandraschi/godot-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/sandraschi/godot-mcp/actions/workflows/ci.yml)
[![Version](https://img.shields.io/badge/version-0.2.0-blue?style=flat-square)](https://github.com/sandraschi/godot-mcp)
[![Python](https://img.shields.io/badge/python-3.12|3.13-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastMCP](https://img.shields.io/badge/FastMCP-3.3-6366f1?style=flat-square&logo=python&logoColor=white)](https://github.com/jlowin/fastmcp)
[![MCP](https://img.shields.io/badge/MCP-2024--11--05-8B5CF6?style=flat-square)](https://modelcontextprotocol.io)
[![License: MIT](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Godot](https://img.shields.io/badge/Godot-4.4-478cbf?style=flat-square&logo=godot-engine&logoColor=white)](https://godotengine.org/)
[![Just](https://img.shields.io/badge/Built-Just-000000?style=flat-square&logo=gnu-bash&logoColor=white)](https://github.com/casey/just)

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
- [Community](docs/community.md)
- [History](docs/history.md)

## Quick Start

```powershell
just bootstrap      # uv sync + npm install
just serve          # start backend (port 10993)
just web            # start frontend (port 10992)
```
Or `.\start.ps1` — kills zombies, starts both, opens browser.

## Key Features

- **14 MCP tools** — godot_status, godot_import_stl, godot_import_glb, godot_import_obj, godot_spawn_particles, godot_load_velocity, godot_animate_streamline, godot_set_material, godot_add_light, godot_create_camera, godot_export_web, godot_run_simulation, godot_set_scene_property, godot_query_scene
- **Godot 4 engine control** — scene graph manipulation via WebSocket bridge (port 9080)
- **Multi-format import** — STL (binary), GLB/GLTF (via GLTFDocument), OBJ (via ResourceLoader)
- **CFD velocity fields** — load FluidX3D data, animate streamlines with GPU particles
- **PBR materials** — assign physically-based materials to any mesh surface
- **HTML5 export** — build WebAssembly/WebGL with `godot --headless --export-release` fallback
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
