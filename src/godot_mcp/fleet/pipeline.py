"""Import fleet assets into Godot via TCP bridge."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from godot_mcp.fleet import exchange, worldlabs


def _ensure_bridge():
    from godot_mcp.services.godot_bridge import get_bridge

    bridge = get_bridge()
    if not bridge.connected:
        result = bridge.connect()
        if not result.get("success"):
            raise RuntimeError(result.get("error", "Godot bridge not connected — run just godot-bridge"))
    return bridge


def import_mesh_path(
    path: str | Path,
    name: str = "FleetImport",
    scale: float = 1.0,
) -> dict[str, Any]:
    resolved = exchange.validate_import_path(path)
    ext = resolved.suffix.lower()
    bridge = _ensure_bridge()

    params = {
        "path": str(resolved),
        "name": name,
        "scale": scale,
        "position": {"x": 0.0, "y": 0.0, "z": 0.0},
    }

    if ext in {".glb", ".gltf"}:
        action = "import_glb"
    elif ext == ".obj":
        action = "import_obj"
    elif ext == ".stl":
        action = "import_stl"
    else:
        raise ValueError(f"Unsupported extension: {ext}")

    result = bridge.send(action, params)
    return {
        "success": result.get("success", False),
        "action": action,
        "path": str(resolved),
        "bridge_result": result,
        "error": result.get("error"),
    }


def stage_worldlabs_mesh(world_id: str) -> dict[str, Any]:
    info = worldlabs.fetch_world(world_id)
    mesh_url = info["assets"].get("mesh")
    if not mesh_url:
        return {
            "success": False,
            "error": "World has no collider mesh URL yet (generation may still be running)",
            "world_id": world_id,
            "assets": info["assets"],
        }
    dest = exchange.worldlabs_dir() / f"{world_id[:12]}_collider.glb"
    worldlabs.download_url(mesh_url, dest)
    return {
        "success": True,
        "world_id": world_id,
        "mesh_path": str(dest),
        "assets": info["assets"],
        "spark_viewer_url": info.get("spark_viewer_url"),
        "splat_note": "SPZ splats are staged separately; Godot does not render them in-engine yet.",
    }


def stage_worldlabs_splat(world_id: str, resolution: str = "500k") -> dict[str, Any]:
    info = worldlabs.fetch_world(world_id)
    key = f"splat_{resolution}" if resolution != "full" else "splat_full"
    if resolution == "100k":
        key = "splat_100k"
    elif resolution == "500k":
        key = "splat_500k"
    elif resolution in {"full", "full_res"}:
        key = "splat_full"
    url = info["assets"].get(key)
    if not url:
        return {"success": False, "error": f"No {key} URL on world", "assets": info["assets"]}
    suffix = ".spz" if ".spz" in url.lower() else ".ply"
    dest = exchange.worldlabs_dir() / f"{world_id[:12]}_{key}{suffix}"
    worldlabs.download_url(url, dest)
    return {
        "success": True,
        "world_id": world_id,
        "splat_path": str(dest),
        "resolution": key,
        "spark_viewer_url": info.get("spark_viewer_url"),
        "godot_import": "not_supported — use spark_viewer_url or Unity splat path",
    }


def worldlabs_mesh_to_godot(
    world_id: str,
    node_name: str | None = None,
    scale: float = 1.0,
) -> dict[str, Any]:
    staged = stage_worldlabs_mesh(world_id)
    if not staged.get("success"):
        return staged
    name = node_name or f"World_{world_id[:8]}"
    imported = import_mesh_path(staged["mesh_path"], name=name, scale=scale)
    return {
        "success": imported.get("success", False),
        "world_id": world_id,
        "mesh_path": staged["mesh_path"],
        "spark_viewer_url": staged.get("spark_viewer_url"),
        "assets": staged.get("assets"),
        "import": imported,
        "error": imported.get("error"),
    }
