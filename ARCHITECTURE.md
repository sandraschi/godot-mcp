# godot-mcp — Godot 4.0 Engine Control via MCP + WebSocket Bridge

**Vision**: Import STL geometry from qcad-mcp, load FluidX3D velocity fields, spawn GPU particle systems, animate streamlines, assign PBR materials, set up lighting/cameras, and export to Web/Resonite — all through MCP tools bridging to a running Godot 4.0 engine.

**Price of entry**: Free. Godot 4.0 is MIT-licensed open source.

---

## Architecture

```
Godot 4.0 Engine (local or headless)
    │
    └── TCP bridge (port 9080)
            │
            └── MCP Server (FastMCP 3.2 + FastAPI)
                    │
                    ├── SSE transport (MCP clients)
                    ├── REST API (/api/v1/*)
                    └── Vite + React webapp (port 10992)
```

### Communication Flow

```
MCP Client → HTTP POST /sse → FastMCP → TCP → Godot 4.0 Engine
                                              │
REST Client → HTTP /api/v1/status ────────────┘
```

The TCP bridge (port 9080) is the critical path component. A Godot MCP addon/plugin must be loaded into the engine to accept JSON commands and return structured results.

---

## MCP Tools (12)

### Engine & Scene
| Tool | Access | Purpose |
|------|--------|---------|
| `godot_status` | READ_ONLY | Engine availability, version, node count, FPS |
| `godot_import_stl` | MUTATING | Import STL mesh file into the current scene as a MeshInstance3D |
| `godot_read_scene_tree` | READ_ONLY | Dump scene hierarchy as nested JSON tree |

### Particles & Velocity Fields
| Tool | Access | Purpose |
|------|--------|---------|
| `godot_spawn_particles` | MUTATING | Create GPU particle system (GPUParticles3D) with configurable emission, lifetime, velocity |
| `godot_load_velocity_field` | MUTATING | Load FluidX3D-compatible CSV velocity field data and bind to particle system |
| `godot_animate_streamlines` | MUTATING | Animate particles along streamlines from velocity field |

### Materials & Lighting
| Tool | Access | Purpose |
|------|--------|---------|
| `godot_set_material` | MUTATING | Assign StandardMaterial3D (PBR) with albedo, roughness params to mesh |
| `godot_add_light` | MUTATING | Add directional, ambient, or omni light to the scene |

### Camera & Export
| Tool | Access | Purpose |
|------|--------|---------|
| `godot_create_camera` | MUTATING | Create Camera3D with orbit controls, FOV, transform |
| `godot_export_web` | MUTATING | Export current scene as HTML5/WebAssembly build |

### Configuration & Diagnostics
| Tool | Access | Purpose |
|------|--------|---------|
| `godot_set_config` | MUTATING | Write key/value to project.godot INI config file |
| `godot_headless_verify` | READ_ONLY | Check headless mode status + CLI command suggestion |

---

## Cross-Repo Pipeline

### qcad-mcp → Godot → Resonite / Web

```
qcad-mcp plan_extrude → STL
    │
    ├── godot-mcp godot_import_stl → Scene (MeshInstance3D)
    │       │
    │       ├── godot_load_velocity → FluidX3D velocity field
    │       │       │
    │       │       └── GPU particles flow along CFD streamlines
    │       │
    │       ├── godot_set_material → PBR albedo/roughness/metallic
    │       ├── godot_add_light → Scene lighting
    │       ├── godot_create_camera → Render setup
    │       │
    │       └── godot_export_web → HTML5 build
    │               │
    │               └── resonite-mcp → Import as XR world asset
    │
    └── Direct: Godot native STL import via WebSocket command
```

### Velocity Field Pipeline

```
FluidX3D CFD simulation → velocity field (.vti or raw binary)
    │
    └── godot-mcp godot_load_velocity → GPU buffer
            │
            └── godot_spawn_particles → emit at velocity sample points
                    │
                    └── godot_animate_streamline → animate along field
```

---

## Webapp

Fleet-standard Vite + React layout on port 10992:

| Page | Purpose |
|------|---------|
| **Dashboard** | Godot engine status, quick actions, scene summary |
| **Models** | Upload/download STL, OBJ, velocity field files |
| **Logs** | Live SSE log viewer with filter, pause, export |
| **Settings** | Godot path, WebSocket port, engine config |
| **Help** | Godot 4.0 reference, fleet pipeline, tools documentation |

---

## Godot Addon (MCP Bridge)

A single GDScript autoload (`src/godot_mcp/bridge/mcp_bridge.gd`) provides the TCP server bridge. Place as autoload in project.godot to accept commands on port 9080.

The bridge handles: status, import_stl, load_velocity_field, spawn_particles, animate_streamlines, create_camera, add_light, set_material, export_web, read_scene_tree, set_config, headless_verify, add_node, remove_node, save_scene.

---

## Fleet Registration

| Item | Value |
|------|-------|
| **Repo** | `D:\Dev\repos\godot-mcp` |
| **Ports** | Backend 10993, Frontend 10992 |
| **Version** | 0.1.0 |
| **Engine** | Godot 4.0 (MIT, free) |
| **Bridge** | TCP (port 9080) + JSON |
| **Linting** | Ruff (Python) |
| **Pipeline sources** | qcad-mcp (STL), FluidX3D (velocity fields) |
| **Pipeline targets** | resonite-mcp (XR worlds), Web export (HTML5) |
