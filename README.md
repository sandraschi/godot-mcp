# Godot MCP

[![Version](https://img.shields.io/badge/version-0.1.0-blue?style=flat-square)](https://github.com/sandraschi/godot-mcp)
[![Python](https://img.shields.io/badge/python-3.12|3.13-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastMCP](https://img.shields.io/badge/FastMCP-3.2.0-6366f1?style=flat-square&logo=python&logoColor=white)](https://github.com/jlowin/fastmcp)
[![MCP](https://img.shields.io/badge/MCP-2024--11--05-8B5CF6?style=flat-square)](https://modelcontextprotocol.io)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Godot](https://img.shields.io/badge/Godot-4.0-478cbf?style=flat-square&logo=godot-engine&logoColor=white)](https://godotengine.org/)
[![Just](https://img.shields.io/badge/Built-Just-000000?style=flat-square&logo=gnu-bash&logoColor=white)](https://github.com/casey/just)

**AI-driven Godot 4.0 engine control — STL import, GPU particles, velocity fields, material assignment, Web export, and simulation via MCP tools.** 10 planned tools. Your AI assistant becomes a Godot engine operator.

| | |
|--:|--|
| **You might use this if…** | You want your AI to import CAD geometry, spawn GPU particle systems, animate velocity fields from FluidX3D, assign PBR materials, control cameras, and export Web/HTML5 builds — all through MCP tools. |
| **What it connects to** | Godot 4.0 engine (local or headless) via **WebSocket bridge** (port 9080) + `qcad-mcp` STL pipeline + `FluidX3D` velocity data |
| **Ports** | Backend **10993**, Frontend **10992** |
| **Start** | `just bootstrap` then `start.ps1` |

## Engine

| Component | Status | Purpose |
|-----------|--------|---------|
| **Godot 4.0** | Required | Scene graph, GPU particles, physics, Web export |
| **WebSocket bridge** | Required | MCP ↔ Godot communication on port 9080 |
| **MCP Plugin** | Required | Godot addon that listens for MCP commands |

## Planned Tools (10)

| Tool | Access | Purpose |
|------|--------|---------|
| `godot_status` | READ_ONLY | Engine availability, version, scene info |
| `godot_import_stl` | MUTATING | Import STL mesh from qcad-mcp pipeline |
| `godot_spawn_particles` | MUTATING | GPU particle system with configuration |
| `godot_load_velocity` | MUTATING | Load FluidX3D velocity field data |
| `godot_animate_streamline` | MUTATING | Animate particles along streamlines |
| `godot_set_material` | MUTATING | Assign PBR materials to mesh surfaces |
| `godot_add_light` | MUTATING | Add dynamic lights (point, spot, directional) |
| `godot_create_camera` | MUTATING | Create and position render cameras |
| `godot_export_web` | MUTATING | Export scene to HTML5/WebAssembly |
| `godot_run_simulation` | MUTATING | Trigger physics/particle simulation |

## Cross-Repo Pipeline

```
qcad-mcp plan_extrude → STL
    │
    └── godot-mcp godot_import_stl → Godot scene
            │
            ├── godot_load_velocity → FluidX3D velocity field
            ├── godot_spawn_particles → GPU particles
            ├── godot_set_material → PBR materials
            ├── godot_add_light → scene lighting
            ├── godot_create_camera → render cameras
            ├── godot_animate_streamline → particle animation
            └── godot_export_web → HTML5 build or residonite-mcp export
```

## Quick Start

```powershell
# 1. Bootstrap
just bootstrap   # uv sync + npm install

# 2. Set Godot path if not in PATH
$env:GODOT_PATH = "C:\Program Files\Godot\godot.exe"

# 3. Launch
start.ps1        # kills zombies, starts backend + frontend, opens browser
```

## MCP Client Config

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

Once connected, call `godot_status` to verify engine availability, then `godot_import_stl` to bring in CAD geometry from the qcad-mcp pipeline.

## Industrial Quality Stack

- **Python (Core)**: [Ruff](https://astral.sh/ruff) for linting. 10 planned MCP tools on FastMCP 3.2.
- **Webapp (UI)**: Vite + React + Tailwind CSS 3.4. Fleet-standard 5-page dashboard.
- **Protocol**: FastMCP 3.2 SSE transport + REST API.
- **Automation**: [Justfile](./justfile) recipes for all fleet operations.

## Links

- [Godot 4.0 Documentation](https://docs.godotengine.org/en/stable/)
- [Godot Engine](https://godotengine.org/)
- [FluidX3D](https://github.com/ProjectPhysX/FluidX3D)
- [qcad-mcp](https://github.com/sandraschi/qcad-mcp) — STL source pipeline
- [resonite-mcp](https://github.com/sandraschi/resonite-mcp) — XR world export target

## License

MIT — see [LICENSE](LICENSE).
