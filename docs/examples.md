# Godot MCP — Worked Examples

**Version**: 0.1.0

---

## Example 1: CFD Flow Visualization

Import a river STL model, load a FluidX3D velocity field, spawn particle streamlines, add lighting, and export to HTML5.

### Prerequisites

- Godot engine running with `mcp_bridge.gd` Autoload
- `C:/data/river_geometry.stl` — binary STL of river bed
- `C:/data/river_flow.csv` — velocity field (50,000 points, columns: x,y,z,vx,vy,vz)
- Python MCP server connected to bridge

### Step 1: Verify Engine and Bridge

**Tool call**:
```python
await client.call_tool("godot_status", {})
```

**Expected response**:
```json
{
  "success": true,
  "data": {
    "godot_version": "4.6.2",
    "node_count": 3,
    "root_nodes": ["Root"],
    "fps": 60.0,
    "bridge_connected": true
  }
}
```

Bridge is connected, no scene nodes yet.

### Step 2: Import River STL Mesh

**Tool call**:
```python
await client.call_tool("godot_import_stl", {
    "path": "C:/data/river_geometry.stl",
    "name": "River_Mesh",
    "scale": 1.0,
    "position_x": 0.0,
    "position_y": 0.0,
    "position_z": 0.0
})
```

**Expected response**:
```json
{
  "success": true,
  "data": {
    "imported": true,
    "name": "River_Mesh",
    "vertices": 32400,
    "aabb": {"size_x": 20.0, "size_y": 5.0, "size_z": 10.0}
  }
}
```

The mesh is now a `MeshInstance3D` under `STL_Imports` container. The AABB tells us the scene spans 20m × 5m × 10m.

### Step 3: Load Velocity Field Data

**Tool call**:
```python
await client.call_tool("godot_load_velocity_field", {
    "csv_path": "C:/data/river_flow.csv",
    "name": "RiverFlow"
})
```

**Expected response**:
```json
{
  "success": true,
  "data": {
    "loaded": true,
    "name": "RiverFlow",
    "point_count": 50000,
    "bbox": {
      "min_x": -10.0, "min_y": 0.0, "min_z": -5.0,
      "max_x": 10.0, "max_y": 5.0, "max_z": 5.0
    }
  }
}
```

The velocity field is stored as node metadata on a `Node3D` named `RiverFlow`. The bounding box aligns with our STL mesh.

### Step 4: Spawn GPU Particle System

**Tool call**:
```python
await client.call_tool("godot_spawn_particles", {
    "count": 10000,
    "name": "FlowParticles",
    "color": "#4488ff",
    "spread_x": 10.0,
    "spread_y": 5.0,
    "spread_z": 10.0
})
```

**Expected response**:
```json
{
  "success": true,
  "data": {
    "spawned": true,
    "name": "FlowParticles",
    "count": 10000,
    "particle_system": "GPUParticles3D"
  }
}
```

A `GPUParticles3D` node is created under `Particle_Systems` with a sphere mesh draw pass and blue emission color.

### Step 5: Animate Streamlines Along Velocity Field

**Tool call**:
```python
await client.call_tool("godot_animate_streamlines", {
    "velocity_field": "RiverFlow",
    "particle_system": "FlowParticles",
    "speed": 1.5
})
```

**Expected response**:
```json
{
  "success": true,
  "data": {
    "animated": true,
    "particle_system": "FlowParticles",
    "velocity_field": "RiverFlow",
    "speed_multiplier": 1.5,
    "point_count": 50000
  }
}
```

The particle emission box is now set to the velocity field bounding box. Particles emit within the river volume and initial velocities are sampled from the field data.

### Step 6: Set PBR Material on River Mesh

**Tool call**:
```python
await client.call_tool("godot_set_material", {
    "node": "River_Mesh",
    "color": "#2a4a6b",
    "roughness": 0.6
})
```

**Expected response**:
```json
{
  "success": true,
  "data": {
    "set": true,
    "node": "River_Mesh",
    "color": "#2a4a6b",
    "roughness": 0.6
  }
}
```

The river mesh now has a dark blue PBR material with medium roughness (muddy/stone river bed appearance).

### Step 7: Add Scene Lighting

**Tool calls**:
```python
# Directional light (sun)
await client.call_tool("godot_add_light", {
    "light_type": "directional",
    "name": "Sun",
    "intensity": 2.0
})

# Ambient fill light
await client.call_tool("godot_add_light", {
    "light_type": "ambient",
    "name": "Ambient",
    "intensity": 0.3
})
```

**Expected responses**:
```json
{"success": true, "data": {"created": true, "name": "Sun", "type": "directional", "intensity": 2.0}}
{"success": true, "data": {"created": true, "name": "Ambient", "type": "ambient", "intensity": 0.3}}
```

### Step 8: Create Orbit Camera

**Tool call**:
```python
await client.call_tool("godot_create_camera", {
    "name": "MainCam",
    "position_y": 12.0,
    "position_z": 18.0,
    "look_at_y": 2.0,
    "fov": 65.0
})
```

**Expected response**:
```json
{
  "success": true,
  "data": {
    "created": true,
    "name": "MainCam",
    "fov": 65.0,
    "position": {"x": 0.0, "y": 12.0, "z": 18.0}
  }
}
```

Camera positioned above and behind the river, looking at the center. Orbit controls allow runtime manipulation.

### Step 9: Inspect Scene Tree

**Tool call**:
```python
await client.call_tool("godot_read_scene_tree", {})
```

**Expected response** (abbreviated):
```json
{
  "success": true,
  "data": {
    "scene_tree": {
      "name": "Root",
      "type": "Viewport",
      "path": "/root",
      "children": [
        {"name": "MCP_Scene", "type": "Node3D", "path": "/root/MCP_Scene",
         "children": [
           {"name": "STL_Imports", "type": "Node3D", "path": "/root/MCP_Scene/STL_Imports",
            "children": [
              {"name": "River_Mesh", "type": "MeshInstance3D", "path": "/root/MCP_Scene/STL_Imports/River_Mesh", "children": []}
            ]},
           {"name": "Velocity_Fields", "type": "Node3D", "path": "/root/MCP_Scene/Velocity_Fields",
            "children": [
              {"name": "RiverFlow", "type": "Node3D", "path": "/root/MCP_Scene/Velocity_Fields/RiverFlow", "children": []}
            ]},
           {"name": "Particle_Systems", "type": "Node3D", "path": "/root/MCP_Scene/Particle_Systems",
            "children": [
              {"name": "FlowParticles", "type": "GPUParticles3D", "path": "/root/MCP_Scene/Particle_Systems/FlowParticles", "children": []}
            ]},
           {"name": "Lights", "type": "Node3D", "path": "/root/MCP_Scene/Lights",
            "children": [
              {"name": "Sun", "type": "DirectionalLight3D", ...},
              {"name": "Ambient", "type": "OmniLight3D", ...}
            ]},
           {"name": "Cameras", "type": "Node3D", "path": "/root/MCP_Scene/Cameras",
            "children": [
              {"name": "MainCam", "type": "Camera3D", ...}
            ]}
         ]}
      ]
    },
    "node_count": 11
  }
}
```

### Step 10: Export to HTML5

**Tool call**:
```python
await client.call_tool("godot_export_web", {
    "output_path": "C:/builds/cfd-viz/index.html"
})
```

**Expected response**:
```json
{
  "success": true,
  "data": {
    "exported": true,
    "message": "Scene exported to C:/builds/cfd-viz/index.html",
    "requires_cli": false
  }
}
```

**Result**: Open `C:/builds/cfd-viz/index.html` in any modern browser. 10,000 GPU particles animate along the river velocity field. The scene is fully interactive (orbit camera, real-time particles).

---

## Example 2: Architecture Visualization

Import a CAD building model, set up lighting, apply PBR concrete/glass materials, position camera, and export for client review.

### Prerequisites

- `C:/data/building.stl` — CAD export of building model

### Step 1: Import Building Model

```python
await client.call_tool("godot_import_stl", {
    "path": "C:/data/building.stl",
    "name": "Building",
    "scale": 0.01,
    "position_y": 0.0
})
```

**Response**:
```json
{
  "success": true,
  "data": {
    "imported": true,
    "name": "Building",
    "vertices": 180000,
    "aabb": {"size_x": 15.0, "size_y": 40.0, "size_z": 25.0}
  }
}
```

The building is 15m × 40m × 25m (a real-world scale 15-story structure). Scale 0.01 converts from CAD units (cm) to Godot units (m).

### Step 2: Apply PBR Materials

Concrete base material and glass accent material.

```python
# Concrete base
await client.call_tool("godot_set_material", {
    "node": "Building",
    "color": "#c8c8c8",
    "roughness": 0.7
})
```

**Response**:
```json
{
  "success": true,
  "data": {
    "set": true,
    "node": "Building",
    "color": "#c8c8c8",
    "roughness": 0.7
  }
}
```

Grey PBR concrete, matte finish (roughness 0.7).

### Step 3: Add Architectural Lighting

```python
# Main directional light (sun simulation)
await client.call_tool("godot_add_light", {
    "light_type": "directional",
    "intensity": 2.5
})

# Ambient fill to soften shadows
await client.call_tool("godot_add_light", {
    "light_type": "ambient",
    "intensity": 0.3
})

# Warm accent light from the side
await client.call_tool("godot_add_light", {
    "light_type": "omni",
    "name": "WarmAccent",
    "intensity": 1.2,
    "position_x": 20.0,
    "position_y": 10.0,
    "position_z": -10.0
})
```

### Step 4: Create Architecture Camera

```python
await client.call_tool("godot_create_camera", {
    "name": "ArchCam",
    "position_y": 25.0,
    "position_z": 40.0,
    "look_at_y": 15.0,
    "fov": 60.0
})
```

**Response**:
```json
{
  "success": true,
  "data": {
    "created": true,
    "name": "ArchCam",
    "fov": 60.0,
    "position": {"x": 0.0, "y": 25.0, "z": 40.0}
  }
}
```

Elevated perspective showing the full building height.

### Step 5: Export

```python
await client.call_tool("godot_export_web", {
    "output_path": "C:/builds/arch-viz/index.html"
})
```

**Result**: Client opens the HTML5 export in any browser. The 180K-vertex building renders with PBR materials, three-point lighting, and orbit camera for exploration.

---

## Example 3: Particle Toy

Create a standalone GPU particle playground with colorful emission, wide spread, and fast animation — no CAD or velocity data needed.

### Step 1: Spawn Large Particle System

```python
await client.call_tool("godot_spawn_particles", {
    "count": 50000,
    "name": "Fireworks",
    "color": "#ff6600",
    "spread_x": 20.0,
    "spread_y": 15.0,
    "spread_z": 20.0
})
```

**Response**:
```json
{
  "success": true,
  "data": {
    "spawned": true,
    "name": "Fireworks",
    "count": 50000,
    "particle_system": "GPUParticles3D"
  }
}
```

50,000 orange particles in a 40×30×40 meter emission box.

### Step 2: Create Dynamic Lighting

```python
# Colored omni lights for particle illumination
await client.call_tool("godot_add_light", {
    "light_type": "omni",
    "name": "RedLight",
    "intensity": 3.0,
    "position_x": 10.0, "position_y": 5.0, "position_z": 0.0
})

await client.call_tool("godot_add_light", {
    "light_type": "omni",
    "name": "BlueLight",
    "intensity": 3.0,
    "position_x": -10.0, "position_y": 5.0, "position_z": 0.0
})
```

### Step 3: Set Camera for Overview

```python
await client.call_tool("godot_create_camera", {
    "name": "ParticleCamera",
    "position_y": 20.0,
    "position_z": 30.0,
    "look_at_y": 0.0,
    "fov": 75.0
})
```

### Step 4: Export as Screensaver/Installation

```python
await client.call_tool("godot_export_web", {
    "output_path": "C:/builds/particle-toy/index.html"
})
```

**Result**: A standalone HTML5 particle screensaver. 50,000 glowing orange particles fill a 40m box with real-time GPU compute.

### Variations

To create different visual effects, change only the spawn parameters:

**Galaxy effect**:
```python
await client.call_tool("godot_spawn_particles", {
    "count": 100000,
    "name": "Galaxy",
    "color": "#aa88ff",
    "spread_x": 50.0,
    "spread_y": 5.0,
    "spread_z": 50.0
})
```

**Lava effect**:
```python
await client.call_tool("godot_spawn_particles", {
    "count": 20000,
    "name": "Lava",
    "color": "#ff2200",
    "spread_x": 0.5,
    "spread_y": 2.0,
    "spread_z": 0.5
})
```

---

## Troubleshooting Examples

### Bridge Not Connected

**Problem**: `godot_status` returns connection error.

**Check**:
1. Is the Godot project running? (F5 in Godot editor)
2. Is `mcp_bridge.gd` set as Autoload? (Project > Project Settings > Autoload)
3. Is port 9080 free? (`Get-NetTCPConnection -LocalPort 9080`)

**Error response**:
```json
{
  "success": false,
  "error": "Bridge not connected. Start Godot with mcp_bridge.gd Autoload."
}
```

### STL Import Fails

**Problem**: `godot_import_stl` returns `file_not_found`.

**Check**:
1. Use absolute paths only (e.g., `C:/data/mesh.stl` not `./mesh.stl`)
2. Forward slashes only — backslashes cause issues
3. File must be binary STL, not ASCII STL

**Error response**:
```json
{
  "success": false,
  "error": "File not found: C:/data/mesh.stl"
}
```

### Export Templates Missing

**Problem**: `godot_export_web` fails.

**Check**:
1. Open Godot Editor > Editor > Manage Export Templates
2. Download and install the latest HTML5 templates
3. Or use CLI export: `godot --headless --export-release "Web" build/index.html`

**Error response**:
```json
{
  "success": false,
  "error": "Web export templates not installed. Use godot editor to install or export via CLI."
}
```
