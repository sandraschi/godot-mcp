# FreeCAD → Godot Bridge

How qcad-mcp generates DXF/STL geometry, freecad-mcp converts to parametric models,
and godot-mcp imports for real-time visualization.

## Pipeline

```
qcad-mcp (DXF floor plan) → freecad-mcp (extrude → STEP) → godot-mcp (import → PBR → export HTML5)
```

## Step-by-Step

### 1. qcad-mcp generates a floor plan

```python
from godot_mcp.mcp_bridge import get_or_create_bridge

qcad = await get_or_create_bridge("http://localhost:10966")
result = await qcad.call_tool("qcad_draw_rectangle", {
    "x": 0, "y": 0, "width": 10000, "height": 8000
})
# qcad returns: {"success": true, "file": "/tmp/floorplan.dxf"}
```

### 2. freecad-mcp converts to parametric 3D

```python
freecad = await get_or_create_bridge("http://localhost:10944")
result = await freecad.call_tool("import_dxf", {"path": "/tmp/floorplan.dxf"})
result = await freecad.call_tool("extrude", {
    "sketch_name": "FloorPlan",
    "distance": 3000
})
result = await freecad.call_tool("export_step", {"path": "/tmp/building.step"})
# freecad returns: {"success": true, "file": "/tmp/building.step"}
```

### 3. godot-mcp imports and renders

```python
from godot_mcp.services.godot_bridge import get_bridge

gb = get_bridge()
gb.connect()

gb.send("import_step", {
    "path": "/tmp/building.step",
    "name": "Building",
    "material_override": "res://materials/concrete.tres"
})
gb.send("add_directional_light", {
    "name": "Sun",
    "direction": [-0.5, -1.0, -0.3],
    "energy": 2.0
})
gb.send("create_camera_3d", {
    "name": "OrbitCamera",
    "position": [20, 15, 25],
    "target": [0, 1.5, 0]
})

# Export as HTML5
result = await bridge.call_tool("godot_export_html5", {"output_dir": "./build"})
```

## Expected Tool Response Format

All bridge tools return:

```json
{
  "success": true,
  "message": "FreeCAD extruded FloorPlan by 3000mm",
  "data": {
    "file": "/tmp/building.step",
    "volume_mm3": 240000000000
  }
}
```

## Notes

- FreeCAD uses mm as default unit; Godot uses m. Apply a 0.001 scale when importing.
- Always run `gb.connect()` before sending commands; it opens a TCP socket to the Godot editor.
- STL is preferred for mesh-only transfer; STEP preserves parametric history.
