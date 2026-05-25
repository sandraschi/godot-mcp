# WorldLabs → Godot Bridge

How worldlabs-mcp generates worlds and godot-mcp loads them.

> **Splat vs mesh:** Marble outputs **SPZ/RAD splats** (pretty) and **GLB** (Chisel collision).  
> godot-mcp imports **GLB only** today. For splat fidelity use Spark viewer or Unity; see [fleet-game-pipeline.md](../docs/fleet-game-pipeline.md).

## Pipeline (mesh path — works now)

```
worldlabs-mcp (generate_world → mesh_url GLB) → _exchange → godot_import_glb → export
```

## Step-by-Step

### 1. worldlabs-mcp generates a world (Marble)

```python
# Via worldlabs-mcp MCP tools (names may vary — check server tool list):
# generate_world_from_text(prompt="cyberpunk alley at night")
# get_world(world_id) → assets.mesh_url, assets.splat_url (SPZ), panorama_url

mesh_glb = "/exchange/models/worldlabs/alley_collision.glb"  # download mesh_url
# splat_spz = ".../visual.spz"  # NOT imported by godot-mcp yet
```

### 1b. Import collision mesh into Godot

```python
from godot_mcp.services.godot_bridge import get_bridge

gb = get_bridge()
gb.connect()

gb.send("import_glb", {
    "path": mesh_glb,
    "name": "WorldCollision",
    "scale": 1.0,
})
```

### 2. (Optional) Heightmap / CFD — legacy sketch

Older docs assumed `generate_terrain` + `import_heightmap` bridge actions. Those are **not** in current godot-mcp bridge — use GLB import instead. CFD particle flow still applies on top of any mesh terrain via `godot_load_velocity_field` + `godot_spawn_particles` (see [freecad-bridge-example.md](freecad-bridge-example.md)).

### 3. Export

```powershell
just little-game-export web mygame
just ship web mygame
```

## Notes

- **Splat (SPZ):** view in worldlabs Spark viewer; Unity via unity3d-mcp; Godot splat import = future work.
- **GLB:** Chisel collision mesh — good for `StaticBody3D` walkable proxy, not the radiance-field look.
- Panorama JPG from Marble can become Godot `PanoramaSkyMaterial` for cheap mood matching.
