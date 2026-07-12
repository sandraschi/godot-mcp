"""MCP tools for fleet maker → Godot pipelines."""

from __future__ import annotations

from typing import Annotated, Literal

from fastmcp import Context
from pydantic import Field

from godot_mcp.fleet import service

_READ_ONLY = {"readonly": True}
_MUTATING = {"mutating": True}


async def fleet_exchange_status(ctx: Context = None) -> dict:
    """List fleet exchange depot assets and pipeline readiness."""
    return service.fleet_exchange_status()


async def fleet_import_from_exchange(
    path: Annotated[str, Field(description="Absolute path under FLEET_EXCHANGE_ROOT (GLB/OBJ/STL).")],
    name: Annotated[str, Field(default="FleetImport")] = "FleetImport",
    scale: Annotated[float, Field(default=1.0, ge=0.001)] = 1.0,
    ctx: Context = None,
) -> dict:
    """Import a mesh from the fleet exchange into Godot (requires godot-bridge)."""
    return service.fleet_import_from_exchange(path, name=name, scale=scale)


async def fleet_worldlabs_get_world(
    world_id: Annotated[str, Field(description="Marble world id from worldlabs-mcp.")],
    ctx: Context = None,
) -> dict:
    """Fetch World Labs asset URLs (mesh, splats, panorama) via worldlabs bridge API."""
    return service.fleet_worldlabs_get_world(world_id)


async def fleet_worldlabs_stage_mesh(
    world_id: Annotated[str, Field(description="Marble world id.")],
    ctx: Context = None,
) -> dict:
    """Download Chisel collision GLB to _exchange/models/worldlabs/ (no Godot import)."""
    return service.fleet_worldlabs_stage_mesh(world_id)


async def fleet_worldlabs_stage_splat(
    world_id: Annotated[str, Field(description="Marble world id.")],
    resolution: Annotated[str, Field(description="100k, 500k, or full", default="500k")] = "500k",
    ctx: Context = None,
) -> dict:
    """Download SPZ splat to exchange for Spark/Unity — not imported to Godot yet."""
    return service.fleet_worldlabs_stage_splat(world_id, resolution=resolution)


async def fleet_worldlabs_import_mesh(
    world_id: Annotated[str, Field(description="Marble world id.")],
    node_name: Annotated[str | None, Field(default=None)] = None,
    scale: Annotated[float, Field(default=1.0, ge=0.001)] = 1.0,
    ctx: Context = None,
) -> dict:
    """Download World Labs collider GLB and import into Godot via godot_import_glb bridge."""
    return service.fleet_worldlabs_import_mesh(world_id, node_name=node_name, scale=scale)


async def fleet_ops(
    operation: Annotated[
        Literal[
            "exchange_status",
            "import",
            "worldlabs_get",
            "worldlabs_stage_mesh",
            "worldlabs_stage_splat",
            "worldlabs_import",
        ],
        Field(
            description="Fleet operation: exchange_status (depot assets), import (GLB/OBJ/STL from exchange), worldlabs_get (fetch asset URLs), worldlabs_stage_mesh (download collider GLB), worldlabs_stage_splat (download SPZ), worldlabs_import (download + import GLB into Godot)."
        ),
    ],
    path: Annotated[str | None, Field(default=None, description="Asset path. Used by: import.")] = None,
    name: Annotated[
        str | None, Field(default=None, description="Node name. Used by: import, worldlabs_import.")
    ] = None,
    scale: Annotated[float, Field(default=1.0, description="Scale factor. Used by: import, worldlabs_import.")] = 1.0,
    world_id: Annotated[str | None, Field(default=None, description="Marble world id. Used by: worldlabs_*.")] = None,
    resolution: Annotated[
        str, Field(default="500k", description="Splat resolution. Used by: worldlabs_stage_splat.")
    ] = "500k",
    ctx: Context = None,
) -> dict:
    """Fleet exchange pipeline — consolidated portmanteau.

    ## Return Format
    {"success": bool, ...}

    ## Examples
    await fleet_ops(operation="exchange_status")
    await fleet_ops(operation="import", path="models/scene.glb", name="Imported")
    await fleet_ops(operation="worldlabs_get", world_id="abc123")
    """
    from godot_mcp.fleet import service as s

    match operation:
        case "exchange_status":
            return s.fleet_exchange_status()
        case "import":
            return s.fleet_import_from_exchange(path or "", name=name or "FleetImport", scale=scale)
        case "worldlabs_get":
            return s.fleet_worldlabs_get_world(world_id or "")
        case "worldlabs_stage_mesh":
            return s.fleet_worldlabs_stage_mesh(world_id or "")
        case "worldlabs_stage_splat":
            return s.fleet_worldlabs_stage_splat(world_id or "", resolution=resolution)
        case "worldlabs_import":
            return s.fleet_worldlabs_import_mesh(world_id or "", node_name=name, scale=scale)
        case _:
            return {"success": False, "error": f"Unknown fleet operation: {operation}"}


def register(mcp):
    mcp.tool(annotations=_READ_ONLY, version="0.2.1")(fleet_exchange_status)
    mcp.tool(annotations=_READ_ONLY, version="0.2.1")(fleet_worldlabs_get_world)
    mcp.tool(annotations=_MUTATING, version="0.2.1")(fleet_import_from_exchange)
    mcp.tool(annotations=_MUTATING, version="0.2.1")(fleet_worldlabs_stage_mesh)
    mcp.tool(annotations=_MUTATING, version="0.2.1")(fleet_worldlabs_stage_splat)
    mcp.tool(annotations=_MUTATING, version="0.2.1")(fleet_worldlabs_import_mesh)
    mcp.tool(annotations=_READ_ONLY, version="0.4.0")(fleet_ops)
