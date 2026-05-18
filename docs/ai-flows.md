# Godot MCP — AI Game Development Flows

This document describes how AI agents (LLMs with tool access) use godot-mcp to create, modify, and export Godot scenes programmatically.

## Agentic Game Development

### Core Concept

Traditional game development involves a human clicking through the Godot editor to place nodes, adjust parameters, and build scenes. With godot-mcp, an AI agent can perform these same operations through 12 MCP tools — creating nodes, setting materials, configuring lights, positioning cameras, spawning particle systems, and exporting builds.

The AI becomes a "Godot engine operator" that can:
- Build scenes from natural language descriptions
- Import and configure assets from external pipelines
- Run procedural generation at scale
- Export to multiple targets in automated workflows

### Tool Categories

```
Scene Construction:
  godot_import_stl       — Import 3D geometry
  godot_add_light        — Add lighting
  godot_create_camera    — Set up rendering
  godot_set_material     — Configure materials

Particle & Simulation:
  godot_load_velocity_field  — Load CFD data
  godot_spawn_particles      — Create particle system
  godot_animate_streamlines  — Drive particles with velocity data

Export & Inspection:
  godot_export_web       — HTML5/WASM build
  godot_read_scene_tree  — Inspect hierarchy
  godot_status           — Engine diagnostics

Configuration:
  godot_set_config       — Modify project settings
  godot_headless_verify  — Check headless mode
```

## Cross-Repo Pipeline

The primary use case for godot-mcp is as the **visualization terminal** in a multi-repo CAD-to-game pipeline:

### Full Pipeline: CAD → CFD → Visualization

```
┌──────────────────────┐
│   qcad-mcp (10966)   │  CAD: Design geometry
│   plan_extrude       │  Export: DXF, STL
└────────┬─────────────┘
         │ STL file
         ▼
┌──────────────────────┐
│  freecad-mcp (10944) │  BIM: Convert to STEP/STL
│   import_stl         │  Scale, validate, prepare
└────────┬─────────────┘
         │ STL file (validated)
         ▼
┌──────────────────────┐
│  FluidX3D (GPU CFD)  │  CFD: Run Lattice Boltzmann simulation
│                      │  Export: CSV velocity field (x,y,z,vx,vy,vz)
└────────┬─────────────┘
         │ CSV velocity field
         ▼
┌──────────────────────┐
│  godot-mcp (10993)   │  Visualization: Import, render, animate
│  godot_import_stl    │    ├─ MeshInstance3D
│  godot_load_velocity │    ├─ Velocity field node
│  godot_spawn_particles│   ├─ GPU particle system
│  godot_animate_stream│   ├─ Streamline animation
│  godot_set_material   │   ├─ PBR materials
│  godot_add_light      │   ├─ Scene lighting
│  godot_create_camera  │   ├─ Render camera
│  godot_export_web     │   └─ HTML5 export
└────────┬─────────────┘
         │
    ┌────┴────┐
    ▼         ▼
 HTML5    resonite-mcp
 (web)     (XR world)
```

### Step-by-Step: CFD Velocity Field Animation Pipeline

This is the flagship flow for scientific visualization:

**1. Prepare geometry** (qcad-mcp):
```
Call: plan_extrude → STL file
Output: C:/data/river_geometry.stl
```

**2. Import to Godot**:
```
Call: godot_import_stl(path="C:/data/river_geometry.stl", name="River_Mesh", scale=1.0)
Result: MeshInstance3D named "River_Mesh" created with vertex count and AABB
```

**3. Load velocity data**:
```
Call: godot_load_velocity_field(csv_path="C:/data/river_flow.csv", name="FlowData")
Result: Node3D "FlowData" with 50,000 points and vectors stored as metadata
```

**4. Spawn particles**:
```
Call: godot_spawn_particles(count=10000, name="FlowParticles", color="#4488ff", spread_x=10, spread_y=5, spread_z=10)
Result: GPUParticles3D system created, sphere draw pass configured
```

**5. Animate streamlines**:
```
Call: godot_animate_streamlines(velocity_field="FlowData", particle_system="FlowParticles", speed=1.5)
Result: Particle emission box set to velocity field bounds, emission velocity configured
```

**6. Style the scene**:
```
Call: godot_set_material(node="River_Mesh", color="#336699", roughness=0.4)
Call: godot_add_light(light_type="directional", intensity=1.5)
Call: godot_add_light(light_type="ambient", intensity=0.3)
```

**7. Position camera**:
```
Call: godot_create_camera(name="RenderCam", position_y=15, position_z=20, look_at_y=2, fov=60)
```

**8. Export**:
```
Call: godot_export_web(output_path="C:/builds/cfd-viz/index.html")
Result: HTML5/WASM build with particle animation running in browser
```

### STL Import Pipeline

Simpler flow for just importing and rendering CAD geometry:

```
qcad-mcp / freecad-mcp → STL
    │
    ▼
godot_import_stl → MeshInstance3D
    │
    ├── godot_set_material (PBR)
    ├── godot_add_light (directional + ambient)
    ├── godot_create_camera (orbit)
    └── godot_export_web (HTML5 viewer)
```

## Kids CFD Game ("RiverRide")

A Godot HTML5 game that teaches STEM concepts to 4-8 year olds through fluid dynamics visualization.

### Concept

- Colorful 3D river scene with gentle water flow
- Kids place boats (rubber duck, paper boat, toy sailboat) into the river
- Boats follow real fluid streamlines computed by FluidX3D
- Speed slider: "Fast Water / Slow Water"
- Color-coded velocity: blue = slow, yellow = medium, red = fast
- Gentle math overlay: "The water moves at 0.5 meters per second — that's as fast as you walking!"

### MCP Pipeline

```
qcad-mcp: Design simple river geometry → DXF
    │
FluidX3D: Simulate laminar flow → CSV velocity field
    │
godot-mcp:
    ├── godot_import_stl (river bed)
    ├── godot_load_velocity_field (flow data)
    ├── godot_spawn_particles (colorful boats)
    ├── godot_animate_streamlines (boats follow flow)
    ├── godot_add_light (sunlight)
    ├── godot_create_camera (top-down view)
    └── godot_export_web → playable HTML5 game
```

### Learning Objectives by Age

| Age | Concept |
|-----|---------|
| 4-5 | Fast/slow water, colorful streamlines, boat placement |
| 5-6 | What is a "meter per second"? Compare to walking speed |
| 6-7 | Why is water faster in the middle? (boundary layers — visual only) |
| 8+ | Introduction to vectors: "the arrow shows where water goes" |

## Tauri Native Wrapper

For desktop distribution beyond the web export:

```
godot_export_web → HTML5/WASM build
    │
    ▼
native/ (Tauri 2.0)
    ├── Cargo.toml (Rust + tauri 2)
    ├── tauri.conf.json (window config)
    └── src/main.rs (entry point)
    │
    ▼
Standalone .exe (~5 MB + web content)
```

The Tauri wrapper:
- Bundles the web export into a standalone desktop app
- ~5 MB overhead (vs ~200 MB for Electron)
- System tray for background particle simulation monitoring
- Auto-updater for distributed CFD visualization tools
- Native file dialogs for STL/CSV file loading

## Example Agentic Session

An LLM-driven workflow to create a simple architectural visualization scene:

```
User: "Create a 3D scene with a CAD model, PBR concrete material, and orbit camera."

Agent:
  1. godot_status()
     → Engine v4.4.0, bridge connected, 0 nodes

  2. godot_import_stl(path="C:/projects/building.stl", name="Building", scale=0.01)
     → Imported, 45,000 vertices, AABB 15x8x12m

  3. godot_set_material(node="Building", color="#c4c4c4", roughness=0.7)
     → PBR concrete material applied

  4. godot_add_light(light_type="directional", intensity=2.0)
     → DirectionalLight3D "MCP_Light_directional" created

  5. godot_add_light(light_type="ambient", intensity=0.4)
     → Ambient light set

  6. godot_create_camera(name="ArchCam", position_y=20, position_z=30, look_at_y=4, fov=65)
     → Camera3D with orbit controls created

  7. godot_read_scene_tree()
     → Returns full hierarchy:
        - Building (MeshInstance3D)
        - MCP_Light_directional (DirectionalLight3D)
        - ArchCam (Camera3D)

  8. godot_export_web(output_path="C:/builds/arch-viz/index.html")
     → Web export ready
```

## Benefits of Agentic Game Development

### Rapid Prototyping
An AI agent can go from "idea" to "running scene" in minutes. Multiple design iterations can be explored by modifying tool calls rather than re-doing manual editor work.

### Procedural Generation at Scale
AI agents can invoke the tools in loops to generate thousands of objects programmatically — something tedious in the editor but trivial with MCP tools.

### Educational Tools
The pipeline enables creation of interactive science visualizations (CFD flow, architectural walkthroughs, particle physics demos) that can be exported to Web and deployed instantly.

### Cross-Repo Integration
godot-mcp is not isolated — it consumes output from qcad-mcp, freecad-mcp, and FluidX3D, and feeds into resonite-mcp. An AI agent orchestrating the full pipeline can create end-to-end visualizations without human intervention.

### Reproducibility
Tool call sequences are deterministic and can be logged, versioned, and replayed. This makes scientific visualizations reproducible — a key requirement for academic CFD work.

## Future Directions

### Multi-Agent Game Creation
Multiple AI agents working concurrently on different aspects of a game: one agent on level design (placing nodes), another on materials (PBR configuration), a third on lighting, coordinated through a supervisor agent.

### Real-Time Collaborative Editing
Multiple users and AI agents connected to the same Godot engine via MCP, each making changes visible to all others in real time. Like Google Docs for game development.

### AI-Generated Shaders
MCP tools that can generate GDScript shader code, upload it to the engine, and apply it to materials — all through natural language prompts.

### Automated Testing
AI agents running through game levels via MCP tools, verifying scene tree state after each operation, and reporting bugs automatically.
