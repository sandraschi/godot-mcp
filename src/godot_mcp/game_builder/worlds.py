"""World Labs operation parsing and fleet mesh staging for game_builder."""

from __future__ import annotations

from typing import Any

from godot_mcp.fleet import exchange, pipeline as fleet_pipeline


def unwrap_bridge_response(resp: dict[str, Any]) -> dict[str, Any]:
    """Normalize MCP bridge HTTP responses from remote servers."""
    if not isinstance(resp, dict):
        return {"raw": resp}
    if resp.get("success") is False and resp.get("error"):
        return resp
    data = resp.get("data")
    if isinstance(data, dict):
        return data
    result = resp.get("result")
    if isinstance(result, dict):
        return result
    return resp


def extract_operation_id(op: dict[str, Any]) -> str:
    if op.get("operation_id"):
        return str(op["operation_id"])
    name = op.get("name", "")
    if name:
        return str(name).split("/")[-1]
    nested = op.get("data", {})
    if isinstance(nested, dict) and nested.get("operation_id"):
        return str(nested["operation_id"])
    return ""


def extract_marble_world_id(done_op: dict[str, Any]) -> str:
    """Marble world UUID from a completed long-running operation."""
    response = done_op.get("response", {})
    if isinstance(response, dict):
        world = response.get("world", {})
        if isinstance(world, dict):
            wid = world.get("id") or world.get("world_id")
            if wid:
                return str(wid)
    for key in ("world_id", "id"):
        if done_op.get(key):
            return str(done_op[key])
    return ""


def extract_world_assets(done_op: dict[str, Any]) -> dict[str, Any]:
    response = done_op.get("response", {})
    if isinstance(response, dict):
        world = response.get("world", {})
        if isinstance(world, dict):
            assets = world.get("assets")
            if isinstance(assets, dict):
                return assets
    assets = done_op.get("assets")
    return assets if isinstance(assets, dict) else {}


def operation_is_done(op: dict[str, Any]) -> bool:
    if op.get("done") is True:
        return True
    status = str(op.get("status", op.get("state", ""))).lower()
    return status in {"completed", "done", "success", "succeeded"}


def operation_failed(op: dict[str, Any]) -> bool:
    if op.get("error"):
        return True
    status = str(op.get("status", op.get("state", ""))).lower()
    return status in {"failed", "error", "cancelled"}


def expected_mesh_path(marble_world_id: str) -> str:
    return str(exchange.worldlabs_dir() / f"{marble_world_id[:12]}_collider.glb")


def stage_mesh_for_marble_world(marble_world_id: str) -> dict[str, Any]:
    """Download collider GLB to fleet exchange."""
    if not marble_world_id:
        return {"success": False, "error": "missing marble_world_id"}
    try:
        return fleet_pipeline.stage_worldlabs_mesh(marble_world_id)
    except Exception as exc:
        return {"success": False, "error": str(exc), "marble_world_id": marble_world_id}


def enrich_world_result(entry: dict[str, Any], *, stage_mesh: bool = True) -> dict[str, Any]:
    """Attach marble_world_id, mesh_path, and optional staged GLB to a plan-slug result."""
    marble_id = entry.get("marble_world_id") or entry.get("world_id") or ""
    if not marble_id:
        marble_id = extract_marble_world_id(entry)
    if marble_id:
        entry["marble_world_id"] = marble_id
        entry.setdefault("world_id", marble_id)

    if stage_mesh and marble_id and entry.get("status") == "completed" and not entry.get("mesh_path"):
        staged = stage_mesh_for_marble_world(marble_id)
        entry["staged"] = staged.get("success", False)
        if staged.get("success"):
            entry["mesh_path"] = staged.get("mesh_path")
            entry["spark_viewer_url"] = staged.get("spark_viewer_url")
        else:
            entry["stage_error"] = staged.get("error")

    if marble_id and not entry.get("mesh_path"):
        path = expected_mesh_path(marble_id)
        from pathlib import Path

        if Path(path).is_file():
            entry["mesh_path"] = path

    return entry


def marble_id_for_plan_slug(world_results: dict[str, Any], plan_slug: str) -> str:
    entry = world_results.get(plan_slug, {})
    if not isinstance(entry, dict):
        return ""
    return str(entry.get("marble_world_id") or entry.get("world_id") or "")
