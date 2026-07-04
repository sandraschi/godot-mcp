"""Godot MCP core tools — engine control, STL/velocity import, particles, animation, export."""

import asyncio
import logging
from typing import Annotated

from fastmcp import Context
from pydantic import Field

from godot_mcp.services.godot_bridge import get_bridge

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
            return {
                "success": False,
                "error": result.get("error", "Cannot connect to Godot"),
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


def register(mcp):
    mcp.tool(annotations=_READ_ONLY, version="0.1.0")(godot_status)
    mcp.tool(annotations=_MUTATING, version="0.1.0")(godot_import_stl)
    mcp.tool(annotations=_MUTATING, version="0.1.0")(godot_import_glb)
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
