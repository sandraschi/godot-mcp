# WorldLabs → Godot Bridge

How worldlabs-mcp generates procedural terrain and godot-mcp loads it as
a real-time scene with CFD particle effects from FluidX3D.

## Pipeline

```
worldlabs-mcp (terrain heightmap) → godot-mcp (import → texture → CFD particles → export)
```

## Step-by-Step

### 1. worldlabs-mcp generates a landscape

```python
from godot_mcp.mcp_bridge import get_or_create_bridge

wl = await get_or_create_bridge("http://localhost:10864")

result = await wl.call_tool("generate_terrain", {
    "seed": 42,
    "width": 1024,
    "height": 1024,
    "scale": 50.0,
    "octaves": 6,
    "persistence": 0.5,
    "lacunarity": 2.0,
    "erosion_iterations": 10
})
result = await wl.call_tool("apply_biome", {
    "name": "alpine",
    "parameters": {
      "rock_texture": "granite",
      "snow_cap_height": 40,
      "tree_density": 0.05
    }
})
result = await wl.call_tool("export_heightmap", {
    "format": "png",
    "path": "/tmp/terrain_height.png",
    "normal_map": true
})
# wl returns: {"success": true, "heightmap": "/tmp/terrain_height.png",
#              "normalmap": "/tmp/terrain_normal.png", "bounds": {...}}
```

### 2. godot-mcp imports terrain

```python
from godot_mcp.services.godot_bridge import get_bridge
from godot_mcp.services.cfd import load_velocity_field

gb = get_bridge()
gb.connect()

gb.send("import_heightmap", {
    "path": "/tmp/terrain_height.png",
    "name": "AlpineTerrain",
    "size": [50, 50],
    "height_scale": 60.0,
    "material": "res://materials/terrain_alpine.tres"
})

gb.send("set_material", {
    "node": "AlpineTerrain",
    "albedo_texture": "res://textures/alpine_snow_rock.png",
    "normal_texture": "/tmp/terrain_normal.png",
    "uv_scale": [10, 10]
})
```

### 3. Add CFD particles over the terrain

```python
# Load FluidX3D velocity field CSV
vf = load_velocity_field("/data/cfd/wind_flow.csv")
# vf contains: grid_shape, positions, velocities, timesteps

for i, pos in enumerate(vf.positions[:1000]):
    gb.send("spawn_particles", {
        "emitter_name": f"WindParticle_{i}",
        "position": [pos[0], pos[1] + 5, pos[2]],
        "velocity": vf.velocities[i].tolist(),
        "lifetime": 8.0,
        "color": [0.2, 0.6, 1.0],
        "scale": 0.3
    })
```

### 4. Animate wind flow

```python
gb.send("animate_property", {
    "node": "WindParticles",
    "property": "velocity",
    "keyframes": [
        {"time": 0.0, "value": [1, 0, 0]},
        {"time": 2.0, "value": [1.5, 0.2, -0.3]},
        {"time": 4.0, "value": [0.8, -0.1, 0.5]}
    ],
    "loop": true
})
```

### 5. Export for distribution

```python
# HTML5
result = await bridge.call_tool("godot_export_html5", {
    "output_dir": "./build/web",
    "resolution": [1920, 1080]
})

# Tauri desktop
result = await bridge.call_tool("godot_export_tauri", {
    "output_dir": "./build/tauri"
})
```

## Expected Responses

```json
{
  "success": true,
  "message": "Terrain generated: 1024x1024 alpine with 512 particles",
  "data": {
    "triangle_count": 262144,
    "particle_count": 1000,
    "export_paths": {
      "html5": "./build/web/index.html",
      "tauri": "./build/tauri"
    }
  }
}
```

## Notes

- Heightmap resolution: 1024x1024 maps to ~260K triangles at full detail.
- Use LOD (Level of Detail) for large terrains — Godot's GridMap or custom LOD system.
- CFD particles should be GPU particles for performance at 1000+ count.
- Export to HTML5 first for quick iteration, then Tauri for production desktop app.
