# Maker Pipeline — Cross-Connect

This directory documents how godot-mcp connects to other "maker" MCP servers
in the fleet ecosystem.

## Pipeline Flow

```
CAD (qcad-mcp) → BIM (freecad-mcp) → Geometry (blender-mcp) → CFD (FluidX3D) → Render (godot-mcp)
                                                                                        ↓
                                                                              HTML5 / Tauri / Resonite
```

## Connected Maker Repos

### freecad-mcp (port 10944/10945)
FreeCAD parametric modeling via MCP.

**Bridge Example:**
```python
from godot_mcp.mcp_bridge import get_or_create_bridge

async def import_from_freecad():
    bridge = await get_or_create_bridge("http://localhost:10944")
    result = await bridge.call_tool("export_stl", {"path": "/tmp/model.stl"})
    # Then use godot-mcp to import:
    from godot_mcp.services.godot_bridge import get_bridge
    gb = get_bridge()
    gb.connect()
    gb.send("import_stl", {"path": "/tmp/model.stl", "name": "FreeCADModel"})
```

### blender-mcp (port 10848/10849)
Blender 3D modeling via MCP.

**Bridge Example:**
Same pattern — bridge calls blender-mcp to generate geometry, then godot-mcp to import and render.

### worldlabs-mcp (port 10864/10865)
World generation via Marble API — **Gaussian splats** (SPZ/RAD) + **Chisel collision mesh** (GLB).

**Bridge Example:** See [worldlabs-bridge-example.md](worldlabs-bridge-example.md).

**Godot today:** import **GLB mesh** with `godot_import_glb`; **splats** not in-engine yet — see [docs/fleet-game-pipeline.md](../docs/fleet-game-pipeline.md).

Handoffs to Blender / Unity / Resonite exist in worldlabs-mcp; Godot uses `_exchange` + GLB path.

### Resonite (XR)
Resonite integration for VR/AR visualization of Godot scenes.

## Typical Workflow

1. **Design** in FreeCAD (via freecad-mcp) → export STL
2. **Detail** in Blender (via blender-mcp) → texture/bake
3. **Simulate** in FluidX3D → CSV velocity field
4. **Visualize** in Godot (via godot-mcp) → import, light, animate, export
5. **Distribute** as HTML5 web game or Tauri native app
