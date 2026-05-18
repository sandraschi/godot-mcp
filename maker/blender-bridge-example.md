# Blender → Godot Bridge

How blender-mcp creates and optimizes meshes, then godot-mcp imports them
for real-time rendering with PBR materials and lighting.

## Pipeline

```
blender-mcp (low-poly tree) → godot-mcp (import → PBR material → light → particles)
```

## Step-by-Step

### 1. blender-mcp generates a low-poly tree

```python
from godot_mcp.mcp_bridge import get_or_create_bridge

blender = await get_or_create_bridge("http://localhost:10848")

# Create trunk
result = await blender.call_tool("create_cylinder", {
    "name": "Trunk",
    "radius": 0.15,
    "depth": 2.0,
    "location": [0, 0, 0]
})

# Create canopy (three spheres stacked)
result = await blender.call_tool("create_uv_sphere", {
    "name": "Canopy_Base",
    "radius": 1.2,
    "location": [0, 1.8, 0]
})
result = await blender.call_tool("create_uv_sphere", {
    "name": "Canopy_Mid",
    "radius": 1.0,
    "location": [0.3, 2.6, -0.2]
})
result = await blender.call_tool("create_uv_sphere", {
    "name": "Canopy_Top",
    "radius": 0.8,
    "location": [-0.2, 3.3, 0.1]
})

# Join and decimate for low-poly
result = await blender.call_tool("join_meshes", {
    "names": ["Trunk", "Canopy_Base", "Canopy_Mid", "Canopy_Top"],
    "name": "LowPolyTree"
})
result = await blender.call_tool("decimate", {
    "name": "LowPolyTree",
    "ratio": 0.3
})
result = await blender.call_tool("export_glb", {
    "path": "/tmp/tree.glb",
    "apply_modifiers": true
})
# blender returns: {"success": true, "file": "/tmp/tree.glb", "triangle_count": 420}
```

### 2. godot-mcp imports and sets PBR material

```python
from godot_mcp.services.godot_bridge import get_bridge

gb = get_bridge()
gb.connect()

gb.send("import_glb", {
    "path": "/tmp/tree.glb",
    "name": "LowPolyTree_01",
    "generate_lod": true
})

gb.send("set_material", {
    "node": "LowPolyTree_01/Trunk",
    "albedo": [0.45, 0.25, 0.1],
    "metallic": 0.0,
    "roughness": 0.9
})

gb.send("set_material", {
    "node": "LowPolyTree_01/Canopy_Base",
    "albedo": [0.1, 0.6, 0.05],
    "metallic": 0.0,
    "roughness": 0.8
})
# Repeat for Canopy_Mid and Canopy_Top with slightly varying greens
```

### 3. Light and instance

```python
gb.send("add_directional_light", {
    "name": "Sun",
    "direction": [-0.5, -1.0, -0.3],
    "energy": 2.0
})

# Instance trees across a terrain grid
for x in range(-10, 11, 3):
    for z in range(-10, 11, 3):
        gb.send("instance_scene", {
            "scene": "LowPolyTree_01",
            "position": [x + random.uniform(-0.5, 0.5), 0, z + random.uniform(-0.5, 0.5)],
            "scale": random.uniform(0.8, 1.4)
        })
```

## Expected Blender Tool Responses

```json
{
  "success": true,
  "message": "Exported LowPolyTree to /tmp/tree.glb (420 triangles, 3 LODs)",
  "data": {
    "file": "/tmp/tree.glb",
    "formats_available": ["glb", "fbx", "obj"],
    "triangle_count": 420
  }
}
```

## Notes

- GLB (binary glTF) is preferred — it packs mesh + materials in one file.
- Material assignments use node pathing; Blender exports material slots.
- Decimate ratio 0.3 works well for low-poly game assets.
- For larger scenes, instance scenes instead of duplicating nodes.
