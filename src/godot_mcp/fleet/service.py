"""Fleet pipeline service layer."""

from __future__ import annotations

from typing import Any

from godot_mcp.fleet import exchange, pipeline, worldlabs


def fleet_exchange_status() -> dict[str, Any]:
    root = exchange.exchange_root()
    assets = exchange.list_exchange_assets(limit=50)
    return {
        "success": True,
        "exchange_root": str(root),
        "exchange_exists": root.is_dir(),
        "asset_count": len(assets),
        "assets": assets,
        "worldlabs_bridge": worldlabs.bridge_base_url(),
        "worldlabs_web": worldlabs.web_base_url(),
        "godot_splat_import": False,
        "godot_mesh_import": True,
    }


def fleet_import_from_exchange(
    path: str,
    name: str = "FleetImport",
    scale: float = 1.0,
) -> dict[str, Any]:
    try:
        return pipeline.import_mesh_path(path, name=name, scale=scale)
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def fleet_worldlabs_get_world(world_id: str) -> dict[str, Any]:
    try:
        return worldlabs.fetch_world(world_id)
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def fleet_worldlabs_stage_mesh(world_id: str) -> dict[str, Any]:
    try:
        return pipeline.stage_worldlabs_mesh(world_id)
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def fleet_worldlabs_stage_splat(world_id: str, resolution: str = "500k") -> dict[str, Any]:
    try:
        return pipeline.stage_worldlabs_splat(world_id, resolution=resolution)
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def fleet_worldlabs_import_mesh(
    world_id: str,
    node_name: str | None = None,
    scale: float = 1.0,
) -> dict[str, Any]:
    try:
        return pipeline.worldlabs_mesh_to_godot(world_id, node_name=node_name, scale=scale)
    except Exception as exc:
        return {"success": False, "error": str(exc)}
