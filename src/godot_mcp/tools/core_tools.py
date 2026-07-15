"""Godot MCP core tools — engine control, STL/velocity import, particles, animation, export."""

import asyncio
import logging
from typing import Annotated, Any, Literal

from fastmcp import Context
from pydantic import Field

from godot_mcp.services.godot_bridge import find_godot, get_bridge, launch_bridge

logger = logging.getLogger("godot-mcp.tools")

_READ_ONLY = {"readonly": True}
_MUTATING = {"mutating": True}


async def godot_status(ctx: Context = None) -> dict:
    """Query the Godot engine for version, scene root node count, and current FPS.

    Calls the GDScript bridge over TCP to read live engine state.

    ## Return Format
    {"success": bool, "data": {"godot_version": str, "node_count": int, "fps": float, "bridge_connected": bool}}

    ## Examples
    await godot_status()
    """
    bridge = get_bridge()
    if not bridge.connected:
        result = await asyncio.to_thread(bridge.connect)
        if not result["success"]:
            godot = await asyncio.to_thread(find_godot)
            hint = ""
            if godot:
                hint = " Godot found — try start_bridge() or just godot-bridge."
            else:
                hint = " Install Godot 4.x (just install-godot) then start the bridge."
            return {
                "success": False,
                "error": result.get("error", "Cannot connect to Godot") + hint,
                "bridge_connected": False,
            }

    result = await asyncio.to_thread(bridge.send, "status")
    if result["success"]:
        result["data"]["bridge_connected"] = True
    return result


async def godot_import_stl(
    path: Annotated[str, Field(description="Absolute path to STL file on disk.")],
    name: Annotated[
        str, Field(description="Node name for the resulting MeshInstance3D.", default="STL_Mesh")
    ] = "STL_Mesh",
    scale: Annotated[
        float, Field(description="Uniform scale factor applied to the mesh.", default=1.0, ge=0.001)
    ] = 1.0,
    position_x: Annotated[float, Field(description="X position in the scene.", default=0.0)] = 0.0,
    position_y: Annotated[float, Field(description="Y position in the scene.", default=0.0)] = 0.0,
    position_z: Annotated[float, Field(description="Z position in the scene.", default=0.0)] = 0.0,
    ctx: Context = None,
) -> dict:
    """Import an STL mesh into the current Godot scene as a MeshInstance3D.

    Reads binary STL vertex/normal data, creates an ArrayMesh, and returns vertex count
    and AABB extents. Use in cross-repo pipeline with qcad-mcp and freecad-mcp.

    ## Return Format
    {"success": bool, "data": {"imported": bool, "name": str, "vertices": int, "aabb": {"size_x": float, "size_y": float, "size_z": float}}}

    ## Examples
    await godot_import_stl(path="C:/uploads/part.stl", name="MyPart", scale=0.01)
    """
    bridge = get_bridge()
    if not bridge.connected:
        result = await asyncio.to_thread(bridge.connect)
        if not result["success"]:
            return {"success": False, "error": result.get("error", "Cannot connect to Godot")}

    return await asyncio.to_thread(
        bridge.send,
        "import_stl",
        {"path": path, "name": name, "scale": scale, "position": {"x": position_x, "y": position_y, "z": position_z}},
    )


async def godot_import_glb(
    path: Annotated[str, Field(description="Absolute path to GLB or GLTF file on disk.")],
    name: Annotated[
        str, Field(description="Node name for the resulting import root.", default="GLB_Import")
    ] = "GLB_Import",
    scale: Annotated[
        float, Field(description="Uniform scale factor applied to the imported scene.", default=1.0, ge=0.001)
    ] = 1.0,
    position_x: Annotated[float, Field(description="X position in the scene.", default=0.0)] = 0.0,
    position_y: Annotated[float, Field(description="Y position in the scene.", default=0.0)] = 0.0,
    position_z: Annotated[float, Field(description="Z position in the scene.", default=0.0)] = 0.0,
    ctx: Context = None,
) -> dict:
    """Import a GLB/GLTF 3D model into the current Godot scene.

    Uses Godot 4.0's native GLTFDocument importer to load meshes, materials,
    and node hierarchy from glTF 2.0 binary (.glb) or text (.gltf) files.
    This unlocks the blender-mcp → godot-mcp pipeline.

    ## Return Format
    {"success": bool, "data": {"imported": bool, "name": str, "total_nodes": int, "mesh_count": int}}

    ## Examples
    await godot_import_glb(path="C:/exchange/robot.glb", name="Robot", scale=0.01)
    await godot_import_glb(path="C:/exchange/scene.gltf")
    """
    bridge = get_bridge()
    if not bridge.connected:
        result = await asyncio.to_thread(bridge.connect)
        if not result["success"]:
            return {"success": False, "error": result.get("error", "Cannot connect to Godot")}

    return await asyncio.to_thread(
        bridge.send,
        "import_glb",
        {
            "path": path,
            "name": name,
            "scale": scale,
            "position": {"x": position_x, "y": position_y, "z": position_z},
        },
    )


async def godot_import_vrm(
    path: Annotated[str, Field(description="Absolute path to .vrm file on disk.")],
    name: Annotated[str, Field(description="Node name for the imported avatar.", default="VRM_Import")] = "VRM_Import",
    ctx: Context = None,
) -> dict:
    """Import a VRM avatar model into the current Godot scene.

    Copies the VRM file into the project, installs the V-Sekai/godot-vrm
    addon if missing, and loads it via Godot's ResourceLoader which
    triggers the VRM addon's glTF extension importer.

    ## Return Format
    {"success": bool, "data": {"imported": bool, "name": str}}

    ## Examples
    await godot_import_vrm(path="~/.avatarmcp/models/Nekomimi-chan.vrm", name="Miko")
    """
    bridge = get_bridge()
    if not bridge.connected:
        result = await asyncio.to_thread(bridge.connect)
        if not result["success"]:
            return {"success": False, "error": result.get("error", "Cannot connect to Godot")}

    import os

    abs_path = os.path.abspath(os.path.expanduser(path))
    return await asyncio.to_thread(bridge.send, "import_vrm", {"path": abs_path, "name": name})


async def godot_list_vrm(
    depot_path: Annotated[
        str, Field(description="Path to VRM depot directory.", default="~/.avatarmcp/models")
    ] = "~/.avatarmcp/models",
    ctx: Context = None,
) -> dict:
    """List available VRM models in the shared avatar depot.

    ## Return Format
    {"success": bool, "data": {"models": list[dict], "depot_path": str}}

    ## Examples
    await godot_list_vrm()
    """
    import glob
    import os

    depot = os.path.abspath(os.path.expanduser(depot_path))
    models = []
    if os.path.isdir(depot):
        for f in sorted(glob.glob(os.path.join(depot, "*.vrm"))):
            name = os.path.splitext(os.path.basename(f))[0]
            size_mb = round(os.path.getsize(f) / (1024 * 1024), 1)
            models.append({"name": name, "path": f, "size_mb": size_mb})
    return {"success": True, "models": models, "depot_path": depot, "count": len(models)}


async def godot_import_obj(
    path: Annotated[str, Field(description="Absolute path to OBJ file on disk.")],
    name: Annotated[
        str, Field(description="Node name for the resulting import root.", default="OBJ_Import")
    ] = "OBJ_Import",
    scale: Annotated[
        float, Field(description="Uniform scale factor applied to the imported mesh.", default=1.0, ge=0.001)
    ] = 1.0,
    position_x: Annotated[float, Field(description="X position in the scene.", default=0.0)] = 0.0,
    position_y: Annotated[float, Field(description="Y position in the scene.", default=0.0)] = 0.0,
    position_z: Annotated[float, Field(description="Z position in the scene.", default=0.0)] = 0.0,
    ctx: Context = None,
) -> dict:
    """Import an OBJ 3D model into the current Godot scene.

    Uses Godot 4.0's ResourceLoader to import Wavefront OBJ files (.obj + .mtl).
    Supports the freecad-mcp CFD streamline export → godot-mcp pipeline.

    ## Return Format
    {"success": bool, "data": {"imported": bool, "name": str}}

    ## Examples
    await godot_import_obj(path="C:/exchange/streamlines.obj", name="CFD_Streamlines")
    """
    bridge = get_bridge()
    if not bridge.connected:
        result = await asyncio.to_thread(bridge.connect)
        if not result["success"]:
            return {"success": False, "error": result.get("error", "Cannot connect to Godot")}

    return await asyncio.to_thread(
        bridge.send,
        "import_obj",
        {
            "path": path,
            "name": name,
            "scale": scale,
            "position": {"x": position_x, "y": position_y, "z": position_z},
        },
    )


async def godot_play_animation(
    root_name: Annotated[
        str,
        Field(
            description="Imported GLB root node name to search (empty = entire scene).",
            default="",
        ),
    ] = "",
    animation: Annotated[
        str,
        Field(
            description="Animation clip name to play. Empty lists available clips.",
            default="",
        ),
    ] = "",
    loop: Annotated[bool, Field(description="Loop the animation.", default=True)] = True,
    speed_scale: Annotated[float, Field(description="Playback speed multiplier.", default=1.0, ge=0.01, le=10.0)] = 1.0,
    ctx: Context = None,
) -> dict:
    """Play or list animations on an imported GLB character via AnimationPlayer.

    Use after godot_import_glb with a GLB that includes baked animation tracks
    (typical path: blender-mcp VMD bake -> GLB export -> godot_import_glb).

    ## Return Format
    Playing: {"success": bool, "data": {"playing": true, "animation": str, "available_animations": list}}
    Listing: {"success": bool, "data": {"listed": true, "animations": list}}

    ## Examples
    await godot_play_animation(root_name="Dancer", animation="")
    await godot_play_animation(root_name="Dancer", animation="dance_01", loop=True)
    """
    bridge = get_bridge()
    if not bridge.connected:
        result = await asyncio.to_thread(bridge.connect)
        if not result["success"]:
            return {"success": False, "error": result.get("error", "Cannot connect to Godot")}

    return await asyncio.to_thread(
        bridge.send,
        "play_animation",
        {
            "root_name": root_name,
            "animation": animation,
            "loop": loop,
            "speed_scale": speed_scale,
        },
    )


async def godot_load_velocity_field(
    csv_path: Annotated[str, Field(description="Absolute path to CSV velocity field file (x,y,z,vx,vy,vz columns).")],
    name: Annotated[
        str, Field(description="Data node name for the velocity field.", default="VelocityField")
    ] = "VelocityField",
    ctx: Context = None,
) -> dict:
    """Load a CSV velocity field dataset into the Godot scene.

    Parses CFD/FluidX3D-style CSV with position and vector columns. Stores points and
    vectors as node metadata for downstream particle animation.

    ## Return Format
    {"success": bool, "data": {"loaded": bool, "name": str, "point_count": int, "bbox": {"min_x": float, ..., "max_z": float}}}

    ## Examples
    await godot_load_velocity_field(csv_path="C:/data/velocity_field.csv", name="FlowData")
    """
    bridge = get_bridge()
    if not bridge.connected:
        result = await asyncio.to_thread(bridge.connect)
        if not result["success"]:
            return {"success": False, "error": result.get("error", "Cannot connect to Godot")}

    return await asyncio.to_thread(bridge.send, "load_velocity_field", {"csv_path": csv_path, "name": name})


async def godot_spawn_particles(
    ctx: Context = None,
    count: Annotated[int, Field(description="Number of GPU particles.", default=1000, ge=1, le=1000000)] = 1000,
    name: Annotated[
        str, Field(description="Node name for the GPUParticles3D system.", default="StreamlineParticles")
    ] = "StreamlineParticles",
    color: Annotated[
        str, Field(description="Hex color for particle material (e.g. '#00aaff').", default="#00aaff")
    ] = "#00aaff",
    spread_x: Annotated[float, Field(description="Emission box X extent.", default=5.0)] = 5.0,
    spread_y: Annotated[float, Field(description="Emission box Y extent.", default=5.0)] = 5.0,
    spread_z: Annotated[float, Field(description="Emission box Z extent.", default=5.0)] = 5.0,
) -> dict:
    """Create a GPUParticles3D system in the Godot scene.

    Sets up a particle system with configurable emission box, count, and draw pass
    sphere mesh. Use after godot_load_velocity_field for CFD visualisation.

    ## Return Format
    {"success": bool, "data": {"spawned": bool, "name": str, "count": int, "particle_system": str}}

    ## Examples
    await godot_spawn_particles(count=5000, name="CFD_Flow", spread_x=10, spread_y=10, spread_z=10)
    """
    bridge = get_bridge()
    if not bridge.connected:
        result = await asyncio.to_thread(bridge.connect)
        if not result["success"]:
            return {"success": False, "error": result.get("error", "Cannot connect to Godot")}

    return await asyncio.to_thread(
        bridge.send,
        "spawn_particles",
        {
            "count": count,
            "name": name,
            "color": color,
            "spread_x": spread_x,
            "spread_y": spread_y,
            "spread_z": spread_z,
        },
    )


async def godot_animate_streamlines(
    ctx: Context = None,
    velocity_field: Annotated[
        str, Field(description="Name of the velocity field data node.", default="VelocityField")
    ] = "VelocityField",
    particle_system: Annotated[
        str, Field(description="Name of the GPUParticles3D node to animate.", default="StreamlineParticles")
    ] = "StreamlineParticles",
    speed: Annotated[float, Field(description="Animation speed multiplier.", default=1.0)] = 1.0,
) -> dict:
    """Animate GPU particles along a previously loaded velocity field.

    Adjusts particle emission box to match velocity field bounding box, sets initial
    velocity range from field vectors, and enables particle emission.

    ## Return Format
    {"success": bool, "data": {"animated": bool, "particle_system": str, "velocity_field": str, "speed_multiplier": float, "point_count": int}}

    ## Examples
    await godot_animate_streamlines(velocity_field="FlowData", particle_system="CFD_Flow", speed=2.0)
    """
    bridge = get_bridge()
    if not bridge.connected:
        result = await asyncio.to_thread(bridge.connect)
        if not result["success"]:
            return {"success": False, "error": result.get("error", "Cannot connect to Godot")}

    return await asyncio.to_thread(
        bridge.send,
        "animate_streamlines",
        {"velocity_field": velocity_field, "particle_system": particle_system, "speed": speed},
    )


async def godot_create_camera(
    ctx: Context = None,
    name: Annotated[str, Field(description="Node name for the camera.", default="MCP_Camera")] = "MCP_Camera",
    position_x: Annotated[float, Field(description="Camera X position.", default=0.0)] = 0.0,
    position_y: Annotated[float, Field(description="Camera Y position.", default=5.0)] = 5.0,
    position_z: Annotated[float, Field(description="Camera Z position.", default=10.0)] = 10.0,
    look_at_x: Annotated[float, Field(description="Look-at target X.", default=0.0)] = 0.0,
    look_at_y: Annotated[float, Field(description="Look-at target Y.", default=0.0)] = 0.0,
    look_at_z: Annotated[float, Field(description="Look-at target Z.", default=0.0)] = 0.0,
    fov: Annotated[float, Field(description="Field of view in degrees.", default=75.0, ge=1.0, le=179.0)] = 75.0,
) -> dict:
    """Create a Camera3D with orbit controls in the Godot scene.

    Sets the camera as active (current=true), attaches a GDScript-based orbit controller
    with mouse drag and scroll-zoom support.

    ## Return Format
    {"success": bool, "data": {"created": bool, "name": str, "fov": float, "position": {"x": float, "y": float, "z": float}}}

    ## Examples
    await godot_create_camera(name="RenderCam", position_y=10, position_z=15, fov=60)
    """
    bridge = get_bridge()
    if not bridge.connected:
        result = await asyncio.to_thread(bridge.connect)
        if not result["success"]:
            return {"success": False, "error": result.get("error", "Cannot connect to Godot")}

    return await asyncio.to_thread(
        bridge.send,
        "create_camera",
        {
            "name": name,
            "position": {"x": position_x, "y": position_y, "z": position_z},
            "look_at": {"x": look_at_x, "y": look_at_y, "z": look_at_z},
            "fov": fov,
        },
    )


async def godot_add_light(
    ctx: Context = None,
    light_type: Annotated[
        str, Field(description="Light type: 'directional', 'ambient', or 'omni'.", default="directional")
    ] = "directional",
    name: Annotated[str, Field(description="Node name for the light.")] = "",
    intensity: Annotated[float, Field(description="Light energy/intensity.", default=1.0, ge=0.0)] = 1.0,
    position_x: Annotated[float, Field(description="Light X position (omni only).", default=5.0)] = 5.0,
    position_y: Annotated[float, Field(description="Light Y position (omni only).", default=5.0)] = 5.0,
    position_z: Annotated[float, Field(description="Light Z position (omni only).", default=5.0)] = 5.0,
) -> dict:
    """Add a dynamic light source to the Godot scene.

    Supports directional (sun-like parallel rays), ambient (environment fill), and
    omni (point) light types.

    ## Return Format
    {"success": bool, "data": {"created": bool, "name": str, "type": str, "intensity": float}}

    ## Examples
    await godot_add_light(light_type="directional", intensity=2.0)
    await godot_add_light(light_type="omni", name="KeyLight", position_x=0, position_y=3, position_z=5)
    await godot_add_light(light_type="ambient", intensity=0.3)
    """
    bridge = get_bridge()
    if not bridge.connected:
        result = await asyncio.to_thread(bridge.connect)
        if not result["success"]:
            return {"success": False, "error": result.get("error", "Cannot connect to Godot")}

    params: dict = {"type": light_type, "intensity": intensity}
    if name:
        params["name"] = name
    else:
        params["name"] = f"MCP_Light_{light_type}"
    if light_type in ("omni", "spot"):
        params["position"] = {"x": position_x, "y": position_y, "z": position_z}

    return await asyncio.to_thread(bridge.send, "add_light", params)


async def godot_set_material(
    node: Annotated[str, Field(description="Name of the target MeshInstance3D node.")],
    color: Annotated[str, Field(description="Hex albedo color (e.g. '#ff8844').", default="#ffffff")] = "#ffffff",
    roughness: Annotated[
        float, Field(description="PBR roughness (0 = mirror, 1 = matte).", default=0.5, ge=0.0, le=1.0)
    ] = 0.5,
    ctx: Context = None,
) -> dict:
    """Assign a StandardMaterial3D (PBR) to a mesh node in the Godot scene.

    Sets albedo color and roughness. The node must already exist in the scene tree.

    ## Return Format
    {"success": bool, "data": {"set": bool, "node": str, "color": str, "roughness": float}}

    ## Examples
    await godot_set_material(node="STL_Mesh", color="#4488ff", roughness=0.3)
    """
    bridge = get_bridge()
    if not bridge.connected:
        result = await asyncio.to_thread(bridge.connect)
        if not result["success"]:
            return {"success": False, "error": result.get("error", "Cannot connect to Godot")}

    return await asyncio.to_thread(bridge.send, "set_material", {"node": node, "color": color, "roughness": roughness})


async def godot_export_web(
    ctx: Context = None,
    output_path: Annotated[
        str,
        Field(
            description="Output path for the export (absolute or res:// path).", default="user://export/web/index.html"
        ),
    ] = "user://export/web/index.html",
    resolution_x: Annotated[int, Field(description="Viewport width in pixels.", default=1280, ge=64)] = 1280,
    resolution_y: Annotated[int, Field(description="Viewport height in pixels.", default=720, ge=64)] = 720,
) -> dict:
    """Export the current Godot scene to HTML5/WebAssembly.

    Attempts in-editor export via the GDScript bridge first. Falls back to
    godot --headless --export-release if the bridge reports templates unavailable.

    ## Return Format
    {"success": bool, "data": {"exported": bool, "message": str, "output_path": str}}

    ## Examples
    await godot_export_web(output_path="C:/builds/godot-web/index.html")
    """
    bridge = get_bridge()
    if bridge.connected:
        result = await asyncio.to_thread(bridge.send, "export_web", {"output_path": output_path}, 300.0)
        if result.get("success") and result.get("data", {}).get("exported"):
            return result

    # Fallback: run godot CLI
    import os
    import shutil
    import subprocess
    from pathlib import Path

    godot_exe = os.getenv("GODOT_PATH", "")
    if not godot_exe or not Path(godot_exe).is_file():
        godot_exe = shutil.which("godot") or shutil.which("godot.exe") or ""
    if not godot_exe:
        candidates = [
            r"C:\Program Files\Godot\godot.exe",
            r"C:\Program Files (x86)\Godot\godot.exe",
            str(Path.home() / "Godot" / "godot.exe"),
        ]
        for p in candidates:
            if Path(p).is_file():
                godot_exe = p
                break

    if not godot_exe:
        return {
            "success": False,
            "error": "Godot executable not found. Set GODOT_PATH env var or install Godot.",
        }

    # Build export command
    abs_output = str(Path(output_path).resolve())
    output_dir = str(Path(abs_output).parent)
    os.makedirs(output_dir, exist_ok=True)

    cmd = [
        godot_exe,
        "--headless",
        "--export-release",
        "Web",
        abs_output,
    ]

    try:
        proc = await asyncio.to_thread(
            subprocess.run,
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(Path(__file__).resolve().parent.parent.parent.parent),
        )
        if proc.returncode == 0 and Path(abs_output).exists():
            return {
                "success": True,
                "data": {
                    "exported": True,
                    "message": f"Exported to {abs_output}",
                    "output_path": abs_output,
                },
            }
        return {
            "success": False,
            "error": f"Export failed (code {proc.returncode}): {proc.stderr[:500]}",
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Export timed out after 300s"}
    except Exception as e:
        return {"success": False, "error": f"Export error: {e}"}


async def godot_read_scene_tree(ctx: Context = None) -> dict:
    """Read the full Godot scene tree as a nested JSON structure.

    Returns the root node with all children recursively, showing name, type, and path
    for each node in the tree.

    ## Return Format
    {"success": bool, "data": {"scene_tree": {"name": str, "type": str, "path": str, "children": [...]}, "node_count": int}}

    ## Examples
    await godot_read_scene_tree()
    """
    bridge = get_bridge()
    if not bridge.connected:
        result = await asyncio.to_thread(bridge.connect)
        if not result["success"]:
            return {"success": False, "error": result.get("error", "Cannot connect to Godot")}

    return await asyncio.to_thread(bridge.send, "read_scene_tree")


async def godot_set_config(
    section: Annotated[str, Field(description="Config section name (e.g. 'application', 'rendering').")],
    key: Annotated[str, Field(description="Config key to set.")],
    value: Annotated[str, Field(description="Config value (string).")],
    ctx: Context = None,
) -> dict:
    """Write a setting to the project.godot configuration file.

    Modifies the res://project.godot INI-style file via ConfigFile API.

    ## Return Format
    {"success": bool, "data": {"updated": bool, "section": str, "key": str, "value": str}}

    ## Examples
    await godot_set_config(section="application", key="config/name", value="My CFD Project")
    await godot_set_config(section="rendering", key="quality/driver/driver_name", value="GLES3")
    """
    bridge = get_bridge()
    if not bridge.connected:
        result = await asyncio.to_thread(bridge.connect)
        if not result["success"]:
            return {"success": False, "error": result.get("error", "Cannot connect to Godot")}

    return await asyncio.to_thread(bridge.send, "set_config", {"section": section, "key": key, "value": value})


async def godot_headless_verify(
    ctx: Context = None,
    script: Annotated[
        str, Field(description="Path to a GDScript file to verify in headless mode.", default="res://dev/mcp_verify.gd")
    ] = "res://dev/mcp_verify.gd",
) -> dict:
    """Check whether the Godot engine is running in headless mode.

    Returns the headless status and a suggested CLI command for headless script
    execution with godot --headless --script.

    ## Return Format
    {"success": bool, "data": {"headless": bool, "script_path": str, "message": str}}

    ## Examples
    await godot_headless_verify(script="res://tests/mcp_headless_test.gd")
    """
    bridge = get_bridge()
    if not bridge.connected:
        result = await asyncio.to_thread(bridge.connect)
        if not result["success"]:
            return {"success": False, "error": result.get("error", "Cannot connect to Godot")}

    return await asyncio.to_thread(bridge.send, "headless_verify", {"script": script})


async def godot_capture_viewport(
    output_path: Annotated[
        str | None, Field(description="Absolute path for the PNG (optional, auto-generated if omitted).", default=None)
    ] = None,
    ctx: Context = None,
) -> dict:
    """Capture the current Godot viewport as a PNG image.

    Saves a screenshot of the active viewport to disk and returns the path
    and dimensions. The Godot bridge must be connected.

    ## Return Format
    {"success": bool, "data": {"path": str, "width": int, "height": int, "format": "png"}}

    ## Examples
    await godot_capture_viewport()
    await godot_capture_viewport(output_path="C:/captures/scene.png")
    """
    bridge = get_bridge()
    if not bridge.connected:
        result = await asyncio.to_thread(bridge.connect)
        if not result["success"]:
            return {"success": False, "error": result.get("error", "Cannot connect to Godot")}

    params = {}
    if output_path:
        params["output_path"] = output_path
    return await asyncio.to_thread(bridge.send, "capture_viewport", params, timeout=30)


async def godot_simulate_input(
    actions: Annotated[
        list[dict],
        Field(
            description="""List of input actions. Each action dict selects a format by its keys:

**Key press/release** (legacy, backward-compat):
  {"key": "Space", "pressed": true, "hold_ms": 100}

**Action press with analog strength:**
  {"action": "move_left", "strength": 1.0}
  {"action": "jump", "pressed": false}

**Joypad axis:**
  {"joypad": {"device": 0, "axis": 0, "value": -0.8}}

**Joypad button:**
  {"joypad": {"device": 0, "button": 0, "pressed": true}}

**Mouse look (relative motion):**
  {"mouse_look": {"dx": 15, "dy": -3}}

**Mouse button click:**
  {"mouse_button": {"button": 1, "pressed": true, "position": {"x": 960, "y": 540}}}

**Text input (per-character key events):**
  {"type": "text", "text": "hello"}""",
        ),
    ],
    ctx: Context = None,
) -> dict:
    """Simulate input in the Godot engine — keyboard, action, joypad, mouse, and text.

    Dispatches each action dict by its key signature. Legacy ``{"key": ...}``
    entries use ``InputEventKey`` with optional hold-timed release. New formats
    use ``Input.action_press`` (analog actions), ``InputEventJoypadMotion`` /
    ``InputEventJoypadButton``, ``InputEventMouseMotion``, ``InputEventMouseButton``,
    and per-character ``InputEventKey`` (text).

    ## Return Format
    {"success": bool, "data": {"actions_processed": int, "results": [...]}}

    ## Examples
    # Legacy key press with hold
    await godot_simulate_input(actions=[{"key": "Space", "pressed": true, "hold_ms": 100}])

    # Analog action
    await godot_simulate_input(actions=[{"action": "move_left", "strength": 0.5}])

    # Joypad axis
    await godot_simulate_input(actions=[{"joypad": {"axis": 0, "value": -0.8}}])

    # Mouse look
    await godot_simulate_input(actions=[{"mouse_look": {"dx": 45, "dy": -10}}])

    # Text input
    await godot_simulate_input(actions=[{"type": "text", "text": "hello"}])

    # Mixed
    await godot_simulate_input(actions=[
        {"action": "move_left", "strength": 1.0},
        {"joypad": {"axis": 0, "value": -0.8}},
        {"mouse_look": {"dx": 200, "dy": 0}},
    ])
    """
    bridge = get_bridge()
    if not bridge.connected:
        result = await asyncio.to_thread(bridge.connect)
        if not result["success"]:
            return {"success": False, "error": result.get("error", "Cannot connect to Godot")}

    return await asyncio.to_thread(bridge.send, "simulate_input", {"actions": actions}, timeout=30)


async def godot_read_node(
    node: Annotated[
        str,
        Field(description="Node path (e.g. 'Player' or 'World/Enemy') or node name to search for recursively."),
    ],
    ctx: Context = None,
) -> dict:
    """Read properties of a single node by path or name.

    Returns effective properties (position, rotation, scale, velocity, visible,
    current_animation) and child list. Lightweight alternative to read_scene_tree
    when you only need one node. If the node defines ``_mcp_state()``, that takes
    priority over auto-collected properties.

    ## Return Format
    {"success": bool, "data": {"node": {"name": str, "type": str, "path": str, ...}}}

    ## Examples
    await godot_read_node(node="Player")
    await godot_read_node(node="World/Camera3D")
    """
    bridge = get_bridge()
    if not bridge.connected:
        result = await asyncio.to_thread(bridge.connect)
        if not result["success"]:
            return {"success": False, "error": result.get("error", "Cannot connect to Godot")}

    return await asyncio.to_thread(bridge.send, "read_node", {"node": node}, timeout=10)


async def godot_inspect_resource(
    path: Annotated[
        str,
        Field(
            description="Resource path (e.g. 'res://assets/player.tres', 'res://tileset.tres'). Loaded via ResourceLoader inside the Godot engine."
        ),
    ],
    ctx: Context = None,
) -> dict:
    """Inspect a resource file loaded in the Godot engine.

    Type-aware inspection for:
    - **SpriteFrames**: animation names, frame counts, speed, loop
    - **TileSet**: source count, source IDs, tile counts
    - **Material** (StandardMaterial3D): albedo, roughness, metallic, emission
    - **ShaderMaterial**: shader path, parameter list with values
    - **Texture2D**: width, height, format, mipmap status
    - **Generic**: property list for any other resource type

    ## Return Format
    {"success": bool, "data": {"resource": {"path": str, "type": str, ...}}}

    ## Examples
    await godot_inspect_resource(path="res://characters/player.tres")
    await godot_inspect_resource(path="res://materials/ground.material")
    """
    bridge = get_bridge()
    if not bridge.connected:
        result = await asyncio.to_thread(bridge.connect)
        if not result["success"]:
            return {"success": False, "error": result.get("error", "Cannot connect to Godot")}

    return await asyncio.to_thread(bridge.send, "inspect_resource", {"path": path}, timeout=15)


_tilemap_literals = Literal["read", "set_cell", "erase_cell", "clear"]


async def godot_tilemap(
    operation: Annotated[
        _tilemap_literals,
        Field(
            description="Operation: ``read`` returns all used cells, ``set_cell`` writes cells (requires ``cells`` param), ``erase_cell`` removes cells (requires ``coords`` param), ``clear`` removes all cells."
        ),
    ],
    node: Annotated[
        str,
        Field(description="Node path or name of a TileMapLayer or GridMap node in the scene."),
    ],
    cells: Annotated[
        list[dict] | None,
        Field(
            description='List of cell data for ``set_cell``: ``[{"x": 0, "y": 0, "source_id": 1, "atlas_coords": {"x": 0, "y": 0}, "alternative_tile": 0}]``.',
            default=None,
        ),
    ] = None,
    coords: Annotated[
        list[dict] | None,
        Field(
            description='List of coordinates for ``erase_cell``: ``[{"x": 0, "y": 0}]``.',
            default=None,
        ),
    ] = None,
    ctx: Context = None,
) -> dict:
    """Read or edit TileMapLayer and GridMap cells.

    For TileMapLayer: reads cell source IDs, atlas coordinates, and alternative
    tiles. For GridMap: reads cell item IDs and orientations. The ``set_cell``
    operation writes cells that would otherwise be base64-encoded in the ``.tscn``
    file — this is the only practical way for agents to edit tilemap data.

    ## Return Format
    {"success": bool, "data": {"node": str, "type": str, "cells": [...], "cell_count": int}}

    ## Examples
    await godot_tilemap(operation="read", node="GroundLayer")
    await godot_tilemap(operation="set_cell", node="GroundLayer", cells=[{"x": 5, "y": 3, "source_id": 0, "atlas_coords": {"x": 2, "y": 1}}])
    await godot_tilemap(operation="erase_cell", node="GroundLayer", coords=[{"x": 5, "y": 3}])
    await godot_tilemap(operation="clear", node="GroundLayer")
    """
    bridge = get_bridge()
    if not bridge.connected:
        result = await asyncio.to_thread(bridge.connect)
        if not result["success"]:
            return {"success": False, "error": result.get("error", "Cannot connect to Godot")}

    if operation == "read":
        return await asyncio.to_thread(bridge.send, "tilemap_read", {"node": node}, timeout=10)
    else:
        params: dict = {"node": node, "operation": operation}
        if cells is not None:
            params["cells"] = cells
        if coords is not None:
            params["coords"] = coords
        return await asyncio.to_thread(bridge.send, "tilemap_edit", params, timeout=10)


_anim_literals = Literal[
    "list_animations", "list_tracks", "list_keyframes", "insert_keyframe", "remove_keyframe", "set_interpolation"
]


async def godot_animation(
    operation: Annotated[
        _anim_literals,
        Field(
            description="Operation: ``list_animations`` (list all), ``list_tracks`` (tracks in one anim), ``list_keyframes`` (keys in one track), ``insert_keyframe``, ``remove_keyframe``, ``set_interpolation``."
        ),
    ],
    node: Annotated[
        str,
        Field(description="Node path or name of an AnimationPlayer node in the scene."),
    ],
    animation: Annotated[
        str | None,
        Field(
            description="Animation name. Required for: list_tracks, list_keyframes, insert_keyframe, remove_keyframe, set_interpolation.",
            default=None,
        ),
    ] = None,
    track: Annotated[
        int | None,
        Field(
            description="Track index. Required for: list_keyframes, insert_keyframe, remove_keyframe, set_interpolation.",
            default=None,
        ),
    ] = None,
    time: Annotated[
        float | None,
        Field(description="Time position in seconds. Required for: insert_keyframe, remove_keyframe.", default=None),
    ] = None,
    value: Annotated[
        Any,
        Field(description="Keyframe value. Required for: insert_keyframe.", default=None),
    ] = None,
    mode: Annotated[
        str | None,
        Field(
            description="Interpolation mode for set_interpolation: 'nearest', 'linear', 'cubic', 'linear_angle', 'cubic_angle'.",
            default=None,
        ),
    ] = None,
    ctx: Context = None,
) -> dict:
    """Read and edit animation keyframes and tracks on an AnimationPlayer.

    Query existing animations, inspect their tracks down to individual keyframes,
    insert or remove keyframes, and change track interpolation modes.

    ## Return Format
    {"success": bool, "data": {"node": str, "animation": str, ...}}

    ## Examples
    await godot_animation(operation="list_animations", node="AnimationPlayer")
    await godot_animation(operation="list_tracks", node="AnimationPlayer", animation="walk")
    await godot_animation(operation="list_keyframes", node="AnimationPlayer", animation="walk", track=0)
    await godot_animation(operation="insert_keyframe", node="AnimationPlayer", animation="walk", track=0, time=1.5, value=100.0)
    await godot_animation(operation="remove_keyframe", node="AnimationPlayer", animation="walk", track=0, time=1.5)
    await godot_animation(operation="set_interpolation", node="AnimationPlayer", animation="walk", track=0, mode="cubic")
    """
    bridge = get_bridge()
    if not bridge.connected:
        result = await asyncio.to_thread(bridge.connect)
        if not result["success"]:
            return {"success": False, "error": result.get("error", "Cannot connect to Godot")}

    params: dict = {"node": node, "operation": operation}
    if animation is not None:
        params["animation"] = animation
    if track is not None:
        params["track"] = track
    if time is not None:
        params["time"] = time
    if value is not None:
        params["value"] = value
    if mode is not None:
        params["mode"] = mode

    timeout = 30 if operation == "insert_keyframe" else 10
    return await asyncio.to_thread(bridge.send, "animation_edit", params, timeout=timeout)


_profile_literals = Literal["snapshot", "enable", "history"]


async def godot_profile(
    operation: Annotated[
        _profile_literals,
        Field(
            description="Operation: ``snapshot`` (read all current metrics), ``enable`` (start/stop auto-sampling), ``history`` (analyze sampled frames for spikes)."
        ),
    ],
    enabled: Annotated[
        bool | None,
        Field(description="Toggle auto-sampling on/off (used with ``enable`` operation).", default=None),
    ] = None,
    ctx: Context = None,
) -> dict:
    """Read Godot performance metrics and detect frame spikes.

    Snapshots read 14 metrics from Godot's ``Performance`` singleton: FPS, process
    time, physics time, memory (static/dynamic), object/node/orphan counts, render
    draw calls/primitives/video memory, physics active objects/collisions, audio
    latency.

    Enable auto-sampling to record a rolling history of 300 frames, then use
    ``history`` to detect anomalous spikes (>2 stddev from the window mean).

    ## Return Format
    {"success": bool, "data": {"snapshot": dict, "enabled": bool, "spikes": list}}

    ## Examples
    await godot_profile(operation="snapshot")
    await godot_profile(operation="enable", enabled=True)
    # ... play some frames ...
    await godot_profile(operation="history")
    """
    bridge = get_bridge()
    if not bridge.connected:
        result = await asyncio.to_thread(bridge.connect)
        if not result["success"]:
            return {"success": False, "error": result.get("error", "Cannot connect to Godot")}

    if operation == "snapshot":
        return await asyncio.to_thread(bridge.send, "profile_snapshot", {}, timeout=10)
    elif operation == "enable":
        return await asyncio.to_thread(
            bridge.send, "profile_enable", {"enabled": enabled if enabled is not None else True}, timeout=10
        )
    elif operation == "history":
        return await asyncio.to_thread(bridge.send, "profile_history", {}, timeout=10)
    return {"success": False, "error": f"Unknown operation: {operation}"}


async def godot_help(
    topic: Annotated[
        str | None,
        Field(
            description="Optional topic: 'playtesting', 'scene', 'import', 'input', 'animation', 'tilemap', 'publishing', 'profiling', 'docs', or omit for the full index.",
            default=None,
        ),
    ] = None,
    ctx: Context = None,
) -> dict:
    """Get context-aware help for godot-mcp tools and workflows.

    Returns markdown with tool categories, example commands, and usage tips.
    Use ``topic`` to drill into a specific area.

    ## Return Format
    {"success": bool, "help": str, "topic": str}

    ## Examples
    await godot_help()
    await godot_help(topic="playtesting")
    await godot_help(topic="scene")
    """
    index = """# godot-mcp Help

**85+ tools** for Godot 4 engine control via MCP.

## Categories

| Topic | Tools | Description |
|-------|-------|-------------|
| `playtesting` | game_time, step_until, simulate_input, state_digest, capture_viewport | Deterministic game testing with frozen clock |
| `scene` | scene, read_scene_tree, read_node, add_node, remove_node, modify_node | Scene tree management |
| `import` | import_stl, import_glb, import_obj | 3D model import |
| `input` | simulate_input | Keyboard, action, joypad, mouse, text injection |
| `animation` | play_animation, animation | Playback and keyframe authoring |
| `tilemap` | tilemap | TileMapLayer and GridMap cell read/write |
| `material` | set_material, inspect_resource | PBR material and resource inspection |
| `particles` | spawn_particles, animate_streamlines, load_velocity_field | GPU particle systems |
| `camera` | create_camera, add_light, capture_viewport | Scene setup |
| `profiling` | profile | Performance metrics and spike detection |
| `publishing` | itch_ops, steam_ops | itch.io and Steam publishing |
| `docs` | godot_docs | Fetch Godot documentation |

## Quick Start

```python
# Check bridge
await godot_status()

# Freeze and step
await godot_game_time(action="freeze")
await godot_simulate_input(actions=[{"action": "jump", "strength": 1.0}])
await godot_step_until(condition="get_node('Player').is_on_floor()")
await godot_capture_viewport()
```

See ``docs/TOOLS.md`` for the full reference.
"""
    topics = {
        "playtesting": """## Deterministic Playtesting

Freeze the game clock, inject input, step frame-by-step until a condition, capture results.

```python
await godot_game_time(action="freeze")
await godot_simulate_input(actions=[{"action": "jump", "strength": 1.0}])
step = await godot_step_until(condition="get_node('Player').is_on_floor()")
state = await godot_state_digest(node_names=["Player"])
await godot_capture_viewport()
```

**Tools**: godot_game_time, godot_step_until, godot_simulate_input, godot_state_digest, godot_capture_viewport
""",
        "scene": """## Scene Management

Read or modify the Godot scene tree.

```python
# Read
await godot_read_scene_tree()
await godot_read_node(node="Player")

# Write
await godot_scene(operation="add_node", parent=".", node_type="Camera3D", name="Cam")
await godot_scene(operation="modify_node", node_path="Player", property_name="position", value={"x": 0, "y": 5, "z": 0})
await godot_scene(operation="save_scene")
```

**Tools**: godot_scene, godot_read_scene_tree, godot_read_node
""",
        "import": """## 3D Model Import

Import STL, GLB/GLTF, or OBJ files into the scene.

```python
await godot_import_glb(path="/models/robot.glb", name="Robot", scale=0.01)
await godot_import_stl(path="/models/part.stl", name="Bracket")
```

**Tools**: godot_import_stl, godot_import_glb, godot_import_obj
""",
        "input": """## Input Injection

Simulate keyboard, action, joypad, mouse, or text input.

```python
# Analog action
await godot_simulate_input(actions=[{"action": "move_left", "strength": 0.5}])

# Mouse look
await godot_simulate_input(actions=[{"mouse_look": {"dx": 45, "dy": -10}}])

# Joypad
await godot_simulate_input(actions=[{"joypad": {"axis": 0, "value": -0.8}}])

# Legacy key
await godot_simulate_input(actions=[{"key": "Space", "hold_ms": 100}])
```

**Tools**: godot_simulate_input
""",
        "animation": """## Animation

Query and edit AnimationPlayer keyframes.

```python
# List
await godot_animation(operation="list_animations", node="AnimationPlayer")
await godot_animation(operation="list_tracks", node="AnimationPlayer", animation="walk")
await godot_animation(operation="list_keyframes", node="AnimationPlayer", animation="walk", track=0)

# Edit
await godot_animation(operation="insert_keyframe", node="AnimationPlayer", animation="walk", track=0, time=1.5, value=100.0)
await godot_animation(operation="set_interpolation", node="AnimationPlayer", animation="walk", track=0, mode="cubic")

# Play
await godot_play_animation(root_name="Robot", animation="dance_01")
```

**Tools**: godot_animation, godot_play_animation
""",
        "tilemap": """## TileMap & GridMap

Read and edit TileMapLayer and GridMap cells.

```python
# Read all cells
await godot_tilemap(operation="read", node="GroundLayer")

# Set a cell
await godot_tilemap(operation="set_cell", node="GroundLayer", cells=[{"x": 5, "y": 3, "source_id": 0, "atlas_coords": {"x": 2, "y": 1}}])

# Clear
await godot_tilemap(operation="clear", node="GroundLayer")
```

**Tools**: godot_tilemap
""",
        "publishing": """## Publishing

Ship games to itch.io and Steam.

```python
# itch.io
await itch_ops(operation="status")
await ship_to_itch()

# Steam
await steam_ops(operation="status")
await ship_to_steam()
```

**Tools**: itch_ops, steam_ops, ship_to_itch, ship_to_steam
""",
        "profiling": """## Profiling

Read performance metrics and detect frame spikes.

```python
# One-shot snapshot
await godot_profile(operation="snapshot")

# Auto-sample 300 frames
await godot_profile(operation="enable", enabled=True)
# ... play some frames ...
await godot_profile(operation="history")
```

**Tools**: godot_profile
""",
        "docs": """## Godot Documentation

Fetch Godot class reference docs as markdown.

```python
await godot_docs(query="Node3D")
await godot_docs(query="AnimationPlayer", section="methods")
```

**Tools**: godot_docs
""",
    }

    if topic and topic.lower() in topics:
        return {"success": True, "help": topics[topic.lower()], "topic": topic}
    return {"success": True, "help": index, "topic": "index"}


async def godot_import_splat(
    path: Annotated[str, Field(description="Path to .ply or .spz (compressed) 3D Gaussian Splatting file.")],
    name: Annotated[
        str, Field(description="Node name for the resulting MultiMeshInstance3D.", default="SplatCloud")
    ] = "SplatCloud",
    max_splats: Annotated[
        int, Field(description="Max splats to import (higher = slower).", default=200000, ge=1000, le=500000)
    ] = 200000,
    pos_scale: Annotated[
        float, Field(description="Position scale factor (use 0.01 for cm→m conversion).", default=1.0)
    ] = 1.0,
    ctx: Context = None,
) -> dict:
    """Import a 3D Gaussian Splatting (.ply or .spz) file into the Godot scene.

    Parses the splat file (decompressing SPZ if needed), extracts per-splat
    positions, SH DC colors, and covariance scales, then renders via a custom
    ``gaussian_splat.gdshader`` on a ``MultiMeshInstance3D``. The shader applies
    proper billboarded Gaussian falloff with per-splat scale.

    Supports ``.ply`` (binary 3DGS format) and ``.spz`` (gzip-compressed).
    Use ``fleet_worldlabs_stage_splat`` to download World Labs splats first.

    ## Return Format
    {"success": bool, "data": {"imported": bool, "name": str, "splat_count": int, "shader": bool}}

    ## Examples
    await godot_import_splat(path="C:/data/scene.ply")
    await godot_import_splat(path="C:/exchange/splat_full.spz", name="WorldLabs", pos_scale=0.01)
    """
    try:
        from godot_mcp.services.splat_import import import_splat_file

        result = import_splat_file(path, output_name=name, max_splats=max_splats, pos_scale=pos_scale)
        if not result["success"]:
            return result

        bridge = get_bridge()
        if not bridge.connected:
            conn = await asyncio.to_thread(bridge.connect)
            if not conn["success"]:
                return {"success": False, "error": conn.get("error", "Cannot connect to Godot")}

        return await asyncio.to_thread(
            bridge.send,
            "import_splat",
            {"path": result["binary_path"], "name": name},
            timeout=60,
        )
    except ImportError as e:
        return {"success": False, "error": f"Splat import requires numpy: {e}"}
    except Exception as e:
        logger.exception("godot_import_splat error")
        return {"success": False, "error": str(e)}


async def godot_validate_meshes(
    ctx: Context = None,
) -> dict:
    """Validate all MeshInstance3D meshes in the scene for geometric corruption.

    Checks each mesh surface for:
    - **NaN/inf values** in vertex positions (segfault risk at render time)
    - **Zero-length normals** (causes flat shading on affected faces)
    - **Degenerate triangles** (zero-area faces from collapsed geometry)
    - **Empty surface arrays** (missing vertex data)

    Catches silently corrupt procedural mesh data that masquerades as lighting
    bugs or invisible geometry — the kind of issue that wastes hours of
    debugging because there's no visible error.

    ## Return Format
    {"success": bool, "data": {"total_meshes": int, "corrupt_meshes": int, "total_issues": int, "issues": list}}

    ## Examples
    await godot_validate_meshes()
    """
    bridge = get_bridge()
    if not bridge.connected:
        result = await asyncio.to_thread(bridge.connect)
        if not result["success"]:
            return {"success": False, "error": result.get("error", "Cannot connect to Godot")}

    return await asyncio.to_thread(bridge.send, "validate_meshes", {}, timeout=30)


async def godot_state_digest(
    node_names: Annotated[
        list[str] | None,
        Field(
            description="Optional node name filter. Omit to return state for all nodes in the ``mcp_watch`` group. Provide a list to target specific nodes by name (found recursively in the scene tree).",
            default=None,
        ),
    ] = None,
    ctx: Context = None,
) -> dict:
    """Read structured runtime state from the game scene.

    Two modes:
    - **Watch group** (omit ``node_names``): returns state for every node in the
      ``mcp_watch`` group. Nodes in this group can define a ``_mcp_state()`` method
      for custom state, or fall back to automatic property collection (position,
      rotation, scale, velocity, visible, current_animation).
    - **Named lookup** (provide ``node_names``): finds each node by name anywhere in
      the tree and returns its state, regardless of watch group membership.

    Cheaper than ``read_scene_tree`` — returns structured JSON without full hierarchy.

    ## Return Format
    {"success": bool, "data": {"nodes": {name: state_dict, ...}, "count": int}}

    ## Examples
    # All watched nodes
    await godot_state_digest()

    # Specific nodes
    await godot_state_digest(node_names=["Player", "EnemyBoss"])
    """
    bridge = get_bridge()
    if not bridge.connected:
        result = await asyncio.to_thread(bridge.connect)
        if not result["success"]:
            return {"success": False, "error": result.get("error", "Cannot connect to Godot")}

    params = {}
    if node_names is not None:
        params["nodes"] = node_names
    return await asyncio.to_thread(bridge.send, "state_digest", params, timeout=15)


_playtest_literals = Literal["freeze", "unfreeze", "step"]


async def godot_game_time(
    action: Annotated[
        _playtest_literals,
        Field(
            description="Clock action: ``freeze`` pauses the game loop (time_scale = 0), ``unfreeze`` resumes normal speed, ``step`` advances N frames then re-freezes."
        ),
    ],
    frames: Annotated[
        int, Field(description="Number of frames to advance (required for ``step`` action).", default=1, ge=1, le=3600)
    ] = 1,
    ctx: Context = None,
) -> dict:
    """Control the game clock for deterministic playtesting.

    **freeze** — pauses the game loop (``Engine.time_scale = 0``). The bridge
    keeps running so you can send input, read state, or set up scenarios.

    **unfreeze** — resumes normal game speed.

    **step** — advances the game by *frames* frames with real time-scale, then
    automatically re-freezes. Use after a freeze to tick the game forward
    deterministically.

    ## Return Format
    {"success": bool, "data": {"state": str, "time_scale": float}}

    ## Examples
    await godot_game_time(action="freeze")
    await godot_game_time(action="step", frames=60)
    await godot_game_time(action="unfreeze")
    """
    bridge = get_bridge()
    if not bridge.connected:
        result = await asyncio.to_thread(bridge.connect)
        if not result["success"]:
            return {"success": False, "error": result.get("error", "Cannot connect to Godot")}

    gaction = f"game_time_{action}"
    params = {"frames": frames} if action == "step" else {}
    return await asyncio.to_thread(bridge.send, gaction, params, timeout=30)


async def godot_step_until(
    condition: Annotated[
        str,
        Field(
            description="A GDScript expression evaluated each frame. When it returns ``true``, stepping stops. Examples:\n  ``get_node('Player').position.y < -10``\n  ``get_node('Boss').health <= 0``\n  ``get_tree().get_nodes_in_group('enemies').size() == 0``\nThe expression runs with ``get_tree().get_root()`` as the base instance, so ``get_node()`` calls are relative to the scene root."
        ),
    ],
    timeout_frames: Annotated[
        int,
        Field(
            description="Maximum frames before giving up (prevents infinite loops).",
            default=3600,
            ge=1,
            le=86400,
        ),
    ] = 3600,
    ctx: Context = None,
) -> dict:
    """Step the game frame-by-frame until a GDScript expression becomes true.

    Freeze the clock first with ``godot_game_time(action=\"freeze\")``, then
    call this to advance one frame at a time until the condition is met.
    The clock re-freezes automatically when the condition triggers (or on timeout).
    The ``timeout_frames`` param prevents runaway conditions.

    The condition expression runs in the context of the scene root, so
    ``get_node(\"Player\")`` resolves relative to the root of the active scene.

    ## Return Format
    {"success": bool, "data": {"condition_met": bool, "frames_elapsed": int, "timed_out": bool | None}}

    ## Examples
    # Jump and wait until Player lands
    await godot_game_time(action="freeze")
    await godot_simulate_input(actions=[{"action": "jump", "strength": 1.0}])
    await godot_step_until(condition="get_node('Player').is_on_floor()")
    await godot_capture_viewport()

    # Wait until boss is dead
    await godot_step_until(condition="get_node('Boss').health <= 0")
    """
    bridge = get_bridge()
    if not bridge.connected:
        result = await asyncio.to_thread(bridge.connect)
        if not result["success"]:
            return {"success": False, "error": result.get("error", "Cannot connect to Godot")}

    return await asyncio.to_thread(
        bridge.send,
        "game_time_step_until",
        {"condition": condition, "timeout_frames": timeout_frames},
        timeout=120,
    )


async def godot_scene(
    operation: Annotated[
        Literal["add_node", "remove_node", "modify_node", "save_scene"],
        Field(
            description="Scene operation: add_node (create a node), remove_node (delete by name/path), modify_node (set property by path), save_scene (persist the current scene)."
        ),
    ],
    parent: Annotated[
        str | None, Field(description="Parent node path (e.g. '.' or 'World/Player'). Used by: add_node.", default=None)
    ] = None,
    node_type: Annotated[
        str | None,
        Field(
            description="Godot node class (e.g. 'Node3D', 'CharacterBody3D', 'Camera3D'). Used by: add_node.",
            default=None,
        ),
    ] = None,
    name: Annotated[
        str | None, Field(description="Node name. Used by: add_node, remove_node, modify_node.", default=None)
    ] = None,
    node_path: Annotated[
        str | None, Field(description="Full path to the node. Used by: modify_node, remove_node.", default=None)
    ] = None,
    property_name: Annotated[
        str | None, Field(description="Property name (e.g. 'position', 'scale'). Used by: modify_node.", default=None)
    ] = None,
    value: Annotated[Any, Field(description="New value for the property. Used by: modify_node.", default=None)] = None,
    ctx: Context = None,
) -> dict:
    """Manage the Godot scene tree: add, remove, modify nodes, or save the scene.

    Portmanteau for 4 bridge-only REST actions: add_node, remove_node,
    modify_node, save_scene.

    ## Return Format
    {"success": bool, "data": {...}}

    ## Examples
    await godot_scene(operation="add_node", parent=".", node_type="Camera3D", name="GameCam")
    await godot_scene(operation="remove_node", name="OldNode")
    await godot_scene(operation="modify_node", node_path="Player/Camera", property_name="current", value=True)
    await godot_scene(operation="save_scene")
    """
    bridge = get_bridge()
    if not bridge.connected:
        result = await asyncio.to_thread(bridge.connect)
        if not result["success"]:
            return {"success": False, "error": result.get("error", "Cannot connect to Godot")}

    params = {}
    if parent is not None:
        params["parent"] = parent
    if node_type is not None:
        params["type"] = node_type
    if name is not None:
        params["name"] = name
    if node_path is not None:
        params["node_path"] = node_path
    if property_name is not None:
        params["property_name"] = property_name
    if value is not None:
        params["value"] = value

    return await asyncio.to_thread(bridge.send, operation, params, timeout=15)


async def godot_generate_procedural_texture(
    texture_type: Annotated[
        Literal["gradient", "noise", "checker", "solid"],
        Field(
            description="Texture type: gradient (vertical color ramp), noise (perlin noise), checker (checkerboard), solid (flat color)."
        ),
    ] = "gradient",
    width: Annotated[int, Field(default=256, ge=16, le=2048, description="Texture width in pixels.")] = 256,
    height: Annotated[int, Field(default=256, ge=16, le=2048, description="Texture height in pixels.")] = 256,
    colors: Annotated[
        list[str],
        Field(
            description="List of hex colors (e.g. ['#ff4444', '#4444ff']). Gradient uses all; noise lerps between first two; checker uses first two; solid uses first."
        ),
    ] = ["#ff4444", "#4444ff", "#44ff44"],
    cell_size: Annotated[int, Field(default=32, ge=4, le=256, description="Cell size for checker pattern.")] = 32,
    frequency: Annotated[float, Field(default=0.05, ge=0.001, le=1.0, description="Noise frequency.")] = 0.05,
    seed: Annotated[int | None, Field(default=None, description="Noise seed (random if omitted).")] = None,
    output_path: Annotated[str | None, Field(default=None, description="Optional output path for the PNG.")] = None,
    ctx: Context = None,
) -> dict:
    """Generate a procedural texture (gradient, noise, checker, solid) in Godot.

    Creates a runtime texture using Godot's Image API, saves it as PNG,
    and returns the path. The texture can be used with godot_set_material
    or as a sprite texture.

    ## Return Format
    {"success": bool, "data": {"path": str, "width": int, "height": int, "texture_type": str}}

    ## Examples
    await godot_generate_procedural_texture(texture_type="gradient", width=512, height=128, colors=["#ff0000", "#0000ff"])
    await godot_generate_procedural_texture(texture_type="noise", width=256, height=256, colors=["#1a1a2e", "#e94560"], frequency=0.03)
    await godot_generate_procedural_texture(texture_type="checker", cell_size=64, colors=["#333333", "#666666"])
    """
    bridge = get_bridge()
    if not bridge.connected:
        result = await asyncio.to_thread(bridge.connect)
        if not result["success"]:
            return {"success": False, "error": result.get("error", "Cannot connect to Godot")}

    params: dict = {
        "type": texture_type,
        "width": width,
        "height": height,
        "colors": colors,
    }
    if texture_type == "checker":
        params["cell_size"] = cell_size
    if texture_type == "noise":
        params["frequency"] = frequency
        if seed is not None:
            params["seed"] = seed
    if output_path:
        params["output_path"] = output_path
    return await asyncio.to_thread(bridge.send, "generate_procedural_texture", params, timeout=15)


async def start_bridge(
    project_root: Annotated[
        str | None, Field(description="Godot project root path (optional — auto-detected).", default=None)
    ] = None,
    ctx: Context = None,
) -> dict:
    """Locate Godot and launch it headless with the MCP bridge addon.

    Finds godot.exe via GODOT_PATH, PATH, or common install dirs, then starts
    it with ``--headless`` and the bridge project. Call ``godot_status`` after
    ~5s to verify the bridge is connected.

    ## Return Format
    {"success": bool, "pid": int, "godot": str, "project": str, "log": str, "message": str}

    ## Examples
    await start_bridge()
    await start_bridge(project_root="C:/MyGame")
    """
    return await asyncio.to_thread(launch_bridge, project_root)


def register(mcp):
    mcp.tool(annotations=_READ_ONLY, version="0.1.0")(godot_status)
    mcp.tool(annotations=_MUTATING, version="0.1.0")(godot_import_stl)
    mcp.tool(annotations=_MUTATING, version="0.1.0")(godot_import_glb)
    mcp.tool(annotations=_MUTATING, version="0.1.0")(godot_import_vrm)
    mcp.tool(annotations=_READ_ONLY, version="0.1.0")(godot_list_vrm)
    mcp.tool(annotations=_MUTATING, version="0.1.0")(godot_import_obj)
    mcp.tool(annotations=_MUTATING, version="0.1.0")(godot_play_animation)
    mcp.tool(annotations=_MUTATING, version="0.1.0")(godot_load_velocity_field)
    mcp.tool(annotations=_MUTATING, version="0.1.0")(godot_spawn_particles)
    mcp.tool(annotations=_MUTATING, version="0.1.0")(godot_animate_streamlines)
    mcp.tool(annotations=_MUTATING, version="0.1.0")(godot_create_camera)
    mcp.tool(annotations=_MUTATING, version="0.1.0")(godot_add_light)
    mcp.tool(annotations=_MUTATING, version="0.1.0")(godot_set_material)
    mcp.tool(annotations=_MUTATING, version="0.1.0")(godot_export_web)
    mcp.tool(annotations=_READ_ONLY, version="0.1.0")(godot_read_scene_tree)
    mcp.tool(annotations=_MUTATING, version="0.1.0")(godot_set_config)
    mcp.tool(annotations=_READ_ONLY, version="0.1.0")(godot_headless_verify)
    mcp.tool(annotations=_READ_ONLY, version="0.1.0")(godot_capture_viewport)
    mcp.tool(annotations=_MUTATING, version="0.1.0")(godot_simulate_input)
    mcp.tool(annotations=_READ_ONLY, version="0.1.0")(godot_read_node)
    mcp.tool(annotations=_READ_ONLY, version="0.1.0")(godot_inspect_resource)
    mcp.tool(annotations=_READ_ONLY, version="0.1.0")(godot_help)
    mcp.tool(annotations=_MUTATING, version="0.2.0")(godot_import_splat)
    mcp.tool(annotations=_MUTATING, version="0.1.0")(godot_tilemap)
    mcp.tool(annotations=_MUTATING, version="0.1.0")(godot_animation)
    mcp.tool(annotations=_READ_ONLY, version="0.1.0")(godot_profile)
    mcp.tool(annotations=_READ_ONLY, version="0.1.0")(godot_validate_meshes)
    mcp.tool(annotations=_READ_ONLY, version="0.2.0")(godot_state_digest)
    mcp.tool(annotations=_MUTATING, version="0.3.0")(godot_game_time)
    mcp.tool(annotations=_MUTATING, version="0.3.0")(godot_step_until)
    mcp.tool(annotations=_MUTATING, version="0.1.0")(godot_scene)
    mcp.tool(annotations=_MUTATING, version="0.1.0")(godot_generate_procedural_texture)
    mcp.tool(annotations=_MUTATING, version="0.1.0")(start_bridge)
